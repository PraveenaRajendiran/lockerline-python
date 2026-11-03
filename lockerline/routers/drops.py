
from fastapi import APIRouter, Response

from ..errors import NoDoorFree, NoSuchFlat
from ..handlers import VALIDATION_RESPONSE, responses
from ..ids import parcel_public
from ..schemas import DropIn, DropOut
from ..services import drops
from ..services.doors import get_tower
from . import ClockDep, SessionDep, SettingsDep


router = APIRouter(prefix="/drops", tags=["drops"])


CREATED = {
    201: {"description": "A door was chosen; the parcel is at the Location given",
          "headers": {"Location": {"schema": {"type": "string"}, "description": "The new parcel, e.g. /parcels/P017"}}}}


@router.post(
    "",
    response_model=DropOut,
    status_code=201,
    summary="Book a door for a parcel",
    responses={
        **CREATED,
        **responses(
            (NoSuchFlat, "Flat '999' does not exist in tower A"),
            (NoDoorFree, "No free L door", {"free_sizes": ["S", "M"]}),
        ),
        **VALIDATION_RESPONSE,
    },
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
