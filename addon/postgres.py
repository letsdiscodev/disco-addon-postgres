import logging

import psycopg

log = logging.getLogger(__name__)


def create_db(admin_conn_str: str, db_name: str) -> None:
    log.info("Creating database %s", db_name)
    user = f"{db_name}_owner"
    with psycopg.connect(admin_conn_str) as conn:
        conn.autocommit = True
        with conn.cursor() as cur:
            cur.execute(f"CREATE DATABASE {db_name};")
    with psycopg.connect(f"{admin_conn_str}/{db_name}") as conn:
        conn.autocommit = True
        with conn.cursor() as cur:
            cur.execute(f"CREATE USER {user};")
            cur.execute(f"ALTER DATABASE {db_name} OWNER TO {user};")
            cur.execute(f"ALTER DEFAULT PRIVILEGES GRANT ALL ON TABLES TO {user};")
            cur.execute(f"ALTER DEFAULT PRIVILEGES GRANT ALL ON SEQUENCES TO {user};")
            cur.execute(f"ALTER DEFAULT PRIVILEGES GRANT ALL ON FUNCTIONS TO {user};")
            cur.execute(f"GRANT ALL PRIVILEGES ON DATABASE {db_name} TO {user};")
            cur.execute(f"GRANT ALL ON SCHEMA public TO {user};")


def drop_db(admin_conn_str: str, db_name: str) -> None:
    log.info("Dropping database %s", db_name)
    with psycopg.connect(admin_conn_str) as conn:
        conn.autocommit = True
        with conn.cursor() as cur:
            cur.execute(f"DROP DATABASE {db_name} WITH (FORCE);")


def add_user(admin_conn_str: str, db_name: str, user: str, password: str) -> None:
    log.info("Adding user %s to database %s", user, db_name)
    owner_role = f"{db_name}_owner"
    with psycopg.connect(f"{admin_conn_str}/{db_name}") as conn:
        conn.autocommit = True
        with conn.cursor() as cur:
            cur.execute(f"CREATE USER {user} WITH ENCRYPTED PASSWORD '{password}';")
            cur.execute(f"GRANT {owner_role} TO {user};")
            cur.execute(f"ALTER DEFAULT PRIVILEGES GRANT ALL ON TABLES TO {user};")
            cur.execute(f"ALTER DEFAULT PRIVILEGES GRANT ALL ON SEQUENCES TO {user};")
            cur.execute(f"ALTER DEFAULT PRIVILEGES GRANT ALL ON FUNCTIONS TO {user};")
            cur.execute(f"GRANT ALL PRIVILEGES ON DATABASE {db_name} TO {user};")
            cur.execute(f"GRANT ALL ON SCHEMA public TO {user};")
            cur.execute(f"GRANT ALL ON ALL TABLES IN SCHEMA public TO {user};")
            cur.execute(f"GRANT ALL ON ALL SEQUENCES IN SCHEMA public TO {user};")
            cur.execute(f"GRANT ALL ON ALL FUNCTIONS IN SCHEMA public TO {user};")


def remove_user(admin_conn_str: str, db_name: str, user: str) -> None:
    log.info("Removing user %s", user)
    owner_role = f"{db_name}_owner"
    with psycopg.connect(f"{admin_conn_str}/{db_name}") as conn:
        conn.autocommit = True
        with conn.cursor() as cur:
            cur.execute(f"REASSIGN OWNED BY {user} TO {owner_role};")
            cur.execute(f"REVOKE ALL PRIVILEGES ON DATABASE {db_name} FROM {user};")
            cur.execute(f"REVOKE ALL ON SCHEMA public FROM {user};")
            cur.execute(f"REVOKE ALL ON ALL TABLES IN SCHEMA public FROM {user};")
            cur.execute(f"REVOKE ALL ON ALL SEQUENCES IN SCHEMA public FROM {user};")
            cur.execute(f"REVOKE ALL ON ALL FUNCTIONS IN SCHEMA public FROM {user};")
            cur.execute(f"ALTER DEFAULT PRIVILEGES REVOKE ALL ON TABLES FROM {user};")
            cur.execute(
                f"ALTER DEFAULT PRIVILEGES REVOKE ALL ON SEQUENCES FROM {user};"
            )
            cur.execute(
                f"ALTER DEFAULT PRIVILEGES REVOKE ALL ON FUNCTIONS FROM {user};"
            )
            cur.execute(f"DROP USER {user};")
