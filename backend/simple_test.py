"""シンプルなテストサーバー"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from pathlib import Path
import os

app = FastAPI(title="Test Server")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {"message": "Test server is running"}

@app.get("/api/sync/test")
def test_sync():
    csv_dir = Path("./data/csv")
    files = []
    if csv_dir.exists():
        for file in csv_dir.glob("*.csv"):
            files.append(file.name)
    return {"csv_files": files}

if __name__ == "__main__":
    print("Starting test server on port 8001...")
    uvicorn.run(app, host="0.0.0.0", port=8001)