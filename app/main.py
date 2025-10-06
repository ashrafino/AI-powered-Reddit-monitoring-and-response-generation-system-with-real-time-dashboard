from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import ORJSONResponse
from fastapi.middleware.trustedhost import TrustedHostMiddleware
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration

from app.core.config import settings
from app.api.routers import auth, health
from app.api.routers import clients as clients_router
from app.api.routers import configs as configs_router
from app.api.routers import posts as posts_router
from app.api.routers import analytics as analytics_router
from app.api.routers import users as users_router
from app.api.routers import ops as ops_router
from app.api.routers import websocket as websocket_router
from app.db.base import Base
from app.db.session import engine
from app.middleware.security import add_security_headers

# Initialize Sentry if DSN is provided
if settings.sentry_dsn:
    sentry_sdk.init(
        dsn=settings.sentry_dsn,
        integrations=[
            FastApiIntegration(),
            SqlalchemyIntegration(),
        ],
        traces_sample_rate=0.1,
        environment=settings.app_env,
    )

app = FastAPI(
    title="Reddit Bot SaaS API",
    version="0.1.0",
    default_response_class=ORJSONResponse,
    openapi_url=f"{settings.api_prefix}/openapi.json",
    docs_url=f"{settings.api_prefix}/docs",
    redoc_url=f"{settings.api_prefix}/redoc",
)

# Security middleware
# In production with nginx proxy, requests come from nginx (localhost)
# So we allow localhost + any IP for direct access
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["*"]  # Nginx handles host validation, backend sees nginx as source
)

# CORS middleware with more restrictive settings for production
# In production, requests come through nginx proxy so we allow all origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Nginx handles the actual origin, backend sees nginx
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health.router, prefix=settings.api_prefix, tags=["health"])
app.include_router(auth.router, prefix=settings.api_prefix, tags=["auth"]) 
app.include_router(clients_router.router, prefix=settings.api_prefix, tags=["clients"]) 
app.include_router(configs_router.router, prefix=settings.api_prefix, tags=["configs"]) 
app.include_router(posts_router.router, prefix=settings.api_prefix, tags=["posts"]) 
app.include_router(analytics_router.router, prefix=settings.api_prefix, tags=["analytics"]) 
app.include_router(users_router.router, prefix=settings.api_prefix, tags=["users"]) 
app.include_router(ops_router.router, prefix=settings.api_prefix, tags=["ops"])
app.include_router(websocket_router.router, prefix=settings.api_prefix, tags=["websocket"]) 

@app.get("/")
def root():
    return {"status": "ok", "version": "1.0.0"}

@app.middleware("http")
async def add_security_headers_middleware(request: Request, call_next):
    response = await call_next(request)
    return add_security_headers(response)

@app.on_event("startup")
def on_startup():
    # For initial bootstrap; in production use Alembic migrations
    Base.metadata.create_all(bind=engine)
