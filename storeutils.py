import json

from keyvaluestore import KeyValueStore


POSTGRES_PROJECT_NAMES_KEY = "POSTGRES_PROJECT_NAMES"
POSTGRES_META_KEY = "POSTGRES_META_{project_name}"


def get_postgres_project_names(store: KeyValueStore) -> list[str]:
    value = store.get(key=POSTGRES_PROJECT_NAMES_KEY)
    if value is None:
        return []
    return json.loads(value)


def remember_postgres_project_name(store: KeyValueStore, name: str) -> None:
    def update_func(value: str | None) -> str:
        if value is None:
            names = []
        else:
            names = json.loads(value)
        names.append(name)
        new_value = json.dumps(names)
        return new_value

    store.update(key=POSTGRES_PROJECT_NAMES_KEY, update_func=update_func)


def remember_admin_credentials(
    store: KeyValueStore, postgres_project_name: str, user: str, password: str
) -> None:
    def update_func(value: str | None) -> str:
        if value is None:
            meta = {"databases": {}}
        else:
            meta = json.loads(value)
        meta["adminUser"] = user
        meta["adminPassword"] = password
        new_value = json.dumps(meta)
        return new_value

    key = POSTGRES_META_KEY.format(project_name=postgres_project_name)
    store.update(key=key, update_func=update_func)


def remember_db(
    store: KeyValueStore,
    postgres_project_name: str,
    db_name: str,
    user: str,
    password: str,
) -> None:
    def update_func(value: str | None) -> str:
        if value is None:
            meta = {"databases": {}}
        else:
            meta = json.loads(value)
        meta["databases"][db_name] = {
            "users": {},
        }
        meta["databases"][db_name]["users"][user] = {
            "password": password,
        }
        new_value = json.dumps(meta)
        return new_value

    key = POSTGRES_META_KEY.format(project_name=postgres_project_name)
    store.update(key=key, update_func=update_func)


def get_admin_conn_str(
    store: KeyValueStore, postgres_project_name: str, disco_host: str
) -> str | None:
    key = POSTGRES_META_KEY.format(project_name=postgres_project_name)
    value = store.get(key)
    if value is None:
        return None
    meta = json.loads(value)
    if "adminUser" not in meta:
        return None
    if "adminPassword" not in meta:
        return None
    return f"postgresql://{meta['adminUser']}:{meta['adminPassword']}@{disco_host}"


def get_conn_str(
    store: KeyValueStore,
    postgres_project_name: str,
    db_name: str,
    user: str,
    disco_host: str,
) -> str | None:
    key = POSTGRES_META_KEY.format(project_name=postgres_project_name)
    value = store.get(key)
    if value is None:
        return None
    meta = json.loads(value)
    if db_name not in meta["databases"]:
        return None
    if user not in meta["databases"][db_name]["users"]:
        return None
    password = meta["databases"][db_name]["users"][user]["password"]
    return f"postgresql://{user}:{password}@{disco_host}/{db_name}"
