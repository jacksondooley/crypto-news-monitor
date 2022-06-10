import os
from fastapi import FastAPI, Body, HTTPException, status
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from bson import ObjectId
from typing import Optional, List
from urllib.request import Request, urlopen
import motor.motor_asyncio
import schedule
import time
from time import gmtime, strftime
import asyncio
import feedparser
import pandas as pd
import mymodels
import re
from bs4 import BeautifulSoup


app = FastAPI()
client = motor.motor_asyncio.AsyncIOMotorClient(os.environ["MONGODB_URL"])
db = client.feed_reader


class BackgroundRunner:
    def __init__(self):
        self.interrupt = False
        self.sources = {}
        self.entries = []
        self.matches = []
        self.pattern = ""
    

    def set_sources(self, sources):
        new_sources = {}
        for source in sources:
            url = source['url']
            source_feed = feedparser.parse(url)
            self.append_entries(source_feed)
            if 'updated' in source_feed.keys():
                new_sources[url] = {'modified': source_feed.updated}
            elif 'etag' in source_feed.keys():
                new_sources[url] = {'etag': source_feed.etag}
            else:
                new_sources[url] = {'last_entry_link': source_feed.entries[0].link}
        self.sources = new_sources


    def append_entries(self, feed):
        for entry in feed.entries[0:30]:
            new_entry = {}
            new_entry["title"] = entry.title
            new_entry["link"] = entry.link
            new_entry["source"] = feed.feed.title
            new_entry["published"] = entry.published
            new_entry["summary"] = entry.summary
            new_entry["content"] = entry.content if "content" in entry.keys() else None
            self.entries.append(new_entry)

    def append_entry(self, entry, source):
        new_entry = {}
        new_entry["title"] = entry.title
        new_entry["link"] = entry.link
        new_entry["source"] = source.title
        new_entry["published"] = entry.published
        new_entry["summary"] = entry.summary
        new_entry["content"] = entry.content if "content" in entry.keys() else None
        self.entries.append(new_entry)

        if self.pattern == "":
            df = pd.DataFrame(new_entry)
            print(df)
        else: 
            self.check_for_match(entry)

    def check_for_match(self, entry):
        if self.pattern == "":
            return
        soup = BeautifulSoup(entry["summary"], "lxml")
        matches = soup.find_all(string=re.compile(self.pattern))
        if matches:
            self.matches.append(entry)
        elif entry['content'] != None:
            content = entry["content"][0].value
            soup = BeautifulSoup(content, "lxml")
            matches = soup.find_all(string=re.compile(self.pattern))
            if matches:
                print(entry['title'] + ' contains ' + self.pattern)
            else:
                print("no match")
        else:
            req = Request(entry["link"], headers={'User-Agent': 'Mozilla/5.0`'})
            page = urlopen(req).read()
            soup = BeautifulSoup(page, "lxml")
            if soup.body.find("div", class_="post-content"):
                soup = soup.body.find("div", class_="post-content")
                matches = soup.find_all(string=re.compile(self.pattern))
                if matches:
                    print(entry['title'] + ' contains ' + self.pattern)
                else:
                    print("no match")
            elif soup.body.find("section", class_="article-content"):
                soup = soup.body.find("section", class_="article-content")
                matches = soup.find_all(string=re.compile(self.pattern))
                if matches:
                    print(entry['title'] + ' contains ' + self.pattern)
                else:
                    print("no match")
            else:
                print(entry['title'] + " has no post-content")

    def check_for_matches(self):
        for idx, entry in enumerate(self.entries):
            entry["match"] = False
            entry["pattern"] = self.pattern
            soup = BeautifulSoup(entry["summary"], "lxml")
            matches = soup.find_all(string=re.compile(self.pattern))
            if matches:
                self.matches.append(entry)
                entry["match"] = True
            elif entry['content'] != None:
                content = entry["content"][0].value
                soup = BeautifulSoup(content, "lxml")
                matches = soup.find_all(string=re.compile(self.pattern))
                if matches:
                    self.matches.append(entry)
                    entry["match"] = True
            else:
                req = Request(entry["link"], headers={'User-Agent': 'Mozilla/5.0`'})
                page = urlopen(req).read()
                soup = BeautifulSoup(page, "lxml")
                if soup.body.find("div", class_="post-content"):
                    soup = soup.body.find("div", class_="post-content")
                    matches = soup.find_all(string=re.compile(self.pattern))
                    if matches:
                        self.matches.append(entry)
                        entry["match"] = True
                elif soup.body.find("section", class_="article-content"):
                    soup = soup.body.find("section", class_="article-content")
                    matches = soup.find_all(string=re.compile(self.pattern))
                    if matches:
                        self.matches.append(entry)
                        entry["match"] = True
            df = pd.DataFrame(entry, index=[idx])
            print(df)



    async def run_main(self):
        scan_feeds = True
        df = pd.DataFrame(self.entries)
        print(df)
        while scan_feeds:
            print("checking feeds " + strftime("%Y-%m-%d %H:%M:%S", gmtime()))
            for source in self.sources:
                if 'modified' in self.sources[source]:
                    d = feedparser.parse(source, modified=self.sources[source]['modified'])
                    if d.status == 200:
                        print("feed has not updated")
                        self.sources[source]['modified'] = d.updated
                        self.append_entry(d.entries[0], d.feed.title)
                    elif d.status == 304:
                        print("feed has not updated")
                    else:
                        print(d.status)
                elif 'etag' in self.sources[source]:
                    d = feedparser.parse(source, etag=self.sources[source]['etag'])
                    if d.status == 200:
                        print("feed has updated")
                        self.sources[source]['etag'] = d.etag
                        self.append_entry(d.entries[0], d.feed.title)
                    elif d.status == 304:
                        print("feed has not updated")
                    else:
                        print(d.status)
                else:
                    d = feedparser.parse(source)
                    if d.entries[0].link == self.sources[source]['last_entry_link']:
                        print('feed has not updated')
                    else:
                        print('change (fake 200)')
                        self.append_entry(d.entries[0], d.feed.title)
            await asyncio.sleep(59)

    



runner = BackgroundRunner()


# function runs on server startup
# init_sources function fetches sources and sets their modified/etags
# run_main function checks if each source rss feed has updated
@app.on_event("startup")
async def startup_event():
    sources = await list_sources()
    runner.set_sources(sources)
    asyncio.create_task(runner.run_main())

@app.get("/news", response_description="Get all news")
async def list_news():
    news = runner.entries
    return news



@app.post("/source", response_description="Add new source", response_model=mymodels.SourceModel)
async def add_source(source: mymodels.SourceModel = Body(...)):
    source = jsonable_encoder(source)
    feed = feedparser.parse(source["url"])
    if feed.version[0:3] == 'rss':
        new_source = await db["sources"].insert_one(source)
        created_source = await db["source"].find_one({"_id": new_source.inserted_id})
        return JSONResponse(status_code=status.HTTP_201_CREATED, content=created_source)
    raise HTTPException(status_code=400, detail=f"Source is not valid rss feed")
    

@app.get("/sources", response_description="List all sources", response_model=List[mymodels.SourceModel])
async def list_sources():
    sources = await db["sources"].find().to_list(100)
    return sources


@app.get("/source/{id}", response_description="Get a single source", response_model=mymodels.SourceModel)
async def show_source(id: str):
    if (source := await db["sources"].find_one({"_id": id})) is not None:
        return source
    
    raise HTTPException(status_code=404, detail=f"Source {id} not found")


@app.put("/source/{id}", response_description="Update a source", response_model=mymodels.SourceModel)
async def update_souce(id: str, source: mymodels.UpdateSourceModel = Body(...)):
    source = {k: v for k, v in source.dict().items() if v is not None}

    if len(source) >= 1:
        update_result = await db["sources"].update_one({"_id": id}, {"$set": source})

        
        if update_result.modified_count == 1:
            if (
                updated_source := await db["sources"].find_one({"_id": id})
            ) is not None:
                return updated_source
    
    if (existing_source := await db["sources"].find_one({"_id": id})) is not None:
        return existing_source

    raise HTTPException(status_code=404, detail=f"source {id} not found")


@app.delete("/source/{id}", response_description="Delete a source")
async def delete_source(id: str):
    delete_result = await db["source"].delete_one({"_id": id})

    if delete_result.deleted_count == 1:
        return JSONResponse(status_code=status.HTTP_204_NO_CONTENT)

    raise HTTPException(status_code=404, detail=f"Source {id} not found")

@app.get("/pattern", response_description="Get current pattern")
async def show_pattern():
    if runner.pattern == "":
        return "no pattern"
    else:
        return runner.pattern

@app.post("/pattern", response_description="Set pattern for news")
async def set_pattern(pattern: str):
    runner.pattern = pattern
    print(pattern)

@app.delete("/pattern", response_description="Clears pattern")
async def clear_pattern():
    runner.pattern = ""
    return "pattern cleared"

@app.get("/matches", response_description="Get all news that matches pattern (Will take ~2 minutes)")
async def list_matches():
    runner.check_for_matches()
    news = runner.matches
    return news