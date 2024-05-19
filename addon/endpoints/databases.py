from addon import misc, postgres, storage
from fastapi import APIRouter, Path, HTTPException
from typing import Annotated

router = APIRouter()


@router.get("/instances/{instance_name}/databases")
def instance_databases_get(instance_name: Annotated[str, Path()]):
    postgres_project_name = misc.project_name_for_instance(instance_name)
    instance = storage.get_instance(postgres_project_name)
    if instance is None:
        raise HTTPException(
            status_code=404, detail=f"Instance {instance_name} not found"
        )
    return {
        "databases": [
            {
                "name": db_name,
                **db_info,
            }
            for db_name, db_info in instance["databases"].items()
        ]
    }


@router.post("/instances/{instance_name}/databases", status_code=201)
def instance_databases_post(instance_name: Annotated[str, Path()]):
    postgres_project_name = misc.project_name_for_instance(instance_name)
    instance = storage.get_instance(postgres_project_name)
    if instance is None:
        raise HTTPException(
            status_code=404, detail=f"Instance {instance_name} not found"
        )

    admin_conn_str = storage.get_admin_conn_str(
        postgres_project_name=postgres_project_name,
    )
    assert admin_conn_str is not None
    db_name = misc.generate_db_name()
    postgres.create_db(admin_conn_str=admin_conn_str, db_name=db_name)
    storage.add_db(postgres_project_name, db_name)
    return {"database": {"name": db_name}}


@router.delete("/instances/{instance_name}/databases/{db_name}")
def database_delete(
    instance_name: Annotated[str, Path()], db_name: Annotated[str, Path()]
):
    postgres_project_name = misc.project_name_for_instance(instance_name)
    instance = storage.get_instance(postgres_project_name)
    if instance is None:
        raise HTTPException(
            status_code=404, detail=f"Instance {instance_name} not found"
        )
    if db_name not in instance["databases"]:
        raise HTTPException(
            status_code=404, detail=f"Database {db_name} not found in {instance_name}"
        )
    if len(instance["databases"][db_name]["users"]) > 0:
        usage = {}
        for user_info in instance["databases"][db_name]["users"].values():
            for attachment in user_info["attachments"]:
                usage[attachment["project"]] = attachment["var"]
        raise HTTPException(422, f"Database {db_name} still in use: {usage}")
    admin_conn_str = storage.get_admin_conn_str(
        postgres_project_name=postgres_project_name,
    )
    assert admin_conn_str is not None
    postgres.drop_db(admin_conn_str=admin_conn_str, db_name=db_name)
    storage.remove_db(postgres_project_name, db_name)
    return {}
