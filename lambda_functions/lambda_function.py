import json
import os
import datetime
import uuid
import datatier
import api_utils

from configparser import ConfigParser

def lambda_handler(event, context):
  try:
    print("**STARTING**")
    print("**lambda: finalproj_progress**")
    
    #
    # setup AWS based on config file:
    #
    config_file = 'library-config.ini'
    os.environ['AWS_SHARED_CREDENTIALS_FILE'] = config_file
    
    configur = ConfigParser()
    configur.read(config_file)
    
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
    # expecting pages completed and book id from client, possibly expecting reading speed
    #
    print("**Accessing request body**")
    
    pages_completed = ""
    book_id = ""
    reading_speed = 1
    
    if "body" not in event:
      return api_utils.error(400, "no body in request")
      
    body = json.loads(event["body"])
    
    if "pages_completed" in body and "book_id" in body and "reading_speed" in body:
      pages_completed = body["pages_completed"]
      book_id = body["book_id"]
      if body["reading_speed"] != 0:
        reading_speed = body["reading_speed"]
    else:
      return api_utils.error(400, "missing credentials in body")
    
    print("**Looking up book_id in database**")
    
    sql = "SELECT title, pagecount FROM books WHERE bookid = %s;"
    
    row = datatier.retrieve_one_row(dbConn, sql, [book_id])
    
    if row == ():
        print("**No such book, returning...**")
        return api_utils.error(401, "invalid bookid")
        
    title = row[0]
    page_count = row[1]
      
    print("title", title)
    print("page count:", page_count)
    
    if page_count == null:
      print("No information on length of book, cannot fulfill request")
      return api_utils.error(400, "No information on length of book, cannot fulfill request")
    
    sql = """
      UPDATE books
      SET pgsread = %s
      WHERE bookid = %s;
      """
      
    modified = datatier.perform_action(dbConn, sql, [pages_completed, book_id])
    
    if modified != 1:
      print("**INTERNAL ERROR: update database failed...**")
      return api_utils.error(400, "INTERNAL ERROR: update failed to modify database")
      
    time_remaining_int = (page_count - pages_completed) / reading_speed # in minutes
    time_remaining_str = str(time_remaining) + " minutes"
    if time_remaining_int > 60:
      time_remaining_int = time_remaining_int / 60  # in hours
      time_remaining_str = str(time_remaining_int) + " hours"
      
    sql = """
      UPDATE books
      SET predremaining = %s
      WHERE bookid = %s;
      """
      
    second_mod = datatier.perform_action(dbConn, sql, [time_remaining_str, book_id])
    
    if second_mod != 1:
      print("**INTERNAL ERROR: update database failed...**")
      return api_utils.error(400, "INTERNAL ERROR: update failed to modify database")
      
    #
    # success, done!
    #
    print("**DONE, returning predicted remaining time to read**")

    return api_utils.success(200, time_remaining_str)
    
  except Exception as err:
    print("**ERROR**")
    print(str(err))

    return api_utils.error(400, str(err))
