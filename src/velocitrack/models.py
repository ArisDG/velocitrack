from sqlalchemy import Column, Integer, String, Float
from velocitrack.database import Base


class VelocityModel1D(Base):
    __tablename__ = "velocity_models_1d"

    id = Column(Integer, primary_key=True, index=True)
    depth = Column(Float, nullable=False, index=True)  # Depth in km
    velocity = Column(Float, nullable=False)  # Velocity in km/s
    wave_type = Column(String, nullable=False, index=True)  # VP or VS
    nfo = Column(String, nullable=False, index=True)  # Network/Organization identifier
    author = Column(String, nullable=False, index=True)  # Reference/source


class VelocityModel3D_VP(Base):
    __tablename__ = "velocity_models_3d_vp"

    id = Column(Integer, primary_key=True, index=True)
    longitude = Column(Float, nullable=False, index=True)  # Longitude in degrees
    latitude = Column(Float, nullable=False, index=True)  # Latitude in degrees
    depth = Column(Float, nullable=False, index=True)  # Depth in km
    vp = Column(Float, nullable=False)  # P-wave velocity in km/s
    r = Column(Float)  # R parameter (optional)
    nfo = Column(String, nullable=False, index=True)  # Network/Organization identifier
    author = Column(String, nullable=False, index=True)  # Reference/source


class VelocityModel3D_VS(Base):
    __tablename__ = "velocity_models_3d_vs"

    id = Column(Integer, primary_key=True, index=True)
    longitude = Column(Float, nullable=False, index=True)  # Longitude in degrees
    latitude = Column(Float, nullable=False, index=True)  # Latitude in degrees
    depth = Column(Float, nullable=False, index=True)  # Depth in km
    vs = Column(Float, nullable=False)  # S-wave velocity in km/s
    r = Column(Float)  # R parameter (optional)
    nfo = Column(String, nullable=False, index=True)  # Network/Organization identifier
    author = Column(String, nullable=False, index=True)  # Reference/source
