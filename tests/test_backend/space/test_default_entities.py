import allure
import pytest

from test_backend.data.endpoints.Board.board_endpoints import get_boards_endpoint
from test_backend.data.endpoints.Document.document_endpoints import get_documents_endpoint
from test_backend.data.endpoints.Project.project_endpoints import get_projects_endpoint
from test_backend.data.endpoints.Task.task_endpoints import get_tasks_endpoint

pytestmark = [pytest.mark.backend]


@allure.parent_suite('Space Service')
@allure.suite('Default Entities')
@allure.title('Default project created on registration')
def test_default_project(temp_client):
    client, space_id = temp_client

    with allure.step('GetProjects — запрос проектов в новом спейсе'):
        resp = client.post(**get_projects_endpoint(space_id=space_id))
        assert resp.status_code == 200, f'GetProjects вернул {resp.status_code}: {resp.text}'

    with allure.step('Проверка: есть хотя бы один дефолтный проект'):
        projects = resp.json()['payload']['projects']
        assert len(projects) >= 1, f'Ожидался хотя бы 1 проект, получено: {len(projects)}'


@allure.parent_suite('Space Service')
@allure.suite('Default Entities')
@allure.title('Default board "Start with Vaiz" created on registration')
def test_default_board(temp_client):
    client, space_id = temp_client

    with allure.step('GetBoards — запрос борд в новом спейсе'):
        resp = client.post(**get_boards_endpoint(space_id=space_id))
        assert resp.status_code == 200, f'GetBoards вернул {resp.status_code}: {resp.text}'

    with allure.step('Проверка: борда «Start with Vaiz» существует'):
        boards = resp.json()['payload']['boards']
        board_names = [b['name'] for b in boards]
        assert 'Start with Vaiz' in board_names, (
            f'Борда «Start with Vaiz» не найдена. Борды: {board_names}'
        )


@allure.parent_suite('Space Service')
@allure.suite('Default Entities')
@allure.title('Default tasks created on board "Start with Vaiz"')
def test_default_tasks(temp_client):
    client, space_id = temp_client

    with allure.step('GetTasks — запрос задач в новом спейсе'):
        resp = client.post(**get_tasks_endpoint(space_id=space_id))
        assert resp.status_code == 200, f'GetTasks вернул {resp.status_code}: {resp.text}'

    tasks = resp.json()['payload']['tasks']
    task_names = [t['name'] for t in tasks]

    with allure.step('Проверка: задача «Find a new task manager and sign up to explore»'):
        assert 'Find a new task manager and sign up to explore' in task_names, (
            f'Дефолтная задача не найдена. Задачи: {task_names}'
        )


@allure.parent_suite('Space Service')
@allure.suite('Default Entities')
@allure.title('Default document "The Basics of Vaiz" created on registration')
def test_default_document(temp_client):
    client, space_id = temp_client

    with allure.step('GetDocuments — запрос Space-документов в новом спейсе'):
        resp = client.post(**get_documents_endpoint(kind='Space', kind_id=space_id, space_id=space_id))
        assert resp.status_code == 200, f'GetDocuments вернул {resp.status_code}: {resp.text}'

    with allure.step('Проверка: документ «The Basics of Vaiz» существует'):
        docs = resp.json()['payload']['documents']
        doc_titles = [d.get('title', '') for d in docs]
        assert 'The Basics of Vaiz' in doc_titles, (
            f'Документ «The Basics of Vaiz» не найден. Документы: {doc_titles}'
        )
