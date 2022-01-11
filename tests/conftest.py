import pytest
from fastapi.testclient import TestClient

import sys, os
sys.path.append(os.getcwd())
import main

@pytest.fixture(scope="class")
def client():
    client = TestClient(main.app)
    yield client