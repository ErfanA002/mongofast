from fastapi import FastAPI, File, UploadFile
from fastapi.responses import JSONResponse, FileResponse
from pymongo import MongoClient
from datetime import datetime
from bson import Binary, ObjectId
import io

app = FastAPI()

client = MongoClient("mongodb://admin:admin@localhost:27017/")

db = client["my_dynamic_db"]

collection = db["user_data"]

def serialize_doc(doc):
    doc["_id"] = str(doc["_id"])
    if "_received_at" in doc and isinstance(doc["_received_at"], datetime):
        doc["_received_at"] = doc["_received_at"].isoformat()
    return doc

@app.post("/collect")
async def collect_data(file: UploadFile = File(None), body: dict = None):
    try:

        if file:

            file_content = await file.read()

            file_data = {
                "file_data": Binary(file_content),
                "file_name": file.filename,
                "content_type": file.content_type
            }

        else:
            file_data = {}

        if body is None:
            body = {}

        body.update(file_data)

        body["_received_at"] = datetime.utcnow()

        result = collection.insert_one(body)

        return JSONResponse(status_code=200, content={"status": "ok", "id": str(result.inserted_id)})
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

@app.get("/collect")
def get_all_data():
    try:

        data = list(collection.find())

        return JSONResponse(content=[serialize_doc(doc) for doc in data])
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

@app.get("/file/{file_id}")
async def get_file(file_id: str):
    try:

        file_data = collection.find_one({"_id": ObjectId(file_id)})

        if file_data and "file_data" in file_data:

            return FileResponse(
                io.BytesIO(file_data["file_data"]),
                media_type=file_data["content_type"],
                filename=file_data["file_name"]
            )
        else:
            return JSONResponse(status_code=404, content={"error": "File not found"})
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})