import pytest

# Тестовые сущности в PUBLIC_SPACE_ID
# APP-5938: kind=Project/Milestone/Document возвращает 500 для вручную созданных сущностей
PROJECT_ID = "6a8d60e54c09ca59fa8e847a"       # Test Project
TASK_ID = "6a8d61164c09ca59fa8ebf96"          # Test Task (TSTPRJCT-1)
MILESTONE_ID = "6a8d63164c09ca59fa913619"     # Test Milestone
DOCUMENT_ID = "6a8d61994c09ca59fa8f848a"      # Test Document


@pytest.fixture(scope="session")
def project_id():
    return PROJECT_ID


@pytest.fixture(scope="session")
def task_id():
    return TASK_ID


@pytest.fixture(scope="session")
def milestone_id():
    return MILESTONE_ID


@pytest.fixture(scope="session")
def document_id():
    return DOCUMENT_ID
