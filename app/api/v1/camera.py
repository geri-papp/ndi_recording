from fastapi import APIRouter

router = APIRouter(prefix="/camera", tags=["Camera"])

@router.get("/status")
async def get_camera_status():
    raise NotImplementedError("Getting camera status is not implemented yet.")


@router.post("/start")
async def start_camera():
    raise NotImplementedError("Starting camera is not implemented yet.")


@router.post("/stop")
async def stop_camera():
    raise NotImplementedError("Stopping camera is not implemented yet.")


@router.post("/restart")
async def restart_camera():
    raise NotImplementedError("Restarting camera is not implemented yet.")



