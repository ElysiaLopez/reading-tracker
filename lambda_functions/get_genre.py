import json
import boto3
import os
import datatier

from configparser import ConfigParser

def lambda_handler(event, context):
    try:
        print("**STARTING**")
        print("**lambda: getgenre**")
    
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
        # open connection to the database:
        #
        print("**Opening connection**")
    
        dbConn = datatier.get_dbConn(rds_endpoint, rds_portnum, rds_username, rds_pwd, rds_dbname)
    
        #
        # now retrieve the count of books by genre:
        #
        print("**Retrieving data**")
    
        sql = """
        SELECT genre, COUNT(*) as count
        FROM books
        WHERE genre IS NOT NULL AND genre != 'null'
        GROUP BY genre;
        """
    
        rows = datatier.retrieve_all_rows(dbConn, sql)
    
        # Process the results
        counts_by_genre = {}
        for row in rows:
            genre = row[0]
            count = row[1]
            counts_by_genre[genre] = count
    
        #
        # respond in an HTTP-like way, i.e. with a status
        # code and body in JSON format:
        #
        print("**DONE, returning counts**")
                
        return {
            'statusCode': 200,
            'body': json.dumps(counts_by_genre)
        }

    except Exception as err:
        print("**ERROR**")
        print(str(err))
    
        return {
            'statusCode': 400,
            'body': json.dumps(str(err))
        }
