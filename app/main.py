from fastapi import FastAPI
from fastapi_pagination import add_pagination
from app.api.routers.auth import router as auth_router
from app.api.routers.files import router as files_router

app = FastAPI(title="File Storage Service", version="0.2.0")
app.include_router(auth_router, prefix="/auth", tags=["auth"])
app.include_router(files_router, prefix="/files", tags=["files"])

@app.get("/", tags=["health"])
async def health():
    return {"status": "ok"}

add_pagination(app)
