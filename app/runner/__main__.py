import uvicorn

from app.runner.setup import setup

if __name__ == "__main__":
    uvicorn.run(setup(), host="127.0.0.1", port=8000)
