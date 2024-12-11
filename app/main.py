from fastapi import FastAPI

from .api import router as api_router
from .core.utils.custom_unique_id import custom_generate_unique_id

app = FastAPI(generate_unique_id_function=custom_generate_unique_id)
app.include_router(api_router)
