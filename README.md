# VelociTrack

A FastAPI + PostgreSQL system for managing and querying velocity models, similar to seismotrack but for velocity data.

## Features

- **1D Velocity Models**: Store and query 1D velocity models with depth-velocity relationships
- **3D Velocity Models**: Store and query separate VP and VS 3D velocity models with geographical coordinates
- **RESTful API**: FastAPI-based web service with automatic documentation at `/docs`
- **PostgreSQL Backend**: Reliable database storage for velocity data
- **Data Import**: Tools for importing velocity model data from CSV/Excel files
- **Duplicate Prevention**: Automatic duplicate detection during data import
- **Multiple Output Formats**: VELEST format for 1D models, tab-delimited for 3D models
- **Discovery Endpoints**: Query unique authors and NFOs across all models

## Installation

```bash
# Create and activate virtual environment
python -m venv ~/path/to/velocitrack
source ~/path/to/velocitrack/bin/activate

# Install dependencies
pip install -e .
```

## Configuration

Create a `.env` file with your database configuration:

```
DATABASE_URL=postgresql://postgres:password@localhost/velocitycatalogues
```

## Usage

### Start the server

```bash
source ~/path/to/velocitrack/bin/activate
cd src
python run_server.py
```

The server will start on `http://localhost:8001` with automatic API documentation at `http://localhost:8001/docs`.

### API Endpoints

#### Main Query Endpoints
- `GET /`: Service information and version
- `GET /1d/?author={author}&nfo={nfo}`: Query 1D velocity models (VELEST format)
- `GET /3d/?wave_type={VP|VS}&author={author}&include_r={true|false}`: Query 3D velocity models (tab-delimited)

#### Discovery Endpoints
- `GET /authors`: List all unique authors across all velocity model tables
- `GET /nfos`: List all unique NFO identifiers across all velocity model tables

### Example Queries

```bash
# Get all unique authors
curl http://localhost:8001/authors

# Get all unique NFOs
curl http://localhost:8001/nfos

# Query 1D model by author and NFO (returns VELEST format)
curl "http://localhost:8001/1d/?author=test_author&nfo=test_nfo"

# Query 3D VP model by author (returns tab-delimited format)
curl "http://localhost:8001/3d/?wave_type=VP&author=test_author&nfo=test_nfo"

# Query 3D VS model without R column
curl "http://localhost:8001/3d/?wave_type=VS&author=test_author&nfo=test_nfo&include_r=false"
```

## Data Models

### 1D Velocity Models (`VelocityModel1D`)
- **Depth (km)**: Depth in kilometers
- **Velocity (km/s)**: Velocity in km/s
- **Type**: Wave type (VP for P-wave, VS for S-wave)
- **NFO**: Network/Organization identifier
- **Author**: Reference/source of the model

### 3D Velocity Models (`VelocityModel3D_VP` / `VelocityModel3D_VS`)
- **Longitude**: Geographic longitude
- **Latitude**: Geographic latitude  
- **Depth (km)**: Depth in kilometers
- **Velocity (km/s)**: VP or VS velocity in km/s
- **R**: Optional R parameter (defaults to 1.0)
- **NFO**: Network/Organization identifier
- **Author**: Reference/source of the model

## Output Formats

### 1D Models (VELEST Format)
```
test_author model - test_nfo
 8        vel,depth,vdamp,phase (f5.2,5x,f7.2,2x,f7.3,3x,a1)
 4.80       -3.00   001.000           P-VELOCITY MODEL
 4.80        0.00   001.000
 5.20        4.00   001.000
 ...
 8
 2.67       -3.00   001.000           S-VELOCITY MODEL
 2.67        0.00   001.000
 ...
```

### 3D Models (Tab-Delimited Format)
```
test_author model - test_nfo
Longitude    Latitude    Depth    Vp    R
21.4    38.04    0.0    4.758679    1.0
21.4    38.04    2.0    4.73316    1.0
...
```

## Data Import

### Import 1D Data
```bash
cd scripts
python import_data.py 1d ../data/sample_1d.csv
```

### Import 3D Data
```bash
cd scripts
# Import VP data
python import_data.py 3d ../data/sample_3d_vp.csv vp

# Import VS data  
python import_data.py 3d ../data/sample_3d_vs.csv vs
```

### Import Command Format
```bash
python import_data.py {1d|3d} <filepath> [vp|vs]
```

- For 1D: `python import_data.py 1d <csv_file>`
- For 3D: `python import_data.py 3d <csv_file> {vp|vs}`

### Data File Formats

#### 1D CSV Format
```csv
Depth (km),Velocity (km/s),Type,NFO,Author
-3.0,4.80,VP,test_nfo,test_author
0.0,4.80,VP,test_nfo,test_author
...
```

#### 3D CSV Format
```csv
Longitude,Latitude,Depth,Velocity,R,NFO,Author
21.4,38.04,0.0,4.758679,1.0,test_nfo,test_author
21.4,38.04,2.0,4.73316,1.0,test_nfo,test_author
...
```

## Features

- **Duplicate Detection**: Import script automatically prevents duplicate entries
- **Smart R Column**: 3D endpoint only shows R column if non-default values exist or explicitly requested
- **VELEST Compatibility**: 1D output matches exact VELEST format specifications
- **Author/NFO Headers**: Both 1D and 3D outputs include model attribution headers
- **Flexible Filtering**: Partial matching on author and NFO parameters
- **Automatic Documentation**: Interactive API docs available at `/docs`

## Development

### Database Schema
- Three separate tables: `velocity_model_1d`, `velocity_model_3d_vp`, `velocity_model_3d_vs`
- Automatic table creation on first run
- PostgreSQL with SQLAlchemy ORM

## License

MIT License