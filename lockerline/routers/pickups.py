
from fastapi import APIRouter

from ..errors import CodeExpired, CodeUsed, NoSuchCode
from ..handlers import VALIDATION_RESPONSE, responses
from ..ids import parcel_public
from ..schemas import PickupIn, PickupOut
from ..services import pickups
from . import ClockDep, SessionDep, SettingsDep


router = APIRouter(prefix="/pickups", tags=["pickups"])


@router.post(
    "",
    response_model=PickupOut,
    summary="Open a door with a pickup code",
    responses={
        **responses(
            (CodeUsed, "That code has already opened its door"),
            (NoSuchCode, "That code does not exist in this tower"),
            (CodeExpired, "That code's window has passed"),
        ),
        **VALIDATION_RESPONSE,
    },
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
