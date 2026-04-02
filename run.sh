#!/bin/bash

# Start the FastAPI backend in the background
echo "Starting FastAPI Backend..."
uvicorn backend.main:app --host 0.0.0.0 --port 8000 &

# Give the backend a few seconds to boot up before launching the UI
sleep 5

# Start the Streamlit frontend in the foreground
echo "Starting Streamlit Frontend..."
export API_URL="http://127.0.0.1:8000"
streamlit run frontend/app.py --server.port=8501 --server.address=0.0.0.0
