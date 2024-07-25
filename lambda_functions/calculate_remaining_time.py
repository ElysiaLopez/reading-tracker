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
    print("**lambda: calculate_remaining_time**")
    
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
    reading_speed = ""
    
    if "body" not in event:
      return api_utils.error(400, "no body in request")
      
    body = json.loads(event["body"])
    
    if "pages_completed" in body and "book_id" in body and "reading_speed" in body:
      pages_completed = body["pages_completed"]
      book_id = body["book_id"]
      reading_speed = body["reading_speed"]
      if float(pages_completed) < float(0) and float(reading_speed) <= float(0):
        return api_utils.error(401, "Number of pages read cannot be negative and reading speed must be greater than zero")
      elif float(pages_completed) < float(0):
        return api_utils.error(401, "Number of pages read cannot be negative")
      elif float(reading_speed) <= float(0):
        return api_utils.error(401, "Reading speed must be greater than zero")
    else:
      return api_utils.error(400, "missing credentials in body")
    
    print("**Looking up book_id in database**")
    
    sql = "SELECT title, pagecount, pgsread FROM books WHERE bookid = %s;"
    
    row = datatier.retrieve_one_row(dbConn, sql, [book_id])
    
    if row == ():
        print("**No such book, returning...**")
        return api_utils.error(401, "invalid bookid")
        
    title = row[0]
    page_count = row[1]
    pages_read = row[2]
      
    print("title:", title)
    print("page_count:", page_count)
    print("pages_read:", pages_read)
    
    
    sql = """
      UPDATE books
      SET pgsread = %s
      WHERE bookid = %s;
      """
      
    modified = datatier.perform_action(dbConn, sql, [pages_completed, book_id])
      
    if page_count == None:
      return api_utils.success(200, "No information on length of book, cannot predict time remaining")
    
    pages_remaining = float(page_count) - float(pages_completed)
    if pages_remaining <= 0:
      return api_utils.success(200, "0 minutes remaining, you have completed the book!")
    time_remaining_int = round((pages_remaining / float(reading_speed)), 2) # in minutes
    time_remaining_str = str(time_remaining_int) + " minutes"
    if time_remaining_int > 60:
      time_remaining_int = round((time_remaining_int / 60), 2)  # in hours
      time_remaining_str = str(time_remaining_int) + " hours"
    
    sql = """
      UPDATE books
      SET predremaining = %s
      WHERE bookid = %s;
      """
    
    print(time_remaining_str)
    second_mod = datatier.perform_action(dbConn, sql, [time_remaining_str, book_id])
      
    #
    # success, done!
    #
    print("**DONE, returning predicted remaining time to read**")

    return api_utils.success(200, "Predicted time remaining to complete book: " + time_remaining_str)
    
  except Exception as err:
    print("**ERROR**")
    print(str(err))

    return api_utils.error(400, str(err))