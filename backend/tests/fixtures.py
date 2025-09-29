import pytest
from sqlmodel import Session, SQLModel
from sqlmodel.pool import StaticPool

from fastapi.testclient import TestClient

from app.clients.my_alpaca_client import MyAlpacaClient
from app.main import app
from tests.utils.user import authentication_token_from_email
from tests.utils.utils import get_superuser_token_headers
from app.core.config import settings
from sqlmodel import Session, SQLModel, create_engine
from app.api.deps.deps import get_db
from collections.abc import Generator
from app.api.deps.alpaca_dep import get_alpaca_client_test

from app.api.deps.order_service_dep import get_order_service
from app.services.order_service import OrderService


def create_test_db_engine():
    return create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)

@pytest.fixture(name="session")
def session_fixture():
    from app.core.db import init_db
    engine = create_test_db_engine()
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        init_db(session)
        yield session

@pytest.fixture(name="db")
def db_fixture(session):
    return session

@pytest.fixture(name="client")
def client_fixture(session: Session):
    def get_session_override():
        return session
    app.dependency_overrides[get_db] = get_session_override
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()

@pytest.fixture(name="alpaca_client")
def alpaca_client_fixture() -> Generator[MyAlpacaClient, None, None]:
    def get_override():
        return get_alpaca_client_test()
    alpaca_client = get_override()
    yield alpaca_client

@pytest.fixture(name="order_service")
def order_service_fixture() -> Generator[OrderService, None, None]:
    yield get_order_service()

@pytest.fixture(name="superuser_token_headers")
def superuser_token_headers(client: TestClient) -> dict[str, str]:
    return get_superuser_token_headers(client)


@pytest.fixture(name="normal_user_token_headers")
def normal_user_token_headers(client: TestClient, db: Session) -> dict[str, str]:
    return authentication_token_from_email(
        client=client, email=settings.EMAIL_TEST_USER, db=db
    )