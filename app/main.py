from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routers.claims import router as claims_router

app = FastAPI()

allow_origins = settings.allow_origins
if allow_origins == ["*"]:
    cors_origins = ["*"]
else:
    cors_origins = [origin.strip() for origin in allow_origins if origin.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(claims_router)


@app.get("/health")
async def health():
    return {"status": "ok"}
