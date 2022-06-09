import feedparser
from urllib.request import Request, urlopen
from bs4 import BeautifulSoup
import re
import pandas as pd

print('hello worlddd')

entries = []


# 
d = feedparser.parse('https://decrypt.co/feed')
print(d.feed.keys())
# entries.append(d)

# # has div with class post-content
d = feedparser.parse('https://blockworks.co/feed/')
# entries.append(d)


# d = feedparser.parse('https://cryptopotato.com/feed')
# entries.append(d)

# d = feedparser.parse('https://cryptobriefing.com/feed/')
# entries.append(d)

# section with class article-content but soup strainer section with class recommended-posts
# d = feedparser.parse('https://dailyhodl.com/feed/')
# entries.append(d)
# d = feedparser.parse('https://cointelegraph.com/rss',   request_headers={'Accept-Encoding': 'gzip'})
cleansed = []
for entry in d.entries:
    new_entry = {}
    new_entry["title"] = entry.title
    new_entry["tags"] = []
    for tag in entry.tags:
        new_entry["tags"].append(tag.term)
    cleansed.append(new_entry)

df = pd.DataFrame(cleansed)
print(df)
# has div with class post-content

# print(d.modified)
# d2 = feedparser.parse('https://dailyhodl.com/feed/', modified=d.modified)
# print(d2.status)

# print(len(d.entries))

# URL = d.entries[2].link
# req = Request(URL, headers={'User-Agent': 'Mozilla/5.0`'})
# page = urlopen(req).read()

# soup = BeautifulSoup(page, "html.parser")

# body_text = soup.find("body")





# pattern = "bitcoin|ethereum"

# for entry in entries:
#     # if entry.keys() content:
#     print(entry[0].title)

    # req = Request(entry.link, headers={'User-Agent': 'Mozilla/5.0`'})
    # page = urlopen(req).read()

    # soup = BeautifulSoup(page, "html.parser")

    # body_text = soup.find("body").get_text()
    # content = soup.body.find_all("div", class_=re.compile("content"))
    # for c in content:
    #     c = c.get_text()
    #     match = re.search(".*((Ethereum)|(ETH)).*((fork)|(upgrad)).*", c)
    #     if match:
    #         matches.append(entry.link)
    # print(entry.feed.keys())
    # print("|")
    # print(entry.headers)
    # print("-------")
    

# print(matches)
# print(len(matches))
# print(len(d.entries))