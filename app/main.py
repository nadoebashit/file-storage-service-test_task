from fastapi import FastAPI 
from app.api.routers.auth import router as auth_router

app = FastAPI(title="File Storage Service",vesrion="0.1.0")

app.include_router(auth_router,prefix="/auth",tags=["auth"]) 

@app.get("/",tags["health"])
async def health():
    return {"status":"ok"}