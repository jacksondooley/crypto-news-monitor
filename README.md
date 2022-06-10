# crypto-news-monitor

This project is a crypto news monitor that working by scanning RSS feeds using [FastAPI](https://fastapi.tiangolo.com/), [MongoDB](https://developer.mongodb.com/), [FeedParser](https://feedparser.readthedocs.io/en/latest/index.html), and [BeautifulSoup](https://beautiful-soup-4.readthedocs.io/en/latest/#). 




## Instructions

If you really don't want to read the [blog post](https://developer.mongodb.com/quickstart/python-quickstart-fastapi/) and want to get up and running,
activate your Python virtualenv, and then run the following from your terminal (edit the `DB_URL` first!):

```bash
# Install the requirements:
pip install -r requirements.txt

# Configure the location of your MongoDB database:
export MONGODB_URL="mongodb+srv://rick:XyShRHwg5JGgAYEc@cluster0.w7hqp.mongodb.net/?retryWrites=true&w=majority"
# Please be nice to my database Messari friends.

# Start the service:
uvicorn app:app --reload
```

Now you can load http://localhost:8000 in your browser
Checkout http://localhost:8000/docs, FastAPI provides built in docs that shows the functionality of the project.

