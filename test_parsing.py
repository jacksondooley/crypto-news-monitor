import feedparser
from urllib.request import Request, urlopen
from bs4 import BeautifulSoup
import re

print('hello worlddd')

d = feedparser.parse('https://decrypt.co/feed')
# d = feedparser.parse('https://blockworks.co/feed/')
# d = feedparser.parse('https://cryptopotato.com/feed')
# d = feedparser.parse('https://cryptobriefing.com/feed/')
# d = feedparser.parse('https://dailyhodl.com/feed/')
# d = feedparser.parse('https://cointelegraph.com/rss')
# d2 = feedparser.parse('https://cointelegraph.com/rss', modified=d.feed.updated)

# print(d.modified)
# d2 = feedparser.parse('https://dailyhodl.com/feed/', modified=d.modified)
# print(d2.status)

# print(len(d.entries))

# URL = d.entries[2].link
# req = Request(URL, headers={'User-Agent': 'Mozilla/5.0`'})
# page = urlopen(req).read()

# soup = BeautifulSoup(page, "html.parser")

# body_text = soup.find("body")


matches = []

pattern = "bitcoin|ethereum"

for entry in d.entries:
    URL = entry.link
    req = Request(URL, headers={'User-Agent': 'Mozilla/5.0`'})
    page = urlopen(req).read()

    soup = BeautifulSoup(page, "html.parser")

    body_text = soup.find("body").get_text()
    # print(body_text)
    match = re.search(".*((Ethereum)|(ETH)).*((fork)|(upgrad)).*", body_text)
    if match:
        matches.append(URL)

print(matches)
print(len(matches))
print(len(d.entries))