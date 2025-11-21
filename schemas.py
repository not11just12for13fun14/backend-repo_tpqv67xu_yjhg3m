"""
Database Schemas for TrenchSight

Each Pydantic model below represents a MongoDB collection. The collection name
is the lowercase of the class name (e.g., PhotoSession -> "photosession").
"""
from typing import Optional, List
from pydantic import BaseModel, Field
from datetime import datetime


class PhotoSession(BaseModel):
    site_name: str = Field(..., description="Name of the trench site")
    date: str = Field(..., description="Session date in YYYY-MM-DD")
    start_lat: float = Field(..., description="Start latitude")
    start_lng: float = Field(..., description="Start longitude")
    device: Optional[str] = Field(None, description="User agent/device info")
    battery_level: Optional[float] = Field(None, ge=0, le=1, description="Battery level 0..1")
    created_at: Optional[datetime] = None


class Photo(BaseModel):
    session_id: str = Field(..., description="Associated PhotoSession ID")
    seq: int = Field(..., ge=1, description="Sequence number of the photo")
    lat: float = Field(..., description="Latitude of capture")
    lng: float = Field(..., description="Longitude of capture")
    tilt_deg: Optional[float] = Field(None, description="Device tilt/pitch in degrees")
    heading_deg: Optional[float] = Field(None, description="Device azimuth/heading in degrees")
    zoom: Optional[float] = Field(1.0, description="Camera zoom level if available")
    filename: str = Field(..., description="Stored file name")
    captured_at: datetime = Field(default_factory=datetime.utcnow)
