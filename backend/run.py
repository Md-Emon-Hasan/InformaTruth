import uvicorn
import os
import sys

# Ensure the root directory is in the python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

if __name__ == "__main__":
    # Set reload=False for stable operation with heavy models
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=False)
