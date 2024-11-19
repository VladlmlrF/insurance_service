import uvicorn
from fastapi import FastAPI

from insurance_app.api import router as api_router


app = FastAPI(title="Insurance service")

app.include_router(api_router)


if __name__ == "__main__":
    uvicorn.run("insurance_app.main:app", host="localhost", port=8001, reload=True)
