import pytest
from sqlmodel import Session, SQLModel
from sqlmodel.pool import StaticPool

from fastapi.testclient import TestClient
from app.main import app
from app.api.deps.alpaca_dep import get_alpaca_client
from tests.utils.user import authentication_token_from_email
from tests.utils.utils import get_superuser_token_headers
from app.core.config import settings
from sqlmodel import Session, SQLModel, create_engine
from app.api.deps.deps import get_db

def create_test_db_engine():
    return create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)

@pytest.fixture(name="db")
def db_fixture():
    engine = create_test_db_engine()
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session

@pytest.fixture(name="session")
def session_fixture():
    engine = create_test_db_engine()
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        def get_session_override():
            return session
        app.dependency_overrides[get_db] = get_session_override
        yield session
        app.dependency_overrides.clear()


@pytest.fixture(name="client")
def client_fixture(session: Session):
    client = TestClient(app)
    yield client

@pytest.fixture(name="alpaca_client")
def alpaca_client_fixture():
    app.dependency_overrides[get_alpaca_client] = get_alpaca_client
    alpaca_client = get_alpaca_client()
    yield alpaca_client
    app.dependency_overrides.clear()

@pytest.fixture(name="superuser_token_headers")
def superuser_token_headers(client: TestClient) -> dict[str, str]:
    return get_superuser_token_headers(client)


@pytest.fixture(name="normal_user_token_headers")
def normal_user_token_headers(client: TestClient, db: Session) -> dict[str, str]:
    return authentication_token_from_email(
        client=client, email=settings.EMAIL_TEST_USER, db=db
    )