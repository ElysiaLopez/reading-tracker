from pymysql import NULL
import requests
import datatier
import os
import logging
import base64

from configparser import ConfigParser


def loop_til_valid_val(min, max, text):
  while (True):
    try:
      user_input = float(input(text))
      if user_input >= min and user_input <= max:
        return user_input
      print("Please enter a value between " + str(min) + " and " + str(max))
    except Exception:
      print("Please enter numeric value")


def find_book_from_api():
  key = "AIzaSyDxdYau_lIqQNsSdBlBlokypysmx2ehNvs"
  title = input("Enter a title: ")

  request = f"https://www.googleapis.com/books/v1/volumes?q={title}+intitle:{title}&key={key}"

  response = requests.get(request)
  output = response.json()
  books = output["items"]

  print("\nPlease select an option:\n")

  for i, book in enumerate(books):
    print(f"{i}: \n")
    print("  Title: " + book["volumeInfo"]["title"])
    print("  Author(s):")

    volInfo = book["volumeInfo"]

    if "authors" in volInfo:
      authors = book["volumeInfo"]["authors"]
      for author in authors:
        print("  " + author)
    else:
      print("    None")

  option = int(input("Selected option: "))

  book = books[option]

  return book


def insert_book(baseurl):

  book = find_book_from_api()

  url = baseurl + "/insertbook"

  response = requests.post(url, json=book)
  if response.status_code == 200:
    book_id = response.json()
    print(f"Book inserted with id: {book_id}")
  else:
    print("Failed to insert book")

  return response


############################################################
#
# update_reading_progress
#
def update_reading_progress(baseurl):
  """
  Update pages read in the database and returns expected time left to
  complete book

  Parameters
  ----------
  baseurl: baseurl for web service

  Returns
  -------
  Expected time left to complete book (predremaining)
  """

  print("Enter book id>")
  book_id = input()

  print("Enter number of pages read>")
  pages_completed = input()

  print("Press ENTER to use average reading speed, or")
  print("enter your average reading speed in pages per minute>")
  s = input()

  reading_speed = 1 if s == "" else s

  try:
    #
    # build message:
    #
    data = {
        "book_id": book_id,
        "pages_completed": pages_completed,
        "reading_speed": reading_speed
    }

    #
    # call the web service:
    #
    api = '/calculateremainingtime'
    url = baseurl + api

    res = requests.post(url, json=data)

    #
    # let's look at what we got back:
    #
    if res.status_code != 200:
      # failed:
      print("Failed with status code:", res.status_code)
      print("url: " + url)
      if res.status_code == 400:
        # we'll have an error message
        body = res.json()
        print("Error message:", body)
      #
      return res

    #
    # success:
    #
    print("Updated reading progress")
    time_remaining = res.json()
    print(time_remaining)
    return res

  except Exception as e:
    logging.error("update_reading_progress() failed:")
    logging.error("url: " + url)
    logging.error(e)
    return res


############################################################
#
# get_review_sentiment
#
def get_review_sentiment(baseurl):
  """
  Gets genre and client-inputted review data from database, running Comprehend for
  sentiment analysis, prints out the analysis

  Parameters
  ----------
  baseurl: baseurl for web service

  Returns
  -------
  Nothing
  """

  try:
    #
    # call the web service:
    #
    comprehend_api = '/comprehendreviews'
    comprehend_url = baseurl + comprehend_api

    comprehend_res = requests.get(comprehend_url)


    #
    # let's look at what we got back:
    #
    if comprehend_res.status_code != 200:
      # failed:
      print("Failed with status code:", comprehend_res.status_code)
      print("url: " + comprehend_url)
      if comprehend_res.status_code == 400:
        # we'll have an error message
        body = comprehend_res.json()
        print("Error message:", body)
      #
      return

    #
    # call the web service:
    #
    genre_count_api = '/getgenre'
    genre_count_url = baseurl + genre_count_api

    genre_count_res = requests.get(genre_count_url)

    #
    # let's look at what we got back:
    #
    if genre_count_res.status_code != 200:
        # failed:
        print("Failed with status code:", genre_count_res.status_code)
        print("url: " + genre_count_url)
        if genre_count_res.status_code == 400:
            # we'll have an error message
            body = genre_count_res.json()
            print("Error message:", body)
        return

    #
    # success:
    #
    sentiments_by_genre = comprehend_res.json()

    if sentiments_by_genre == {}:
      print("No reviews found. Try reviewing a book!")
      return
    genre_counts = genre_count_res.json()
    for genre, sentiment_data in sentiments_by_genre.items():
      num_books = genre_counts.get(genre, 0)
      if sentiment_data['sentiment'] == "POSITIVE":
        print(f"You've reviewed {num_books} {genre} books. Your overall sentiment for this genre is positive! Perhaps you should read more of this genre :)")
      if sentiment_data['sentiment'] == "NEUTRAL":
        print(f"You've reviewed {num_books} {genre} books. Your overall sentiment for this genre is neutral! I'm not sure what that means for you...")
      if sentiment_data['sentiment'] == "MIXED":
        print(f"You've reviewed {num_books} {genre} books. Your overall sentiment for this genre is mixed! Love-hate relationship?")
      if sentiment_data['sentiment'] == "NEGATIVE":
        print(f"You've reviewed {num_books} {genre} books. Your overall sentiment for this genre is negative! Pick a new genre to read, please.")

      print("\n")
    return

  except Exception as e:
    logging.error("get_review_sentiment() failed:")
    logging.error(e)
    return

############################################################
#
# update_book_rating
#
def update_book_rating(baseurl):
  """
  Update rating and review in the database and updates text file in S3
  with the user's top rated books

  Parameters
  ----------
  baseurl: baseurl for web service

  Returns
  -------
  Nothing
  """

  #find_book_from_database(baseurl)

  print("Enter book id>")
  book_id = input()

  print("Enter rating (0-10)>")
  ranking = input()

  print("Press ENTER to proceed without review, or")
  print("enter your review of the book>")
  s = input()

  review = "" if s == "" else s

  try:
    #
    # build message:
    #
    data = {"book_id": book_id, "ranking": ranking, "review": review}

    #
    # call the web service:
    #
    api = '/updaterating'
    url = baseurl + api

    res = requests.post(url, json=data)

    #
    # let's look at what we got back:
    #
    if res.status_code != 200:
      # failed:
      print("Failed with status code:", res.status_code)
      print("url: " + url)
      if res.status_code == 400:
        # we'll have an error message
        body = res.json()
        print("Error message:", body)
      #
      return

    #
    # success:
    #
    body = res.json()
    datastr = body
    base64_bytes = datastr.encode()
    bytes = base64.b64decode(base64_bytes)
    results = bytes.decode()

    print("Updated book rating\n")
    updated_ranking = results
    print(updated_ranking)
    return

  except Exception as e:
    logging.error("update_book_rating() failed:")
    logging.error("url: " + url)
    logging.error(e)
    return


############################# MAIN #############################

config_file = 'api-config.ini'
os.environ['AWS_SHARED_CREDENTIALS_FILE'] = config_file

#
# setup base URL to web service:
#
configur = ConfigParser()
configur.read(config_file)
baseurl = configur.get('client', 'webservice')

lastchar = baseurl[len(baseurl) - 1]
if lastchar == "/":
  baseurl = baseurl[:-1]

options = [
    "Add book to shelf", "Update reading progress", "Update book rating",
    "Get review sentiment"
]

print("** Welcome to Your Library! **")

while (True):
  
  print("Menu: ")
  for i in range(len(options)):
    print(str(i) + ": " + options[i])

  user_input = loop_til_valid_val(-1, len(options),
                                  "\nEnter your choice, or -1 to exit: ")

  match (user_input):
    case -1:
      break
    case 0:
      response = insert_book(baseurl)

      if response.status_code != 200:
        print(response.text)
    case 1:
      response = update_reading_progress(baseurl)
      if response.status_code != 200:
        print(response.text)
    case 2:
      response = update_book_rating(baseurl)
    case 3:
      response = get_review_sentiment(baseurl)

print("Done!")
