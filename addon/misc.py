import string
import secrets


def assert_status_code(response, status_code):
    if response.status_code != status_code:
        raise Exception(
            f"Response status code not {status_code}, "
            f"reveived {response.status_code}: {response.text}"
        )


def conn_string(
    user: str, password: str, postgres_project_name: str, db_name: str | None
) -> str:
    instance_url = f"postgresql://{user}:{password}@{postgres_project_name}-postgres"
    if db_name is None:
        return instance_url
    return f"{instance_url}/{db_name}"


def project_name_for_instance(instance_name: str) -> str:
    return f"postgres-instance-{instance_name}"


def generate_str(include_uppercase: bool) -> str:
    if include_uppercase:
        ascii_letters = string.ascii_letters
    else:
        ascii_letters = string.ascii_lowercase
    alphabet = ascii_letters + string.digits
    first_char = secrets.choice(ascii_letters)
    rest = "".join(secrets.choice(alphabet) for _ in range(15))
    return first_char + rest


def generate_db_name() -> str:
    return generate_str(include_uppercase=False)


def generate_user_name() -> str:
    return generate_str(include_uppercase=False)


def generate_password() -> str:
    return generate_str(include_uppercase=True)
