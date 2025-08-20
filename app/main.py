from fastapi import FastAPI, Depends
from fastapi.staticfiles import StaticFiles

from app.api.v1.api import api_router
from app.core.auth import require_auth
from app.core.database import engine
from app.models import Base
from app.web.admin.auth_routes import router as admin_auth_router  # Add this
from app.web.admin.routes import router as admin_router
from app.web.routes import router as web_router

Base.metadata.create_all(bind=engine)

def create_app() -> FastAPI:
    app = FastAPI(title="Luce di Villa")

    app.mount("/static", StaticFiles(directory="static"), name="static")

    app.include_router(web_router)
    app.include_router(admin_auth_router, prefix="/admin")  # Add this
    app.include_router(admin_router, prefix="/admin", tags=["admin"], dependencies=[Depends(require_auth)])  # Protected
    app.include_router(api_router, prefix="/api/v1", dependencies=[Depends(require_auth)])  # Protected

    return app

app = create_app()

# Usage in any protected route:
# def some_protected_route(session=Depends(require_auth)):
#     user_id = session['user_id']
#     username = session['username']

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
