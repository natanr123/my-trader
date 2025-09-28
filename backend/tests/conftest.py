from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, delete

from app.core.config import settings
from app.core.db import engine, init_db
from app.main import app
from app.models.item import Item
from app.models.user import User
from tests.utils.user import authentication_token_from_email
from tests.utils.utils import get_superuser_token_headers

from tests.fixtures import session_fixture, client_fixture, alpaca_client_fixture


#
# @pytest.fixture(name="session")
# def session_fixture():
#     engine = create_test_db_engine()
#     SQLModel.metadata.create_all(engine)
#     with Session(engine) as session:
#         def get_session_override():
#             return session
#         app.dependency_overrides[get_session] = get_session_override
#         yield session
#         app.dependency_overrides.clear()
#
#
# @pytest.fixture(scope="module")
# def client() -> Generator[TestClient, None, None]:
#     with TestClient(app) as c:
#         yield c
#


