from typing import Annotated

from fastapi import APIRouter, HTTPException, Path

from addon import misc, postgres, storage
from addon.models.db import Session

router = APIRouter()


@router.get(
    "/instances/{instance_name}/databases",
)
def instance_databases_get(
    instance_name: Annotated[str, Path()],
):
    with Session.begin() as dbsession:
        instance = storage.get_instance_by_name(dbsession, instance_name)
        if instance is None:
            raise HTTPException(
                status_code=404, detail=f"Instance {instance_name} not found"
            )
        return {
            "databases": [
                {
                    "created": database.created.isoformat(),
                    "name": database.name,
                    "users": [
                        {
                            "created": user.created.isoformat(),
                            "name": user.name,
                            "attachments": [
                                {
                                    "created": attachment.created.isoformat(),
                                    "project": attachment.project_name,
                                    "envVar": attachment.env_var,
                                }
                                for attachment in user.attachments
                            ],
                        }
                        for user in database.users
                    ],
                }
                for database in instance.databases
            ]
        }


@router.post("/instances/{instance_name}/databases", status_code=201)
def instance_databases_post(
    instance_name: Annotated[str, Path()],
):
    with Session.begin() as dbsession:
        instance = storage.get_instance_by_name(dbsession, instance_name)
        if instance is None:
            raise HTTPException(
                status_code=404, detail=f"Instance {instance_name} not found"
            )
    admin_conn_str = storage.get_admin_conn_str(
        instance_name,
    )
    assert admin_conn_str is not None
    db_name = misc.generate_db_name()
    postgres.create_db(admin_conn_str=admin_conn_str, db_name=db_name)
    storage.add_db(instance_name, db_name)
    return {"database": {"name": db_name}}


@router.delete("/instances/{instance_name}/databases/{db_name}")
def database_delete(
    instance_name: Annotated[str, Path()],
    db_name: Annotated[str, Path()],
):
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
        attachments = storage.get_attachments_for_database(dbsession, instance, db_name)
        if len(attachments) > 0:
            usage = [
                {"project": attachment.project_name, "envVar": attachment.env_var}
                for attachment in attachments
            ]
            raise HTTPException(422, f"Database {db_name} still in use: {usage}")
    admin_conn_str = storage.get_admin_conn_str(instance_name)
    assert admin_conn_str is not None
    postgres.drop_db(admin_conn_str=admin_conn_str, db_name=db_name)
    storage.remove_db(instance_name, db_name)
    return {}
