"""
Data Import Script for VelociTrack

This script imports velocity model data into the database.
"""

import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "src"))

from sqlalchemy.orm import sessionmaker
from velocitrack.database import engine
from velocitrack.models import (
    Base,
    VelocityModel1D,
    VelocityModel3D_VP,
    VelocityModel3D_VS,
    AuthorBibref,
)

# Create tables if they don't exist
print("Creating database tables if they don't exist...")
Base.metadata.create_all(bind=engine)
print("Database tables ready.")

# Create a session
Session = sessionmaker(bind=engine)
session = Session()


def import_1d_from_file(filepath: str):
    """Import 1D velocity data from a file"""
    try:
        import pandas as pd

        # Try to read as CSV or Excel
        if filepath.endswith(".csv"):
            df = pd.read_csv(filepath)
        elif filepath.endswith((".xlsx", ".xls")):
            df = pd.read_excel(filepath)
        else:
            print(f"Unsupported file format: {filepath}")
            return False

        # Expected columns for 1D models: Depth (km), Velocity (km/s), Type, NFO, Author
        required_columns = ["Depth (km)", "Velocity (km/s)", "Type", "NFO", "Author"]

        # Check if all required columns exist
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            print(f"Missing required columns: {missing_columns}")
            print(f"Available columns: {list(df.columns)}")
            return False

        imported_count = 0
        skipped_count = 0
        for _, row in df.iterrows():
            depth = float(row["Depth (km)"])
            velocity = float(row["Velocity (km/s)"])
            wave_type = str(row["Type"]).strip().upper()
            nfo = str(row["NFO"]).strip()
            author = str(row["Author"]).strip()

            # Check if this record already exists
            existing = (
                session.query(VelocityModel1D)
                .filter_by(
                    depth=depth,
                    velocity=velocity,
                    wave_type=wave_type,
                    nfo=nfo,
                    author=author,
                )
                .first()
            )

            if existing:
                skipped_count += 1
                continue  # Skip this record as it already exists

            velocity_model = VelocityModel1D(
                depth=depth,
                velocity=velocity,
                wave_type=wave_type,
                nfo=nfo,
                author=author,
            )
            session.add(velocity_model)
            imported_count += 1

        session.commit()
        print(
            f"Successfully imported {imported_count} 1D velocity model records from {filepath}."
        )
        if skipped_count > 0:
            print(f"Skipped {skipped_count} duplicate records.")
        return True

    except Exception as e:
        session.rollback()
        print(f"Error importing 1D data from file: {e}")
        return False
    finally:
        session.close()


def import_3d_from_file(filepath: str, wave_type: str):
    """Import 3D velocity data from a file for VP or VS"""
    try:
        import pandas as pd

        # Validate wave_type
        if wave_type.upper() not in ["VP", "VS"]:
            print(f"Invalid wave type: {wave_type}. Must be 'VP' or 'VS'")
            return False

        wave_type = wave_type.upper()

        # Try to read as CSV or Excel
        if filepath.endswith(".csv"):
            df = pd.read_csv(filepath)
        elif filepath.endswith((".xlsx", ".xls")):
            df = pd.read_excel(filepath)
        else:
            print(f"Unsupported file format: {filepath}")
            return False

        # Expected columns for 3D models: Longitude, Latitude, Depth, Vp/Vs, R, NFO, Author
        if wave_type == "VP":
            required_columns = ["Longitude", "Latitude", "Depth", "Vp", "NFO", "Author"]
            velocity_column = "Vp"
            model_class = VelocityModel3D_VP
        else:
            required_columns = ["Longitude", "Latitude", "Depth", "Vs", "NFO", "Author"]
            velocity_column = "Vs"
            model_class = VelocityModel3D_VS

        optional_columns = ["R"]

        # Check if all required columns exist
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            print(f"Missing required columns: {missing_columns}")
            print(f"Available columns: {list(df.columns)}")
            print(f"Required: {required_columns}")
            print(f"Optional: {optional_columns}")
            return False

        imported_count = 0
        skipped_count = 0
        for _, row in df.iterrows():
            # Extract values
            longitude = float(row["Longitude"])
            latitude = float(row["Latitude"])
            depth = float(row["Depth"])
            velocity = float(row[velocity_column])
            nfo = str(row["NFO"]).strip()
            author = str(row["Author"]).strip()

            # Handle optional R column - default to 1 if not provided
            r_value = 1.0  # Default value
            if "R" in df.columns and pd.notna(row["R"]):
                r_value = float(row["R"])

            # Check if this record already exists
            if wave_type == "VP":
                existing = (
                    session.query(model_class)
                    .filter_by(
                        longitude=longitude,
                        latitude=latitude,
                        depth=depth,
                        vp=velocity,
                        nfo=nfo,
                        author=author,
                    )
                    .first()
                )
            else:  # VS
                existing = (
                    session.query(model_class)
                    .filter_by(
                        longitude=longitude,
                        latitude=latitude,
                        depth=depth,
                        vs=velocity,
                        nfo=nfo,
                        author=author,
                    )
                    .first()
                )

            if existing:
                skipped_count += 1
                continue  # Skip this record as it already exists

            if wave_type == "VP":
                velocity_model = model_class(
                    longitude=longitude,
                    latitude=latitude,
                    depth=depth,
                    vp=velocity,
                    r=r_value,
                    nfo=nfo,
                    author=author,
                )
            else:  # VS
                velocity_model = model_class(
                    longitude=longitude,
                    latitude=latitude,
                    depth=depth,
                    vs=velocity,
                    r=r_value,
                    nfo=nfo,
                    author=author,
                )

            session.add(velocity_model)
            imported_count += 1

        session.commit()
        print(
            f"Successfully imported {imported_count} 3D {wave_type} velocity model records from {filepath}."
        )
        if skipped_count > 0:
            print(f"Skipped {skipped_count} duplicate records.")
        return True

    except Exception as e:
        session.rollback()
        print(f"Error importing 3D {wave_type} data from file: {e}")
        return False
    finally:
        session.close()


def import_bibrefs_from_file(filepath: str):
    """Import author-bibref mappings from a file"""
    try:
        import pandas as pd

        # Try to read as CSV or Excel
        if filepath.endswith(".csv"):
            df = pd.read_csv(filepath)
        elif filepath.endswith((".xlsx", ".xls")):
            df = pd.read_excel(filepath)
        else:
            print(f"Unsupported file format: {filepath}")
            return False

        # Expected columns: Author, Bibref
        required_columns = ["Author", "Bibref"]

        # Check if all required columns exist
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            print(f"Missing required columns: {missing_columns}")
            print(f"Available columns: {list(df.columns)}")
            return False

        imported_count = 0
        updated_count = 0
        for _, row in df.iterrows():
            author = str(row["Author"]).strip()
            bibref = str(row["Bibref"]).strip()

            # Check if this author already exists
            existing = (
                session.query(AuthorBibref)
                .filter_by(author=author)
                .first()
            )

            if existing:
                # Update the bibref if it's different
                if existing.bibref != bibref:
                    existing.bibref = bibref
                    updated_count += 1
                continue

            author_bibref = AuthorBibref(
                author=author,
                bibref=bibref,
            )
            session.add(author_bibref)
            imported_count += 1

        session.commit()
        print(
            f"Successfully imported {imported_count} author-bibref records from {filepath}."
        )
        if updated_count > 0:
            print(f"Updated {updated_count} existing records.")
        return True

    except Exception as e:
        session.rollback()
        print(f"Error importing bibref data from file: {e}")
        return False
    finally:
        session.close()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python import_data.py <model_type> <filepath> [wave_type]")
        print("Model types: 1d, 3d, bibref")
        print("Wave type (for 3d only): vp, vs")
        print("Supported formats: CSV (.csv), Excel (.xlsx, .xls)")
        print()
        print(
            "1D model required columns: Depth (km), Velocity (km/s), Type, NFO, Author"
        )
        print(
            "3D VP model required columns: Longitude, Latitude, Depth, Vp, NFO, Author"
        )
        print(
            "3D VS model required columns: Longitude, Latitude, Depth, Vs, NFO, Author"
        )
        print("3D model optional columns: R")
        print("Bibref model required columns: Author, Bibref")
        print()
        print("Examples:")
        print("  python import_data.py 1d data.xlsx")
        print("  python import_data.py 3d data.xlsx vp")
        print("  python import_data.py 3d data.xlsx vs")
        print("  python import_data.py bibref bibrefs.csv")
        sys.exit(1)

    if len(sys.argv) < 3:
        print("Error: Both model type and filepath are required")
        print("Usage: python import_data.py <model_type> <filepath> [wave_type]")
        sys.exit(1)

    model_type = sys.argv[1].lower()
    filepath = sys.argv[2]

    if not os.path.exists(filepath):
        print(f"File not found: {filepath}")
        sys.exit(1)

    if model_type == "1d":
        success = import_1d_from_file(filepath)
    elif model_type == "3d":
        if len(sys.argv) < 4:
            print("Error: Wave type (vp or vs) is required for 3D models")
            print("Usage: python import_data.py 3d <filepath> <wave_type>")
            sys.exit(1)

        wave_type = sys.argv[3].lower()
        success = import_3d_from_file(filepath, wave_type)
    elif model_type == "bibref":
        success = import_bibrefs_from_file(filepath)
    else:
        print(f"Invalid model type: {model_type}")
        print("Valid model types: 1d, 3d, bibref")
        sys.exit(1)

    if success:
        print("Import completed successfully.")
    else:
        print("Import failed.")
        sys.exit(1)
