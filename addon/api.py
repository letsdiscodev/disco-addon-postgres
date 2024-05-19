from fastapi import FastAPI
from addon.endpoints import (
    instances,
    databases,
    attachments,
)

app = FastAPI()

app.include_router(instances.router)
app.include_router(databases.router)
app.include_router(attachments.router)
