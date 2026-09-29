import os

import pytest

# Never import `magicvibe` at module level here: its settings are read on
# import, so the environment below must be in place first.

SERVICE_TOKEN = "test-service-token"


def pytest_configure(config: pytest.Config) -> None:
    os.environ["AUTH__SERVICE_TOKEN"] = SERVICE_TOKEN
