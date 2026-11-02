
from fastapi import APIRouter

from ..schemas import PickupIn
from ..services import pickups
from . import ClockDep, SessionDep, SettingsDep


router = APIRouter(prefix="/pickups")


@router.post(
    "",
)
def create_pickup(
    body: PickupIn,
    session: SessionDep,
    clock: ClockDep,
    settings: SettingsDep,
) -> None:
    pickups.pickup(
        session,
        body.code,
        clock,
        settings,
    )
