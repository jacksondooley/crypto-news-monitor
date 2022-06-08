import os
from fastapi import FastAPI, Body, HTTPException, status
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel, Field, EmailStr
from bson import ObjectId
from typing import Optional, List
import motor.motor_asyncio
import schedule
import time
import asyncio
import feedparser


app = FastAPI()
client = motor.motor_asyncio.AsyncIOMotorClient(os.environ["MONGODB_URL"])
db = client.college

sources = {
    'https://decrypt.co/feed': '',
    'https://blockworks.co/feed/': '',
    'https://cryptopotato.com/feed': '',
    'https://cryptobriefing.com/feed/': '',
    'https://dailyhodl.com/feed/': '',
    'https://cointelegraph.com/rss': ''
}

class BackgroundRunner:
    def __init__(self):
        self.value = 0

    def init_sources(self):
        for source in sources:
            source_feed = feedparser.parse(source)
            if 'updated' in source_feed.keys():
                sources[source] = {'modified': source_feed.updated}
            elif 'etag' in source_feed.keys():
                sources[source] = {'etag': source_feed.etag}
            else:
                sources[source] = {'last_entry_link': source_feed.entries[0].link}


    async def run_main(self):
        lastEtag = None
        run_feed = True
        while run_feed:
            for source in sources:
                if 'modified' in sources[source]:
                    d = feedparser.parse(source, modified=sources[source]['modified'])
                    if d.status == 200:
                        sources[source]['modified'] = d.updated
                    else:
                        print(d.status)
                elif 'etag' in sources[source]:
                    d = feedparser.parse(source, etag=sources[source]['etag'])
                    if d.status == 200:
                        sources[source]['etag'] = d.etag
                    else:
                        print(d.status)
                else:
                    d = feedparser.parse(source)
                    if d.entries[0].link == sources[source]['last_entry_link']:
                        print('no change (fake 304)')
                    else:
                        print('change (fake 200)')
            # d = feedparser.parse('https://decrypt.co/feed', etag = lastEtag)
            # lastEtag = d.etag
            # entries = []
            # for entry in d.entries:
            #     entries.append(entry.title)
            # print(entries)
            # print(d.status)
            await asyncio.sleep(60)
            self.value += 1

runner = BackgroundRunner()


# function runs on server startup
# init_sources function fetches sources and sets their modified/etags
# run_main function checks if each source rss feed has updated
@app.on_event("startup")
async def startup_event():
    runner.init_sources()
    asyncio.create_task(runner.run_main())


class PyObjectId(ObjectId):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid objectid")
        return ObjectId(v)

    @classmethod
    def __modify_schema__(cls, field_schema):
        field_schema.update(type="string")


class StudentModel(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    name: str = Field(...)
    email: EmailStr = Field(...)
    course: str = Field(...)
    gpa: float = Field(..., le=4.0)

    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}
        schema_extra = {
            "example": {
                "name": "Jane Doe",
                "email": "jdoe@example.com",
                "course": "Experiments, Science, and Fashion in Nanophotonics",
                "gpa": "3.0",
            }
        }

class EntryModel(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    title: str = Field(...)
    link: str = Field(...)

    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}
        schema_extra = {
            "example": {
                "title": "News",
                "link": "news.com/story"
            }
        }


class UpdateStudentModel(BaseModel):
    name: Optional[str]
    email: Optional[EmailStr]
    course: Optional[str]
    gpa: Optional[float]

    class Config:
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}
        schema_extra = {
            "example": {
                "name": "Jane Doe",
                "email": "jdoe@example.com",
                "course": "Experiments, Science, and Fashion in Nanophotonics",
                "gpa": "3.0",
            }
        }


@app.post("/", response_description="Add new student", response_model=StudentModel)
async def create_student(student: StudentModel = Body(...)):
    student = jsonable_encoder(student)
    new_student = await db["students"].insert_one(student)
    created_student = await db["students"].find_one({"_id": new_student.inserted_id})
    return JSONResponse(status_code=status.HTTP_201_CREATED, content=created_student)


@app.get(
    "/", response_description="List all students", response_model=List[StudentModel]
)
async def list_students():
    students = await db["students"].find().to_list(1000)
    return students


@app.get(
    "/{id}", response_description="Get a single student", response_model=StudentModel
)
async def show_student(id: str):
    if (student := await db["students"].find_one({"_id": id})) is not None:
        return student

    raise HTTPException(status_code=404, detail=f"Student {id} not found")


@app.put("/{id}", response_description="Update a student", response_model=StudentModel)
async def update_student(id: str, student: UpdateStudentModel = Body(...)):
    student = {k: v for k, v in student.dict().items() if v is not None}

    if len(student) >= 1:
        update_result = await db["students"].update_one({"_id": id}, {"$set": student})

        if update_result.modified_count == 1:
            if (
                updated_student := await db["students"].find_one({"_id": id})
            ) is not None:
                return updated_student

    if (existing_student := await db["students"].find_one({"_id": id})) is not None:
        return existing_student

    raise HTTPException(status_code=404, detail=f"Student {id} not found")


@app.delete("/{id}", response_description="Delete a student")
async def delete_student(id: str):
    delete_result = await db["students"].delete_one({"_id": id})

    if delete_result.deleted_count == 1:
        return JSONResponse(status_code=status.HTTP_204_NO_CONTENT)

    raise HTTPException(status_code=404, detail=f"Student {id} not found")


