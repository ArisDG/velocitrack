#!/usr/bin/env python3
"""
Run the VelociTrack Service
"""
import uvicorn
import sys
import os

if __name__ == "__main__":
    # Add project root to Python path
    project_root = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, project_root)

    # Run with import string to enable reload
    uvicorn.run("velocitrack.main:app", host="0.0.0.0", port=8001, reload=True)
