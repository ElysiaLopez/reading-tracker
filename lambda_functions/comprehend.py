import json
import boto3
import os
import datatier

from configparser import ConfigParser

def lambda_handler(event, context):
    try:
        print("**STARTING**")
        print("**lambda: final_proj_comprehend**")
    
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
        # now retrieve all the jobs:
        #
        print("**Retrieving data**")
    
        sql = "SELECT genre, client_review FROM books where client_review IS NOT NULL and genre IS NOT NULL AND genre != 'null';"
    
        rows = datatier.retrieve_all_rows(dbConn, sql)
    
        # Group reviews by genre
        reviews_by_genre = {}
        for row in rows:
            genre = row[0]
            review = row[1]
            if genre in reviews_by_genre:
                reviews_by_genre[genre].append(review)
            else:
                reviews_by_genre[genre] = [review]
        # Initalize comprehend 
        comprehend = boto3.client('comprehend')
    
        sentiments_by_genre = {}
        for genre, reviews in reviews_by_genre.items():
            combined_reviews = " ".join(reviews)
            response = comprehend.detect_sentiment(Text=combined_reviews, LanguageCode='en')
            sentiment = response['Sentiment']
            sentiments_by_genre[genre] = {
                'sentiment': sentiment,
                'positive_score': response['SentimentScore']['Positive'],
                'negative_score': response['SentimentScore']['Negative'],
                'neutral_score': response['SentimentScore']['Neutral'],
                'mixed_score': response['SentimentScore']['Mixed']
            }
    
        #
        # respond in an HTTP-like way, i.e. with a status
        # code and body in JSON format:
        #
        print("**DONE, returning sentiments**")
                
        return {
            'statusCode': 200,
            'body': json.dumps(sentiments_by_genre)
        }

    except Exception as err:
        print("**ERROR**")
        print(str(err))
    
        return {
          'statusCode': 400,
          'body': json.dumps(str(err))
        }
