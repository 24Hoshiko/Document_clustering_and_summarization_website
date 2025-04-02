import uvicorn
from fastapi import FastAPI, UploadFile
from fastapi.middleware.cors import CORSMiddleware
import os
import shutil
import subprocess
from fastapi.responses import FileResponse

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_FOLDER = "uploaded_docs"
CLUSTERED_FOLDER = "clustered_docs"

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(CLUSTERED_FOLDER, exist_ok=True)

# Flag to prevent multiple clustering runs
is_clustering = False

@app.post("/upload/")
async def upload_files(files: list[UploadFile]):
    global is_clustering
    if is_clustering:
        return {"message": "Clustering is already in progress. Please wait."}

    is_clustering = True
    try:
        uploaded_filenames = []
        shutil.rmtree(UPLOAD_FOLDER, ignore_errors=True)
        shutil.rmtree(CLUSTERED_FOLDER, ignore_errors=True)
        os.makedirs(UPLOAD_FOLDER)
        os.makedirs(CLUSTERED_FOLDER)

        for file in files:
            safe_filename = os.path.basename(file.filename)
            file_path = os.path.join(UPLOAD_FOLDER, safe_filename)
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            uploaded_filenames.append(safe_filename)

        # Run clustering
        subprocess.run(["python", "text_processing.py"], check=True)
        return {"message": "Files uploaded and clustered successfully!", "processed_files": uploaded_filenames}
    except subprocess.CalledProcessError as e:
        return {"message": "Files uploaded, but clustering failed!", "error": str(e)}
    finally:
        is_clustering = False

@app.get("/clusters/")
async def get_clustered_documents():
    clustered_data = {}
    for category in os.listdir(CLUSTERED_FOLDER):
        category_path = os.path.join(CLUSTERED_FOLDER, category)
        if os.path.isdir(category_path):
            files = os.listdir(category_path)
            clustered_data[category] = {
                "files": files,
                "summaries": [f for f in files if f in ["similarities.txt", "differences.txt"]]
            }
    return {"clusters": clustered_data}

@app.get("/file/{category}/{filename}")
async def get_file(category: str, filename: str):
    file_path = os.path.join(CLUSTERED_FOLDER, category, filename)
    if os.path.exists(file_path):
        return FileResponse(file_path)
    return {"error": "File not found"}

@app.post("/summarize/{category}")
async def summarize_cluster(category: str):
    cluster_path = os.path.join(CLUSTERED_FOLDER, category)
    if not os.path.exists(cluster_path):
        return {"error": "Cluster not found"}

    try:
        subprocess.run(["python", "para_cluster.py", cluster_path], check=True)
    except subprocess.CalledProcessError as e:
        return {"error": f"Summarization failed: {str(e)}"}

    return {"message": f"Summaries generated for {category}"}

if __name__ == "__main__":
    uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=False)