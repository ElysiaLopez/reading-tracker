import json

import requests
import datatier
import os

from configparser import ConfigParser


def get_json_val(json, category):
  if category in json:
    return json[category]
  return "null"

def insert_book_to_database(book, dbConn):

  volumeid = book["id"]
  volInfo = book["volumeInfo"]

  try:
    title = get_json_val(volInfo, "title")
    cats = get_json_val(volInfo, "categories")
    if cats != "null":
      if len(cats) > 0:
        genre = cats[0]
      else:
        genre = "null"
      

    pagecount = get_json_val(volInfo, "pageCount")
    pagecount = int(pagecount) if pagecount != "null" else "null"

    summary = get_json_val(volInfo, "description")
    summary = summary.replace('"', "'")

    avg_review = get_json_val(volInfo, "averageRating")
    avg_review = float(avg_review) if avg_review != "null" else "null"

    num_reviews = get_json_val(volInfo, "ratingsCount")
    num_reviews = int(num_reviews) if num_reviews != "null" else "null"

    pgsread = 0
    predremaining = get_json_val(volInfo, "pageCount")
    predremaining = int(predremaining) if predremaining != "null" else "null"

    sql = f'''INSERT INTO books (title, volumeid, genre, pagecount, summary, avg_review, num_reviews, pgsread, predremaining) VALUES ("{title}", "{volumeid}", "{genre}", {pagecount}, "{summary}", {avg_review}, {num_reviews}, {pgsread}, {predremaining});
    '''

    print(sql)

    datatier.perform_action(dbConn, sql)
    
    book_id_sql = "SELECT MAX(bookid) FROM books;"
    row = datatier.retrieve_one_row(dbConn, book_id_sql)
    
    book_id_result = row[0]

  except Exception as err:
    return {'statusCode': 400, 'body': 'lambda error: ' + str(err)}
  
  return {'statusCode': 200, 'body': book_id_result}

def lambda_handler(event, context):
    
    config_file = 'library-config.ini'
    os.environ['AWS_SHARED_CREDENTIALS_FILE'] = config_file
    
    configur = ConfigParser()
    configur.read(config_file)
    
    rds_endpoint = configur.get('rds', 'endpoint')
    rds_portnum = int(configur.get('rds', 'port_number'))
    rds_username = configur.get('rds', 'user_name')
    rds_pwd = configur.get('rds', 'user_pwd')
    rds_dbname = configur.get('rds', 'db_name')
    
    dbConn = datatier.get_dbConn(rds_endpoint, rds_portnum, rds_username,
                                 rds_pwd, rds_dbname)
                                 
    
    print("Configured database")
    
    book = json.loads(event["body"])
    
    print("book: ")    
    print(book)
    print("****")
  
    print("About to insert book")
    response = insert_book_to_database(book, dbConn)
    print("Inserted book")
    
    
    print("Done with insert")
    return response
