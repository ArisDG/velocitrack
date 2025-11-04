from pydantic import BaseModel
from typing import Optional, Literal


class VelocityModel1DBase(BaseModel):
    depth: float
    velocity: float
    wave_type: Literal["VP", "VS"]
    nfo: str
    author: str


class VelocityModel1DCreate(VelocityModel1DBase):
    pass


class VelocityModel1D(VelocityModel1DBase):
    id: int

    class Config:
        from_attributes = True


class VelocityModel3DBase(BaseModel):
    latitude: float
    longitude: float
    depth: float
    velocity_p: Optional[float] = None
    velocity_s: Optional[float] = None
    nfo: str
    author: str


class VelocityModel3DCreate(VelocityModel3DBase):
    pass


class VelocityModel3D(VelocityModel3DBase):
    id: int

    class Config:
        from_attributes = True
