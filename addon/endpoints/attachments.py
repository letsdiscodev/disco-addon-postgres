from addon import disco, misc, postgres, storage
from fastapi import APIRouter, Path, HTTPException
from pydantic import BaseModel, Field
from typing import Annotated
import logging

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
):
    postgres_project_name = f"postgres-instance-{instance_name}"
    instance = storage.get_instance(postgres_project_name)
    if instance is None:
        raise HTTPException(
            status_code=404, detail=f"Instance {instance_name} not found"
        )
    if db_name not in instance["databases"]:
        raise HTTPException(
            status_code=404, detail=f"Database {db_name} not found in {instance_name}"
        )
    if not disco.project_exists(req_body.project):
        raise HTTPException(
            status_code=404, detail=f"Project {req_body.project} not found"
        )
    for db_name_, db_info in instance["databases"].items():
        if db_name != db_name_:
            continue
        for user_info in db_info["users"].values():
            for attachment in user_info["attachments"]:
                if (
                    attachment["project"] == req_body.project
                    and attachment["var"] == req_body.env_var
                ):
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
                        conn_str=misc.conn_string(
                            user=user_info["user"],
                            password=user_info["password"],
                            postgres_project_name=postgres_project_name,
                            db_name=db_name,
                        ),
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
    admin_conn_str = storage.get_admin_conn_str(
        postgres_project_name=postgres_project_name,
    )
    assert admin_conn_str is not None
    user = misc.generate_user_name()
    password = misc.generate_password()
    postgres.add_user(
        admin_conn_str=admin_conn_str,
        db_name=db_name,
        user=user,
        password=password,
    )
    storage.add_user(
        postgres_project_name=postgres_project_name,
        db_name=db_name,
        user=user,
        password=password,
    )
    deployment_number = disco.set_conn_str_env_var(
        project_name=req_body.project,
        var_name=req_body.env_var,
        conn_str=misc.conn_string(
            user=user,
            password=password,
            postgres_project_name=postgres_project_name,
            db_name=db_name,
        ),
    )
    storage.add_env_var(
        postgres_project_name=postgres_project_name,
        db_name=db_name,
        user=user,
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
    env_var: str = Field(
        None, pattern=r"^[a-zA-Z_]+[a-zA-Z0-9_]*$", max_length=255, alias="envVar"
    )


@router.post("/instances/{instance_name}/databases/{db_name}/detach")
def detach_post(
    instance_name: Annotated[str, Path()],
    db_name: Annotated[str, Path()],
    req_body: DetachDatabaseReqBody,
):
    postgres_project_name = f"postgres-instance-{instance_name}"
    instance = storage.get_instance(postgres_project_name)
    if instance is None:
        raise HTTPException(
            status_code=404, detail=f"Instance {instance_name} not found"
        )
    if db_name not in instance["databases"]:
        raise HTTPException(
            status_code=404, detail=f"Database {db_name} not found in {instance_name}"
        )
    if not disco.project_exists(req_body.project):
        raise HTTPException(
            status_code=404, detail=f"Project {req_body.project} not found"
        )
    for db_name_, db_info in instance["databases"].items():
        if db_name != db_name_:
            continue
        for user_info in db_info["users"].values():
            for attachment in user_info["attachments"]:
                if attachment["project"] == req_body.project and (
                    attachment["var"] == req_body.env_var or req_body.env_var is None
                ):
                    log.info(
                        "Detaching %s (%s) from %s as %s",
                        db_name,
                        instance_name,
                        req_body.project,
                        attachment["var"],
                    )
                    existing_env_var_value = disco.get_conn_str_env_var(
                        project_name=req_body.project, var_name=attachment["var"]
                    )
                    expected_conn_str = misc.conn_string(
                        user=user_info["user"],
                        password=user_info["password"],
                        postgres_project_name=postgres_project_name,
                        db_name=db_name,
                    )
                    if existing_env_var_value == expected_conn_str:
                        deployment_number = disco.unset_conn_str_env_var(
                            project_name=req_body.project, var_name=attachment["var"]
                        )
                    else:
                        deployment_number = None
                    admin_conn_str = storage.get_admin_conn_str(
                        postgres_project_name=postgres_project_name,
                    )
                    assert admin_conn_str is not None
                    postgres.remove_user(
                        admin_conn_str=admin_conn_str,
                        db_name=db_name,
                        user=user_info["user"],
                    )
                    storage.remove_user(
                        postgres_project_name=postgres_project_name,
                        db_name=db_name,
                        user=user_info["user"],
                    )
                    return {
                        "deployment": {"number": deployment_number}
                        if deployment_number is not None
                        else None
                    }
    raise HTTPException(status_code=404, detail="Couldn't find attached database user")
