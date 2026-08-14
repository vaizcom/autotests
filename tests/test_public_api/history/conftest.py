import pytest

# Демо-сущности в PUBLIC_SPACE_ID (создаются при регистрации спейса, стабильные данные с историей)
DEMO_PROJECT_ID = "6a7c51a35a104e5f1b2186e1"
DEMO_TASK_ID = "6a7c51a85a104e5f1b218cd2"
DEMO_MILESTONE_ID = "6a7c51a35a104e5f1b2186f7"
DEMO_DOCUMENT_ID = "6a7c51a35a104e5f1b218713"


@pytest.fixture(scope="session")
def public_project_id():
    return DEMO_PROJECT_ID


@pytest.fixture(scope="session")
def public_task_id():
    return DEMO_TASK_ID


@pytest.fixture(scope="session")
def public_milestone_id():
    return DEMO_MILESTONE_ID


@pytest.fixture(scope="session")
def public_document_id():
    return DEMO_DOCUMENT_ID
