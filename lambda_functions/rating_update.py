import json
import boto3
import os
import datetime
import uuid
import datatier
import api_utils
import base64

from configparser import ConfigParser

def lambda_handler(event, context):
  try:
    print("**STARTING**")
    print("**lambda: rating_update**")
    
    #
    # setup AWS based on config file:
    #
    config_file = 'library-config.ini'
    os.environ['AWS_SHARED_CREDENTIALS_FILE'] = config_file
    
    configur = ConfigParser()
    configur.read(config_file)
    
    #
    # configure for S3 access:
    #
    s3_profile = 's3readwrite'
    boto3.setup_default_session(profile_name=s3_profile)
    
    bucketname = configur.get('s3', 'bucket_name')
    
    s3 = boto3.resource('s3')
    bucket = s3.Bucket(bucketname)
    
    #
    # configure for RDS access
    #
    rds_endpoint = configur.get('rds', 'endpoint')
    rds_portnum = int(configur.get('rds', 'port_number'))
    rds_username = configur.get('rds', 'user_name')
    rds_pwd = configur.get('rds', 'user_pwd')
    rds_dbname = configur.get('rds', 'db_name')
    
    #
    # open database connection
    #
    print("**Opening DB connection**")
    
    dbConn = datatier.get_dbConn(rds_endpoint, rds_portnum, rds_username, rds_pwd, rds_dbname)
    
    #
    # expecting ranking (0-10) and book id from client, possibly expecting review
    #
    print("**Accessing request body**")
    
    ranking = ""
    book_id = ""
    review = ""
    
    if "body" not in event:
      return api_utils.error(400, "no body in request")
    
    body = json.loads(event["body"])
    
    if "ranking" in body and "book_id" in body and "review" in body:
        ranking = body["ranking"]
        book_id = body["book_id"]
        review = body["review"]
        if int(ranking) > 10 or int(ranking) < 0:
            return api_utils.error(400, "Rating must be 0-10")
    else:
        return api_utils.error(400, "missing credentials in body")
    
    print("**Looking up book_id in database**")
    
    sql = "SELECT title FROM books WHERE bookid = %s;"
    
    row = datatier.retrieve_one_row(dbConn, sql, [book_id])
    
    if row == ():
        print("**No such book, returning...**")
        return api_utils.error(401, "invalid bookid")
        
    title = row[0]
      
    print("title", title)
    
    if review == "":
        sql = """
          UPDATE books
          SET ranking = %s
          WHERE bookid = %s;
          """
        modified = datatier.perform_action(dbConn, sql, [ranking, book_id])
    else:
        sql = """
          UPDATE books
          SET ranking = %s, client_review = %s
          WHERE bookid = %s;
          """
        modified = datatier.perform_action(dbConn, sql, [ranking, review, book_id])
      
    sql = """
      SELECT ranking, title, client_review
      FROM books
      ORDER BY ranking DESC;
      """
      
    selected = datatier.retrieve_all_rows(dbConn, sql)
      
    rankings_file = "rankings.txt"
    
    local_results_file = "/tmp/results.txt"
    
    outfile = open(local_results_file, "w")
    outfile.write("**Top Books Read**\n")
    
    outfile.write("RATING " + "TITLE " + "REVIEW" + "\n")
    for i in range(len(selected)):
      if selected[i][0] is not None:
        index = i + 1
        outfile.write(str(index) + ": " + str(selected[i]) + "\n")
      
    outfile.close()
    
    #
    # upload the results file to S3:
    #
    print("**UPLOADING to S3 file", rankings_file, "**")

    bucket.upload_file(local_results_file,
                       rankings_file,
                       ExtraArgs={
                         'ACL': 'public-read',
                         'ContentType': 'text/plain'
                       })
    
    #
    # open the file and read as raw bytes:
    #
    infile = open(local_results_file, "rb")
    bytes = infile.read()
    infile.close()
    
    #
    # encode the data as base64.
    #
    data = base64.b64encode(bytes)
    datastr = data.decode()

    print("**DONE, returning results**")
    
    #
    # done!
    #
    
    print("**DONE, returning data**")
    
    return api_utils.success(200, datastr)
    
  #
  # on an error, try to upload error message to S3:
  #
  except Exception as err:
    print("**ERROR**")
    print(str(err))
    
    local_results_file = "/tmp/results.txt"
    outfile = open(local_results_file, "w")

    outfile.write(str(err))
    outfile.write("\n")
    outfile.close()
    
    if rankings_file == "": 
      #
      # we can't upload the error file:
      #
      pass
    else:
      # 
      # upload the error file to S3
      #
      print("**UPLOADING**")
      #
      bucket.upload_file(local_results_file,
                         rankings_file,
                         ExtraArgs={
                           'ACL': 'public-read',
                           'ContentType': 'text/plain'
                         })
