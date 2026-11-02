
from fastapi import APIRouter

from ..ids import parcel_public
from ..schemas import PickupIn, PickupOut
from ..services import pickups
from . import ClockDep, SessionDep, SettingsDep


router = APIRouter(prefix="/pickups")


@router.post(
    "",
    response_model=PickupOut,
)
def create_pickup(
    body: PickupIn,
    session: SessionDep,
    clock: ClockDep,
    settings: SettingsDep,
) -> PickupOut:
    parcel, door = pickups.pickup(
        session,
        body.code,
        clock,
        settings,
    )

    return PickupOut(
        parcel_id=parcel_public(parcel.id),
        door=door.no,
        opened_at=parcel.collected_at,
        dwell_seconds=parcel.dwell_seconds,
    )
