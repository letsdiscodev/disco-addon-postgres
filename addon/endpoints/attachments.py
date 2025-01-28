import logging
from dataclasses import dataclass
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Path
from pydantic import BaseModel, Field

from addon import disco, misc, postgres, storage
from addon.context import get_api_key
from addon.models.db import Session

log = logging.getLogger(__name__)

router = APIRouter()


class AttachDatabaseReqBody(BaseModel):
    project: str = Field(..., pattern=r"^[a-z][a-z0-9\-]*$", max_length=255)
    env_var: str = Field(
        ..., pattern=r"^[a-zA-Z_]+[a-zA-Z0-9_]*$", max_length=255, alias="envVar"
    )


@router.post("/instances/{instance_name}/databases/{db_name}/attach")
def attach_post(
    instance_name: Annotated[str, Path()],
    db_name: Annotated[str, Path()],
    req_body: AttachDatabaseReqBody,
    api_key: Annotated[str, Depends(get_api_key)],
):
    if not disco.project_exists(req_body.project, api_key=api_key):
        raise HTTPException(
            status_code=404, detail=f"Project {req_body.project} not found"
        )
    postgres_project_name = f"postgres-instance-{instance_name}"
    with Session.begin() as dbsession:
        instance = storage.get_instance_by_name(dbsession, instance_name)
        if instance is None:
            raise HTTPException(
                status_code=404, detail=f"Instance {instance_name} not found"
            )
        if db_name not in [database.name for database in instance.databases]:
            raise HTTPException(
                status_code=404,
                detail=f"Database {db_name} not found in {instance_name}",
            )
        existing_conn_str: str | None = None
        for database in instance.databases:
            if database.name != db_name:
                continue
            for user in database.users:
                for attachment in user.attachments:
                    if (
                        attachment.project_name == req_body.project
                        and attachment.env_var == req_body.env_var
                    ):
                        existing_conn_str = misc.conn_string(
                            user=user.name,
                            password=user.password,
                            postgres_project_name=postgres_project_name,
                            db_name=db_name,
                        )
    if existing_conn_str is not None:
        log.info(
            "%s (%s) was already attached to %s as %s, setting env var again",
            db_name,
            instance_name,
            req_body.project,
            req_body.env_var,
        )
        deployment_number = disco.set_conn_str_env_var(
            project_name=req_body.project,
            var_name=req_body.env_var,
            conn_str=existing_conn_str,
            api_key=api_key,
        )
        return {
            "deployment": {"number": deployment_number}
            if deployment_number is not None
            else None
        }
    log.info(
        "Attaching %s (%s) to %s as env var %s",
        db_name,
        instance_name,
        req_body.project,
        req_body.env_var,
    )
    admin_conn_str = storage.get_admin_conn_str(instance_name)
    assert admin_conn_str is not None
    user_name = misc.generate_user_name()
    password = misc.generate_password()
    postgres.add_user(
        admin_conn_str=admin_conn_str,
        db_name=db_name,
        user=user_name,
        password=password,
    )
    storage.add_user(
        instance_name=instance_name,
        db_name=db_name,
        user_name=user_name,
        password=password,
    )
    deployment_number = disco.set_conn_str_env_var(
        project_name=req_body.project,
        var_name=req_body.env_var,
        conn_str=misc.conn_string(
            user=user_name,
            password=password,
            postgres_project_name=postgres_project_name,
            db_name=db_name,
        ),
        api_key=api_key,
    )
    storage.add_attachment(
        instance_name=instance_name,
        db_name=db_name,
        user_name=user_name,
        project_name=req_body.project,
        var_name=req_body.env_var,
    )
    return {
        "deployment": {"number": deployment_number}
        if deployment_number is not None
        else None
    }


class DetachDatabaseReqBody(BaseModel):
    project: str = Field(..., pattern=r"^[a-z][a-z0-9\-]*$", max_length=255)
    env_var: str | None = Field(
        None, pattern=r"^[a-zA-Z_]+[a-zA-Z0-9_]*$", max_length=255, alias="envVar"
    )


@dataclass
class AttachmentInfo:
    env_var: str
    user: str
    password: str


@router.post("/instances/{instance_name}/databases/{db_name}/detach")
def detach_post(
    instance_name: Annotated[str, Path()],
    db_name: Annotated[str, Path()],
    req_body: DetachDatabaseReqBody,
    api_key: Annotated[str, Depends(get_api_key)],
):
    postgres_project_name = f"postgres-instance-{instance_name}"
    if not disco.project_exists(req_body.project, api_key=api_key):
        raise HTTPException(
            status_code=404, detail=f"Project {req_body.project} not found"
        )
    with Session.begin() as dbsession:
        instance = storage.get_instance_by_name(dbsession, instance_name)
        if instance is None:
            raise HTTPException(
                status_code=404, detail=f"Instance {instance_name} not found"
            )
        if db_name not in [database.name for database in instance.databases]:
            raise HTTPException(
                status_code=404,
                detail=f"Database {db_name} not found in {instance_name}",
            )
        attachments = storage.get_attachments(
            dbsession=dbsession,
            instance_name=instance_name,
            db_name=db_name,
            project_name=req_body.project,
            env_var=req_body.env_var,
        )
        attachments_info = [
            AttachmentInfo(
                env_var=attachment.env_var,
                user=attachment.user.name,
                password=attachment.user.password,
            )
            for attachment in attachments
        ]
    deployment_number = None
    for attachment_info in attachments_info:
        log.info(
            "Detaching %s (%s) from %s as %s",
            db_name,
            instance_name,
            req_body.project,
            attachment_info.env_var,
        )
        existing_env_var_value = disco.get_conn_str_env_var(
            project_name=req_body.project,
            var_name=attachment_info.env_var,
            api_key=api_key,
        )
        expected_conn_str = misc.conn_string(
            user=attachment_info.user,
            password=attachment_info.password,
            postgres_project_name=postgres_project_name,
            db_name=db_name,
        )
        if existing_env_var_value == expected_conn_str:
            deployment_number = disco.unset_conn_str_env_var(
                project_name=req_body.project,
                var_name=attachment_info.env_var,
                api_key=api_key,
            )
        admin_conn_str = storage.get_admin_conn_str(instance_name)
        assert admin_conn_str is not None
        postgres.remove_user(
            admin_conn_str=admin_conn_str,
            db_name=db_name,
            user=attachment_info.user,
        )
        storage.remove_user(
            instance_name=instance_name,
            db_name=db_name,
            user_name=attachment_info.user,
        )
    return {
        "deployment": {"number": deployment_number}
        if deployment_number is not None
        else None
    }
