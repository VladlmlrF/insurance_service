import uvicorn
from fastapi import FastAPI


app = FastAPI(title="Insurance service")


if __name__ == "__main__":
    uvicorn.run("insurance_app.main:app", host="localhost", port=8001, reload=True)
