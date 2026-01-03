
## Run Locally 

If you prefer running without Docker, you will need **two separate terminals**.

### 1. Prerequisite: Install Dependencies
From the project root, install the required packages:
```bash

pip install -r requirements.txt
```

Terminal 1: Start the Backend API

This starts the FastAPI server on port 8002.
```bash
# Run from the root directory
uvicorn server.app.main:app --reload
```


Terminal 2: Start the Frontend Interface
The frontend will open in your browser (usually http://localhost:8501).
```bash
# Run from the root directory
streamlit run client/app.py
```

