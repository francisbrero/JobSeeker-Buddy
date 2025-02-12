#!/bin/bash
# filepath: /Users/francis/Documents/MadKudu/JobSeeker-Buddy/start.sh

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install requirements
echo "Installing requirements..."
pip install -r requirements.txt

# Start the FastAPI backend
echo "Starting FastAPI backend..."
uvicorn main:app --host 0.0.0.0 --port 8000 &

# Start the Streamlit app (assumes you have streamlit_app.py)
echo "Starting Streamlit app..."
streamlit run app.py --server.address=0.0.0.0 --server.port=8501

# Wait for foreground process (Streamlit) to exit before deactivating venv
wait