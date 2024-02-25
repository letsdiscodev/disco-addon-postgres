import os
import json

import psycopg
import requests
import sseclient


admin_conn_str = os.environ.get("ADMIN_CONN_STR")
addon_project_name = os.environ.get("DISCO_PROJECT_NAME")
api_key = os.environ.get("DISCO_API_KEY")
disco_ip = os.environ.get("DISCO_IP")

def main():
    global admin_conn_str
    project_name = "dummy" # get from command line args?
    if admin_conn_str is None:
        admin_conn_str = create_postgres_project(disco_ip)
    add_db(disco_ip, project_name)


def create_postgres_project(disco_ip: str) -> str:
    req_body = {
        "name": "postgres-db",
    }
    response = requests.post(f"http://disco/projects",
        json=req_body,
        auth=(api_key, ""),
        headers={"Accept": "application/json"},
    )
    assert response.status_code == 201
    admin_user = "postgresadmin" # TODO generate username
    admin_password = "Password1" # TODO generate password
    url = f"http://disco/projects/postgres-db/env"
    req_body = dict(
        envVariables=[
        {
            "name": "POSTGRES_USER",
            "value": admin_user,
        },{
            "name": "POSTGRES_PASSWORD",
            "value": admin_password,
        },
        {
            "name": "PGDATA",
            "value": "/var/lib/postgresql/data/pgdata",
        }],
    )
    response = requests.post(url,
        json=req_body,
        auth=(api_key, ""),
        headers={"Accept": "application/json"},
    )
    assert response.status_code == 200
    url = f"http://disco/projects/postgres-db/deployments"
    with open("postgres.json", "r", encoding="utf-8") as f:
        disco_file = f.read()
    req_body = {
        "discoFile": disco_file,
    }
    response = requests.post(url,
        json=req_body,
        auth=(api_key, ""),
        headers={"Accept": "application/json"},
    )
    assert response.status_code == 201
    resp_body = response.json()
    url = f"http://disco/projects/postgres-db/deployments/{resp_body['deployment']['number']}/output"
    response = requests.get(url,
        auth=(api_key, ""),
        headers={'Accept': 'text/event-stream'},
        stream=True,
    )
    for event in sseclient.SSEClient(response).events():
        output = json.loads(event.data)
        print(output["text"], end="", flush=True)
    admin_conn_str = f"postgresql://{admin_user}:{admin_password}@{disco_ip}"
    url = f"http://disco/projects/{addon_project_name}/env"
    req_body = dict(
        envVariables=[
        {
            "name": "ADMIN_CONN_STR",
            "value": admin_conn_str,
        }],
    )
    response = requests.post(url,
        json=req_body,
        auth=(api_key, ""),
        headers={"Accept": "application/json"},
    )
    assert response.status_code == 200
    return admin_conn_str


def add_db(disco_ip: str, project_name: str) -> None:
    new_db_name = "new_db_name" # TODO generate
    new_user = "new_user" # TODO generate
    new_password = "pwpwpwpw" # TODO generate

    with psycopg.connect(admin_conn_str) as conn:
        with conn.cursor() as cur:
            cur.execute(f"CREATE DATABASE {new_db_name};")
            cur.execute(f"CREATE USER {new_user} WITH ENCRYPTED PASSWORD '{new_password}';")
            cur.execute(f"GRANT ALL PRIVILEGES ON DATABASE {new_db_name} TO {new_user};")


    # TODO save new DB/user info
    conn_str = f"postgresql://{new_db_name}:{new_password}@{disco_ip}/{new_db_name}"
    url = f"http://disco/projects/{project_name}/env"
    req_body = dict(
        envVariables=[
        {
            "name": "DATABASE_URL",
            "value": conn_str,
        }],
    )
    response = requests.post(url,
        json=req_body,
        auth=(api_key, ""),
        headers={"Accept": "application/json"},
    )
    assert response.status_code == 200
    # TODO print deployment output?


if __name__ == "__main__":
    main()