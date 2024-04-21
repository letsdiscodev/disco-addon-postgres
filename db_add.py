import os

from keyvaluestore import KeyValueStore
from utils import (
    add_db,
    add_postgres_project,
    attach_db,
    get_params_from_cli_args,
)
from storeutils import (
    get_admin_conn_str,
    get_postgres_project_names,
)


def main():
    addon_project_name = os.environ.get("DISCO_PROJECT_NAME")
    api_key = os.environ.get("DISCO_API_KEY")
    disco_host = os.environ.get("DISCO_HOST")
    project_name = get_params_from_cli_args(api_key)
    store = KeyValueStore(api_key=api_key, project_name=addon_project_name)
    postgres_projects = get_postgres_project_names(store)
    if len(postgres_projects) == 0:
        admin_conn_str, postgres_project_name = add_postgres_project(
            disco_host=disco_host,
            api_key=api_key,
            store=store,
        )
    else:
        postgres_project_name = postgres_projects[0]
        admin_conn_str = get_admin_conn_str(
            store=store, postgres_project_name=postgres_project_name, disco_host=disco_host
        )
    db_name, user = add_db(
        postgres_project_name=postgres_project_name,
        admin_conn_str=admin_conn_str,
        store=store,
    )
    attach_db(
        postgres_project_name=postgres_project_name,
        project_name=project_name,
        db_name=db_name,
        user=user,
        api_key=api_key,
        disco_host=disco_host,
        store=store,
    )


if __name__ == "__main__":
    main()
