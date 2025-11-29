# VelociTrack

A FastAPI + PostgreSQL system for managing and querying seismic velocity models.

## Features

- **1D Velocity Models**: Store and query 1D velocity models with depth-velocity relationships
- **3D Velocity Models**: Store and query separate VP and VS 3D velocity models with geographical coordinates
- **Author Bibliographic References**: Link authors to their bibliographic citations
- **RESTful API**: FastAPI-based web service with automatic documentation at `/docs`
- **PostgreSQL Backend**: Reliable database storage for velocity data
- **Pagination**: Handle large datasets with limit/offset pagination
- **Data Import**: Tools for importing velocity model data from CSV/Excel files
- **Duplicate Prevention**: Automatic duplicate detection during data import
- **Multiple Output Formats**: VELEST format for 1D models, pipe-delimited for 3D models

---

## Table of Contents

1. [Installation](#installation)
2. [Configuration](#configuration)
3. [Running the Server](#running-the-server)
4. [Running as a System Service](#running-as-a-system-service)
5. [API Reference](#api-reference)
6. [Data Import](#data-import)
7. [Data Models](#data-models)

---

## Installation

### Prerequisites

- Python 3.10+
- PostgreSQL database
- pip

### Steps

```bash
# 1. Clone the repository
git clone https://github.com/ArisDG/seismotrack.git
cd velocitrack

# 2. Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate

# 3. Install the package and dependencies
pip install -e .

# 4. Create the database (PostgreSQL)
sudo -u postgres psql -c "CREATE DATABASE velocitycatalogues;"
```

---

## Configuration

Create a `.env` file in the project root with your database configuration:

```env
DATABASE_URL=postgresql://postgres:your_password@localhost/velocitycatalogues
```

---

## Running the Server

### Development Mode

```bash
source venv/bin/activate
python src/run_server.py
```

The server will start on `http://localhost:8001` with automatic API documentation at `http://localhost:8001/docs`.

---

## Running as a System Service

To run VelociTrack as a persistent background service using systemd:

### 1. Create a systemd service file

```bash
sudo nano /etc/systemd/system/velocitrack.service
```

### 2. Add the following configuration

```ini
[Unit]
Description=VelociTrack Velocity Model API Service
After=network.target postgresql.service

[Service]
Type=simple
User=your_username
Group=your_username
WorkingDirectory=/path/to/velocitrack
Environment="PATH=/path/to/velocitrack/venv/bin"
EnvironmentFile=/path/to/velocitrack/.env
ExecStart=/path/to/velocitrack/venv/bin/python src/run_server.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Replace:
- `your_username` with your system username
- `/path/to/velocitrack` with the actual path to the project

### 3. Enable and start the service

```bash
# Reload systemd to recognize the new service
sudo systemctl daemon-reload

# Enable the service to start on boot
sudo systemctl enable velocitrack

# Start the service
sudo systemctl start velocitrack

# Check status
sudo systemctl status velocitrack

# View logs
sudo journalctl -u velocitrack -f
```

### 4. Service management commands

```bash
sudo systemctl start velocitrack    # Start the service
sudo systemctl stop velocitrack     # Stop the service
sudo systemctl restart velocitrack  # Restart the service
sudo systemctl status velocitrack   # Check status
```

---

## API Reference

### Endpoints Overview

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Service information and version |
| `/1d/` | GET | Query 1D velocity models |
| `/3d/` | GET | Query 3D velocity models |
| `/authors` | GET | List all unique authors |
| `/nfos` | GET | List all unique NFO identifiers |

---

### `GET /`

Returns service information.

**Example Request:**
```bash
curl http://localhost:8001/
```

**Example Response:**
```json
{
  "service": "VelociTrack API",
  "version": "0.1.0"
}
```

---

### `GET /1d/`

Query 1D velocity models by author and NFO. Returns data in VELEST format.

#### Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `author` | string | Yes | - | Author/reference to filter by (partial match) |
| `nfo` | string | Yes | - | Network/Organization identifier (partial match) |
| `limit` | integer | No | 10000 | Maximum records to return (1-100000) |
| `offset` | integer | No | 0 | Number of records to skip for pagination |

**Example Request:**
```bash
curl "http://localhost:8001/1d/?author=test_1d&nfo=TEST"
```

**Example Response:**
```
1D TEST_NFO Test_1D_Reference
 8        vel,depth,vdamp,phase (f5.2,5x,f7.2,2x,f7.3,3x,a1)
 4.80       -3.00   001.000           P-VELOCITY MODEL
 4.80        0.00   001.000
 5.20        4.00   001.000
 5.80        7.20   001.000
 6.10        8.20   001.000
 6.30       10.40   001.000
 6.50       15.00   001.000
 7.00       30.00   001.000
 8
 2.67       -3.00   001.000           S-VELOCITY MODEL
 2.67        0.00   001.000
 2.89        4.00   001.000
 3.22        7.20   001.000
 3.39        8.20   001.000
 3.50       10.40   001.000
 3.61       15.00   001.000
 3.89       30.00   001.000
```

---

### `GET /3d/`

Query 3D velocity models by wave type and author. Returns pipe-delimited data.

#### Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `wave_type` | string | Yes | - | Wave type: `VP` or `VS` |
| `author` | string | Yes | - | Author/reference to filter by (partial match) |
| `include_r` | boolean | No | false | Include R column in output. Only shown if true AND R values differ from 1.0 |
| `limit` | integer | No | 10000 | Maximum records to return (1-100000) |
| `offset` | integer | No | 0 | Number of records to skip for pagination |

**Example Request (VP without R):**
```bash
curl "http://localhost:8001/3d/?wave_type=VP&author=test_3d"
```

**Example Response:**
```
3D TEST_NFO Test_3D_Reference
Longitude|Latitude|Depth|Vp
21.4|37.98|2|4.758679
21.4|38.01|2|4.736545
21.4|38.04|2|4.73316
21.4|38.07|2|4.734217
21.4|38.1|2|4.802973
```

**Example Request (VS with R column):**
```bash
curl "http://localhost:8001/3d/?wave_type=VS&author=test_3d&include_r=true"
```

**Example Response:**
```
3D TEST Test 3D Reference
Longitude|Latitude|Depth|Vs|R
21.4|37.98|2|2.758679|0.5
21.4|38.01|2|2.736545|1
21.4|38.04|2|2.73316|1
21.4|38.07|2|2.734217|1
21.4|38.1|2|2.802973|1
```

**Example with Pagination:**
```bash
# Get first 1000 records
curl "http://localhost:8001/3d/?wave_type=VP&author=test_3d&limit=1000"

# Get next 1000 records (page 2)
curl "http://localhost:8001/3d/?wave_type=VP&author=test_3d&limit=1000&offset=1000"
```

**Response with Pagination Info (when more data exists):**
```
3D TEST_NFO Test_3D_Reference
# Showing 1-1000 of 50000 records (limit=1000, offset=0)
Longitude|Latitude|Depth|Vp
...
```

---

### `GET /authors`

Returns all unique authors across all velocity model tables.

**Example Request:**
```bash
curl http://localhost:8001/authors
```

**Example Response:**
```
test_1d
test_3d
```

---

### `GET /nfos`

Returns all unique NFO identifiers across all velocity model tables.

**Example Request:**
```bash
curl http://localhost:8001/nfos
```

**Example Response:**
```
TEST_NFO
```

---

### Error Responses

#### 404 - No Data Found
```json
{
  "detail": "No VP data found for author: unknown_author"
}
```

#### 400 - Invalid Offset
```json
{
  "detail": "Offset 100000 exceeds total records (5000). Max offset: 4999"
}
```

---

## Data Import

### Import 1D Velocity Models

```bash
python scripts/import_data.py 1d data/sample_1d.csv
```

**Required CSV columns:** `Depth (km)`, `Velocity (km/s)`, `Type`, `NFO`, `Author`

### Import 3D Velocity Models

```bash
# Import VP data
python scripts/import_data.py 3d data/sample_3d_vp.csv vp

# Import VS data
python scripts/import_data.py 3d data/sample_3d_vs.csv vs
```

**Required CSV columns:** `Longitude`, `Latitude`, `Depth`, `Vp` (or `Vs`), `NFO`, `Author`
**Optional CSV columns:** `R`

### Import Author Bibliographic References

```bash
python scripts/import_data.py bibref data/sample_bibrefs.csv
```

**Required CSV columns:** `Author`, `Bibref`

### Sample CSV Formats

**1D Model (`data/sample_1d.csv`):**
```csv
Depth (km),Velocity (km/s),Type,NFO,Author
-3.0,4.80,VP,TEST,test_1d
0.0,4.80,VP,TEST,test_1d
4.0,5.20,VP,TEST,test_1d
```

**3D VP Model (`data/sample_3d_vp.csv`):**
```csv
Longitude,Latitude,Depth,Vp,NFO,Author
21.4,37.98,2,4.758679,TEST,test_3d
21.4,38.01,2,4.736545,TEST,test_3d
```

**3D VS Model with R (`data/sample_3d_vs.csv`):**
```csv
Longitude,Latitude,Depth,Vs,NFO,Author,R
21.4,37.98,2,2.758679,TEST,test_3d,0.5
21.4,38.01,2,2.736545,TEST,test_3d,1
```

**Author References (`data/sample_bibrefs.csv`):**
```csv
Author,Bibref
test_1d,Test 1D Reference
test_3d,Test 3D Reference
```

---

## Data Models

### Database Tables

| Table | Description |
|-------|-------------|
| `velocity_models_1d` | 1D velocity models with depth-velocity pairs |
| `velocity_models_3d_vp` | 3D P-wave velocity models |
| `velocity_models_3d_vs` | 3D S-wave velocity models |
| `author_bibrefs` | Author to bibliographic reference mapping |

### Schema Details

**VelocityModel1D:**
- `depth` (Float): Depth in kilometers
- `velocity` (Float): Velocity in km/s
- `wave_type` (String): VP or VS
- `nfo` (String): Network/Organization identifier
- `author` (String): Reference/source

**VelocityModel3D_VP / VelocityModel3D_VS:**
- `longitude` (Float): Geographic longitude
- `latitude` (Float): Geographic latitude
- `depth` (Float): Depth in kilometers
- `vp` / `vs` (Float): Velocity in km/s
- `r` (Float): R parameter (optional, defaults to 1.0)
- `nfo` (String): Network/Organization identifier
- `author` (String): Reference/source

**AuthorBibref:**
- `author` (String, unique): Author identifier
- `bibref` (String): Bibliographic reference string

---

## License

MIT License