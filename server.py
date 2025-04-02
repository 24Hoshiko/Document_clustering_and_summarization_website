import uvicorn
from fastapi import FastAPI, UploadFile
from fastapi.middleware.cors import CORSMiddleware
import os

app = FastAPI()

# Enable CORS for frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Change this to a specific frontend domain in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
import uvicorn
from fastapi import FastAPI, UploadFile
from fastapi.middleware.cors import CORSMiddleware
import os
import shutil
import subprocess

app = FastAPI()

# Enable CORS for frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Change this to a specific frontend domain in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_FOLDER = "uploaded_docs"
CLUSTERED_FOLDER = "clustered_docs"

# Ensure required folders exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(CLUSTERED_FOLDER, exist_ok=True)

@app.post("/upload/")
async def upload_files(files: list[UploadFile]):
    """Handles file uploads and triggers document clustering."""
    
    uploaded_filenames = []
    
    for file in files:
        # Extract only the filename without directory structure
        safe_filename = os.path.basename(file.filename)  
        file_path = os.path.join(UPLOAD_FOLDER, safe_filename)

        # Save the file
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        uploaded_filenames.append(safe_filename)

    # Run document clustering after upload
    try:
        subprocess.run(["python", "document_clustering.py"], check=True)
    except subprocess.CalledProcessError as e:
        return {"message": "Files uploaded, but clustering failed!", "error": str(e)}

    return {"message": "Files uploaded and clustered successfully!", "processed_files": uploaded_filenames}


@app.get("/clusters/")
async def get_clustered_documents():
    """Retrieve clustered document categories and filenames."""
    
    clustered_data = {}
    
    for category in os.listdir(CLUSTERED_FOLDER):
        category_path = os.path.join(CLUSTERED_FOLDER, category)
        
        if os.path.isdir(category_path):  # Ensure it's a folder
            clustered_data[category] = os.listdir(category_path)

    return {"clusters": clustered_data}


if __name__ == "__main__":
    uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=True)

UPLOAD_FOLDER = "uploaded_docs"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.post("/upload/")
async def upload_files(files: list[UploadFile]):
    for file in files:
        safe_filename = file.filename.replace("\\", "/")
        file_path = os.path.join(UPLOAD_FOLDER, safe_filename)

        os.makedirs(os.path.dirname(file_path), exist_ok=True)

        with open(file_path, "wb") as buffer:
            buffer.write(await file.read())

    return {"message": "Files uploaded successfully!"}

# ✅ Correct way to run directly
if __name__ == "__main__":
    uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=True)
