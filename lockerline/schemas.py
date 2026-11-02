
"""
Request and response models. Every response goes through one of these; bodies use Field constraints.
Optional fields are left out of the body when they have no value (the routes use response_model_exclude_none).
"""

from datetime import datetime, timezone
from typing import Annotated, Literal

from pydantic import BaseModel, Field, PlainSerializer


SizeClass = Literal["S", "M", "L"]
DoorState = Literal["free", "holding"]


def _iso_z(dt: datetime) -> str:
    """SQLite hands naive datetimes back; everything the app stores is UTC, so a naive value is UTC, never local time."""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


UtcZ = Annotated[
    datetime,
    PlainSerializer(_iso_z, return_type=str),
]


class DoorListItem(BaseModel):
    """One cell of the wall. A free door carries only no, size and state; a holding door adds its parcel and dwell."""
    no: str
    size: SizeClass
    state: DoorState
    parcel_id: str | None = None
    dwell_seconds: int | None = None


class DoorOut(DoorListItem):
    """One door, read on its own: a holding door also names the flat its parcel is for."""
    flat: str | None = None


class DoorsOut(BaseModel):
    tower: str
    free: int = Field(
        ...,
        description="How many of the doors in this answer (after the filters) are free",
    )
    doors: list[DoorListItem]


class DropIn(BaseModel):
    size_class: SizeClass
    flat: str = Field(
        min_length=1,
        max_length=8,
        pattern=r"^[0-9A-Za-z-]+$",
    )


class DropOut(BaseModel):
    parcel_id: str
    door: str
    size_class: SizeClass
    flat: str
    dropped_at: UtcZ
    code: str = Field(description="Shown once, to the courier")
    expires_at: UtcZ


class PickupIn(BaseModel):
    code: str = Field(
        pattern=r"^\d{6}$",
    )


class ParcelOut(BaseModel):
    parcel_id: str
    state: Literal["holding", "collected"]
    door: str
    size_class: SizeClass
    flat: str
    dropped_at: UtcZ
