"""
Application configuration and environment variables
"""

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Application configuration
ENVIRONMENT = os.getenv("VELOCITRACK_ENVIRONMENT", "development")
DEBUG = os.getenv("VELOCITRACK_DEBUG", "False").lower() == "true"
DATABASE_URL = os.getenv("VELOCITRACK_DATABASE_URL")

# API Configuration
API_TITLE = "VelociTrack API"
API_DESCRIPTION = """
VelociTrack is a web service for querying velocity models.

## Features

* **1D Velocity Models**: Query depth-velocity relationships for P-wave and S-wave velocities
* **3D Velocity Models**: Query 3D velocity models (coming soon)
"""
