"""Routes parse and delegate; they hold no rules. The request-scoped dependencies
(session, clock) are declared here so the services never see the web framework."""
from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from ..clock import Clock, get_clock
from ..db import get_session

SessionDep = Annotated[Session, Depends(get_session)]
ClockDep = Annotated[Clock, Depends(get_clock)]
