from fastapi import APIRouter, Request

from ...schemas.version import VersionSchema

router = APIRouter(prefix="/version", tags=["Version"])


@router.get("", response_model=VersionSchema)
def get_version(request: Request):
    return VersionSchema(version=request.app.version)
