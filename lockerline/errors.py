
"""
Domain refusals and the problem types every error body uses.

The class attributes below are the single source of truth for status, type and title. Services raise these; the one
handler in handlers.py maps them. This module imports nothing from FastAPI or Starlette, so the services that raise
these exceptions stay free of the web framework.
"""

PROBLEM = "application/problem+json"


class DomainError(Exception):

    status: int = 400
    type: str = "/errors/domain"
    title: str = "Refused"

    def __init__(self, detail: str, **extra):
        super().__init__(detail)
        self.detail = detail
        self.extra = extra


class NoSuchTower(DomainError):
    status, type, title = 404, "/errors/no-such-tower", "No such tower"


class NoSuchDoor(DomainError):
    status, type, title = 404, "/errors/no-such-door", "No such door"


class NoSuchParcel(DomainError):
    status, type, title = 404, "/errors/no-such-parcel", "No such parcel"


class NoSuchFlat(DomainError):
    status, type, title = 400, "/errors/no-such-flat", "No such flat in this tower"


class NoDoorFree(DomainError):
    status, type, title = 409, "/errors/no-door-free", "No free door of that size"


class NoSuchCode(DomainError):
    status, type, title = 404, "/errors/no-such-code", "No such code"


class CodeExpired(DomainError):
    status, type, title = 404, "/errors/code-expired", "This code has expired"


class CodeUsed(DomainError):
    status, type, title = 409, "/errors/code-used", "This code has already opened its door"


# (status, type, title) of the errors that are not domain refusals

VALIDATION_BODY = (
    422, "/errors/validation", "The request body is not valid"
)  # a body that fails validation

VALIDATION_PARAMS = (
    400, "/errors/validation", "Invalid query parameter"
)  # an unknown filter value

INTERNAL = (500, "/errors/internal", "Something went wrong")

NOT_FOUND = (
    404, "/errors/not-found", "No such resource"
)  # no route at this path

METHOD_NOT_ALLOWED = (405, "/errors/method-not-allowed", "Method not allowed")

HTTP = "/errors/http"
