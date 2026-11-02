
from fastapi import APIRouter, Response

from ..ids import parcel_public
from ..schemas import DropIn, DropOut
from ..services import drops
from ..services.doors import get_tower
from . import ClockDep, SessionDep, SettingsDep


router = APIRouter(prefix="/drops")


@router.post(
    "",
    response_model=DropOut,
    status_code=201,
)
def create_drop(
    body: DropIn,
    response: Response,
    session: SessionDep,
    clock: ClockDep,
    settings: SettingsDep,
) -> DropOut:
    tower = get_tower(session, "A")

    parcel, door, code = drops.drop(
        session,
        tower,
        body.size_class,
        body.flat,
        clock,
        settings,
    )

    response.headers["Location"] = f"/parcels/{parcel_public(parcel.id)}"

    return DropOut(
        parcel_id=parcel_public(parcel.id),
        door=door.no,
        size_class=parcel.size_class,
        flat=parcel.flat,
        dropped_at=parcel.dropped_at,
        code=code,
        expires_at=parcel.code_expires_at,
    )
