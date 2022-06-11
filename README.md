# Crypto News Monitor

## About

This project is a crypto news monitor that working by scanning RSS feeds using [FastAPI](https://fastapi.tiangolo.com/), [MongoDB](https://developer.mongodb.com/), [FeedParser](https://feedparser.readthedocs.io/en/latest/index.html), and [BeautifulSoup](https://beautiful-soup-4.readthedocs.io/en/latest/#). 


## Instructions
 To get started, activate your Python virtualenv, and then run the following from your terminal:

```bash
# Install the requirements:
pip install -r requirements.txt

# Configure the location of your MongoDB database:
export MONGODB_URL="mongodb+srv://rick:XyShRHwg5JGgAYEc@cluster0.w7hqp.mongodb.net/?retryWrites=true&w=majority"
# Please be nice to my database Messari friends.

# Start the service:
uvicorn app:app --reload
```

Now you can load http://localhost:8000 in your browser.
Checkout http://localhost:8000/docs, FastAPI provides built in docs that shows the functionality of the project.
![FastAPI_docs.png](FastAPI_docs.png)



## How it works
 There is two main components to this project, the RSS Feed Scanner to receive the articles from feeds and the Pattern Checker that utilizes a web scraper to check articles for REGEX patterns.
### RSS Feed Scanner
    1. Server starts and startup event triggers function, which pulls sources from database and starts feed scanner.
    2. Feeds get initially scanned and have all feed entries streamed to stdout and made available to /news API.
    3. Every minute feeds are checked for changes using modified or etag rss header. (allows feed scanner to check for changes without receiving entire feed) Besides cointelegraph, as they did not include these headers.
        3a. If there are no changes detected, "feed has not updated" will be streamed.
        3b. If there are changes detected, "feed has updated" will be streamed and the new entry will be printed.

### Pattern Checker
    1. Pattern is set using /pattern post API
    2. Entries are checked using check_for_matches function after /matches get API
    3. Entries are iterated through and checked individually.
        3a. First, an entry is checked to see if it has content from RSS feed. If it does, it saves a request to it's url and can be checked quickly
        3b. If it doesn't have content, urllib is used to request the url and then scrape the article's content for matches.