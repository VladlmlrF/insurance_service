#!/bin/sh

uvicorn insurance_app.main:app --host 0.0.0.0 --port 8001
