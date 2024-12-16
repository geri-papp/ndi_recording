from fastapi import FastAPI

from .api import router as api_router
from .core.utils.custom_unique_id import custom_generate_unique_id

app = FastAPI(
    generate_unique_id_function=custom_generate_unique_id,
    title="OXCAM",
    version="v0.2.0",
    contact={"name": "OX-IT", "email": "viktor.koch@oxit.hu"},
)
app.include_router(api_router)
