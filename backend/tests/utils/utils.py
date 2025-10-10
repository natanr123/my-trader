import random
import string

from fastapi.testclient import TestClient

from app.core.config.app_settings import app_settings


def random_lower_string() -> str:
    return "".join(random.choices(string.ascii_lowercase, k=32))


def random_email() -> str:
    return f"{random_lower_string()}@{random_lower_string()}.com"


def get_superuser_token_headers(client: TestClient) -> dict[str, str]:
    login_data = {
        "username": app_settings.FIRST_SUPERUSER,
        "password": app_settings.FIRST_SUPERUSER_PASSWORD,
    }
    r = client.post(f"{app_settings.API_V1_STR}/login/access-token", data=login_data)
    tokens = r.json()
    a_token = tokens["access_token"]
    headers = {"Authorization": f"Bearer {a_token}"}
    return headers
