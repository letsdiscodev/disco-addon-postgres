from typing import Annotated
from fastapi import APIRouter, HTTPException, Path

from addon import disco, misc, storage

router = APIRouter()


@router.get("/instances")
def instances_get():
    postgres_projects = storage.get_postgres_project_names()
    return {
        "instances": [
            {"name": project_name.replace("postgres-instance-", "")}
            for project_name in postgres_projects
        ]
    }


@router.post("/instances", status_code=201)
def instances_post():
    version = "16.3"
    postgres_project_name = disco.create_postgres_project()
    storage.add_postgres_instance(postgres_project_name, version)
    admin_user = misc.generate_user_name()
    admin_password = misc.generate_password()
    storage.save_admin_credentials(
        postgres_project_name=postgres_project_name,
        user=admin_user,
        password=admin_password,
    )
    disco.init_postgres_env_variables(
        postgres_project_name=postgres_project_name,
        admin_user=admin_user,
        admin_password=admin_password,
    )
    deployment_number = disco.deploy_postgres_project(
        postgres_project_name=postgres_project_name,
        version=version,
    )
    return {
        "project": {
            "name": postgres_project_name,
        },
        "deployment": {
            "number": deployment_number,
        },
    }


@router.delete("/instances/{instance_name}", status_code=200)
def instance_delete(instance_name: Annotated[str, Path()]):
    postgres_project_name = misc.project_name_for_instance(instance_name)
    instance = storage.get_instance(postgres_project_name)
    if instance is None:
        raise HTTPException(
            status_code=404, detail=f"Instance {instance_name} not found"
        )
    for db_name in instance["databases"]:
        if len(instance["databases"][db_name]["users"]) > 0:
            usage = {}
            for user_info in instance["databases"][db_name]["users"].values():
                for attachment in user_info["attachments"]:
                    usage[attachment["project"]] = attachment["var"]
            raise HTTPException(422, f"Database {db_name} still in use: {usage}")
    if disco.project_exists(postgres_project_name):
        disco.remove_project(postgres_project_name)
    storage.remove_postgres_instance(postgres_project_name)
    return {}
