import logging

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from addon import storage
from addon.models.db import Session

log = logging.getLogger(__name__)

router = APIRouter()


class CreateTunnelReqBody(BaseModel):
    project: str = Field(..., pattern=r"^[a-z][a-z0-9\-]*$", max_length=255)
    env_var: str = Field(
        None, pattern=r"^[a-zA-Z_]+[a-zA-Z0-9_]*$", max_length=255, alias="envVar"
    )


@router.post("/tunnels")
def tunnels_post(
    req_body: CreateTunnelReqBody,
):
    with Session.begin() as dbsession:
        attachments = storage.get_attachments_for_project(
            dbsession=dbsession, project_name=req_body.project, env_var=req_body.env_var
        )
        db_names = set([attachment.user.database.name for attachment in attachments])
        if len(db_names) == 0:
            raise HTTPException(status_code=404, detail="Database not found.")
        if len(db_names) > 1:
            raise HTTPException(
                status_code=422,
                detail="More than one database found. Please specify env variable to use.",
            )
        attachment = attachments[0]
        return {
            "dbInfo": {
                "instance": attachment.user.database.instance.name,
                "database": attachment.user.database.name,
                "user": attachment.user.name,
                "password": attachment.user.password,
            }
        }
