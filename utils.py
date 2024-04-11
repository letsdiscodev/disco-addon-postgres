import string
import secrets
import sys
import json

from keyvaluestore import KeyValueStore
import psycopg
import requests
import sseclient
from storeutils import (
    get_conn_str,
    remember_admin_credentials,
    remember_db,
    remember_postgres_project_name,
)


def add_postgres_project(
    disco_ip: str, store: KeyValueStore, api_key: str
) -> tuple[str, str]:
    postgres_project_name = create_postgres_project(api_key)
    remember_postgres_project_name(store, postgres_project_name)
    admin_user = generate_str(include_uppercase=False)
    admin_password = generate_str(include_uppercase=True)
    remember_admin_credentials(
        store=store,
        postgres_project_name=postgres_project_name,
        user=admin_user,
        password=admin_password,
    )
    init_postgres_env_variables(
        api_key=api_key,
        postgres_project_name=postgres_project_name,
        admin_user=admin_user,
        admin_password=admin_password,
    )
    deploy_postgres_project(
        postgres_project_name=postgres_project_name, api_key=api_key
    )
    return (
        f"postgresql://{admin_user}:{admin_password}@{disco_ip}",
        postgres_project_name,
    )


def add_db(
    postgres_project_name: str, admin_conn_str: str, store: KeyValueStore
) -> tuple[str, str]:
    db_name, user, password = sql_add_db(admin_conn_str)
    remember_db(
        store=store,
        postgres_project_name=postgres_project_name,
        db_name=db_name,
        user=user,
        password=password,
    )
    return db_name, user


def sql_add_db(admin_conn_str: str) -> tuple[str, str, str]:
    new_db_name = generate_str(include_uppercase=False)
    new_user = generate_str(include_uppercase=False)
    new_password = generate_str(include_uppercase=True)

    with psycopg.connect(admin_conn_str) as conn:
        conn.autocommit = True
        with conn.cursor() as cur:
            cur.execute(f"CREATE DATABASE {new_db_name};")
            cur.execute(
                f"CREATE USER {new_user} WITH ENCRYPTED PASSWORD '{new_password}';"
            )
            cur.execute(
                f"GRANT ALL PRIVILEGES ON DATABASE {new_db_name} TO {new_user};"
            )
            cur.execute(f"ALTER DATABASE {new_db_name} OWNER TO {new_user};")

    return new_db_name, new_user, new_password


def attach_db(
    postgres_project_name: str,
    project_name: str,
    db_name: str,
    user: str,
    api_key: str,
    disco_ip: str,
    store: KeyValueStore,
) -> None:
    url = f"http://disco/projects/{project_name}/env"
    req_body = dict(
        envVariables=[
            {
                "name": "DATABASE_URL",
                "value": get_conn_str(
                    store=store,
                    postgres_project_name=postgres_project_name,
                    db_name=db_name,
                    user=user,
                    disco_ip=disco_ip,
                ),
            }
        ],
    )
    response = requests.post(
        url,
        json=req_body,
        auth=(api_key, ""),
        headers={"Accept": "application/json"},
        timeout=10,
    )
    assert_status_code(response, 200)
    resp_body = response.json()
    if resp_body["deployment"] is None:
        return
    url = (
        f"http://disco/projects/{postgres_project_name}"
        f"/deployments/{resp_body['deployment']['number']}/output"
    )
    response = requests.get(
        url,
        auth=(api_key, ""),
        headers={"Accept": "text/event-stream"},
        stream=True,
    )
    for event in sseclient.SSEClient(response).events():
        if event.event == "output":
            output = json.loads(event.data)
            print(output["text"], end="", flush=True)
        elif event.event == "end":
            break


def create_postgres_project(api_key: str) -> str:
    req_body = {
        "name": "postgres-instance",
        "generateSuffix": True,
    }
    response = requests.post(
        f"http://disco/projects",
        json=req_body,
        auth=(api_key, ""),
        headers={"Accept": "application/json"},
        timeout=10,
    )
    assert_status_code(response, 201)
    return response.json()["project"]["name"]


def init_postgres_env_variables(
    api_key: str, postgres_project_name: str, admin_user: str, admin_password: str
) -> None:
    url = f"http://disco/projects/{postgres_project_name}/env"
    req_body = dict(
        envVariables=[
            {
                "name": "POSTGRES_USER",
                "value": admin_user,
            },
            {
                "name": "POSTGRES_PASSWORD",
                "value": admin_password,
            },
            {
                "name": "PGDATA",
                "value": "/var/lib/postgresql/data/pgdata",
            },
        ],
    )
    response = requests.post(
        url,
        json=req_body,
        auth=(api_key, ""),
        headers={"Accept": "application/json"},
        timeout=10,
    )
    assert_status_code(response, 200)


def deploy_postgres_project(postgres_project_name: str, api_key: str) -> None:
    url = f"http://disco/projects/{postgres_project_name}/deployments"
    with open("postgres.json", "r", encoding="utf-8") as f:
        disco_file_str = f.read()
    disco_file = json.loads(disco_file_str)
    disco_file["services"]["postgres"]["volumes"][0]["name"] = (
        f"{postgres_project_name}-data"
    )
    req_body = {
        "discoFile": disco_file,
    }
    response = requests.post(
        url,
        json=req_body,
        auth=(api_key, ""),
        headers={"Accept": "application/json"},
        timeout=10,
    )
    assert_status_code(response, 201)
    resp_body = response.json()
    url = (
        f"http://disco/projects/{postgres_project_name}/deployments"
        f"/{resp_body['deployment']['number']}/output"
    )
    response = requests.get(
        url,
        auth=(api_key, ""),
        headers={"Accept": "text/event-stream"},
        stream=True,
    )
    for event in sseclient.SSEClient(response).events():
        output = json.loads(event.data)
        print(output["text"], end="", flush=True)


def get_params_from_cli_args(api_key: str) -> str:
    project = None
    for i, arg in enumerate(sys.argv):
        if arg == "--project" and len(sys.argv) > i + 1:
            project = sys.argv[i + 1]
    if project is None:
        raise Exception("Please pass project name with --project")
    if not project_exists(api_key, project):
        raise Exception(f"Project {project} doesn't exist")
    return project


def project_exists(api_key: str, project: str):
    response = requests.get(
        "http://disco/projects",
        auth=(api_key, ""),
        headers={"Accept": "application/json"},
        timeout=10,
    )
    assert_status_code(response, 200)
    return project in [project["name"] for project in response.json()["projects"]]


def assert_status_code(response, status_code):
    if response.status_code != status_code:
        raise Exception(
            f"Response status code not {status_code}, "
            f"reveived {response.status_code}: {response.text}"
        )


def generate_str(include_uppercase: bool) -> str:
    if include_uppercase:
        ascii_letters = string.ascii_letters
    else:
        ascii_letters = string.ascii_lowercase
    alphabet = ascii_letters + string.digits
    first_char = secrets.choice(ascii_letters)
    rest = "".join(secrets.choice(alphabet) for _ in range(15))
    return first_char + rest
