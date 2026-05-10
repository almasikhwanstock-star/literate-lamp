#!/bin/bash
echo "Starting Shutterstock AI Backend..."
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
