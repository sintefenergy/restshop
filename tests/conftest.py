import pytest
from fastapi.testclient import TestClient

import sys, os
sys.path.append(os.getcwd())
import main

@pytest.fixture(scope="class")
def client():
    client = TestClient(main.app)
    return client

@pytest.fixture(scope="class")
def session_id_manager():
    class SessionIdManager:
        def __init__(self):
            self.session_id = 1
    return SessionIdManager()