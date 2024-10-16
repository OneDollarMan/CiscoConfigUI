import uvicorn

if __name__ == "__main__":
    uvicorn.run("src.routes:app", host="127.0.0.1", log_level="info")
