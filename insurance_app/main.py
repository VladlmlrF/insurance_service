import atexit
import threading
import time

import uvicorn
from fastapi import FastAPI

from insurance_app.api import router as api_router
from insurance_app.api.api_v1.rates.crud import kafka_producer

atexit.register(kafka_producer.close)

app = FastAPI(title="Insurance service")

app.include_router(api_router)


def periodic_flush(producer, interval=5):
    while True:
        time.sleep(interval)
        producer.flush()
        producer.retry_failed_messages()


threading.Thread(target=periodic_flush, args=(kafka_producer,), daemon=True).start()


if __name__ == "__main__":
    uvicorn.run("insurance_app.main:app", host="localhost", port=8001, reload=True)
