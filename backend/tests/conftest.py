import os

# Set test environment before any imports that load settings
os.environ["ENVIRONMENT"] = "test"

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

from tests.fixtures import session_fixture, client_fixture, alpaca_client_fixture, db_fixture, superuser_token_headers, normal_user_token_headers