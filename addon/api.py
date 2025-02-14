from fastapi import FastAPI

from addon.endpoints import (
    addon,
    attachments,
    databases,
    instances,
    tunnels,
)

app = FastAPI()

app.include_router(addon.router)
app.include_router(instances.router)
app.include_router(databases.router)
app.include_router(attachments.router)
app.include_router(tunnels.router)
