from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Path
from pydantic import BaseModel, Field

from addon import config, disco, misc, storage
from addon.context import get_api_key
from addon.models.db import Session

router = APIRouter()


@router.get("/instances")
def instances_get():
    with Session.begin() as dbsession:
        instances = storage.get_instances(dbsession)
        return {
            "instances": [
                {
                    "created": instance.created.isoformat(),
                    "name": instance.name,
                    "image": instance.image,
                    "version": instance.version,
                }
                for instance in instances
            ]
        }


class AddInstanceReqBody(BaseModel):
    image: str | None = Field(None, pattern=r"^[^\s:]+$", max_length=255)
    version: str | None = Field(None, pattern=r"^[^\s:]+$", max_length=128)


@router.post("/instances", status_code=201)
def instances_post(
    req_body: AddInstanceReqBody,
    api_key: Annotated[str, Depends(get_api_key)],
):
    if req_body.image is None:
        image = config.POSTGRES_IMAGE
    else:
        image = req_body.image
    if req_body.version is None:
        version = config.POSTGRES_VERSION
    else:
        version = req_body.version
    postgres_project_name = disco.create_postgres_project(api_key=api_key)
    instance_name = misc.instance_name_from_project_name(postgres_project_name)
    admin_user = misc.generate_user_name()
    admin_password = misc.generate_password()
    storage.add_postgres_instance(
        instance_name=instance_name,
        image=image,
        version=version,
        admin_user=admin_user,
        admin_password=admin_password,
    )
    disco.init_postgres_env_variables(
        postgres_project_name=postgres_project_name,
        admin_user=admin_user,
        admin_password=admin_password,
        api_key=api_key,
    )
    deployment_number = disco.deploy_postgres_project(
        postgres_project_name=postgres_project_name,
        image=image,
        version=version,
        api_key=api_key,
    )
    return {
        "instance": {
            "name": instance_name,
        },
        "project": {
            "name": postgres_project_name,
        },
        "deployment": {
            "number": deployment_number,
        },
    }


@router.delete("/instances/{instance_name}", status_code=200)
def instance_delete(
    instance_name: Annotated[str, Path()],
    api_key: Annotated[str, Depends(get_api_key)],
):
    with Session.begin() as dbsession:
        instance = storage.get_instance_by_name(dbsession, instance_name)
        if instance is None:
            raise HTTPException(
                status_code=404, detail=f"Instance {instance_name} not found"
            )
        attachments = storage.get_attachments_for_instance(dbsession, instance)
        if len(attachments) > 0:
            usage = [
                {"project": attachment.project_name, "envVar": attachment.env_var}
                for attachment in attachments
            ]
            raise HTTPException(422, f"Instance {instance_name} still in use: {usage}")
    postgres_project_name = misc.instance_project_name(instance_name)
    if disco.project_exists(postgres_project_name, api_key=api_key):
        disco.remove_project(postgres_project_name, api_key=api_key)
    storage.remove_postgres_instance(instance_name)
    return {}
