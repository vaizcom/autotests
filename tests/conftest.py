import datetime
import os
import uuid

from pymongo import MongoClient

import pytest
import requests
import urllib3
import allure
import random
import time

from config.generators import generate_date
from config.settings import BOARD_WITH_TASKS, SECOND_SPACE_ID, SECOND_PROJECT_ID, BOARD_FOR_TEST, MAIN_PROJECT_2_ID, \
    SECOND_BOARD_ID
from test_backend.data.endpoints.Task.task_endpoints import get_tasks_endpoint, create_task_endpoint, \
    delete_task_endpoint
from test_backend.data.endpoints.User.profile_endpoint import get_profile_endpoint
from test_backend.data.endpoints.User.register_endpoint import register_endpoint
from test_backend.data.endpoints.access_group.aaccess_group_endpoints import create_access_group_endpoint
from test_backend.data.endpoints.invite.invite_endpoint import invite_to_space_endpoint, confirm_space_invite_endpoint
from test_backend.data.endpoints.milestone.milestones_endpoints import create_milestone_endpoint, \
    archive_milestone_endpoint
from tests.config import settings
from tests.config.generators import generate_space_name, generate_project_name, generate_slug, generate_board_name
from tests.test_backend.data.endpoints.Board.board_endpoints import get_board_endpoint
from tests.test_backend.data.endpoints.Document.document_endpoints import create_document_endpoint, archive_document_endpoint
from tests.test_backend.data.endpoints.member.member_endpoints import get_space_members_endpoint
from tests.core.client import APIClient
from tests.core.auth import get_token
from tests.config.settings import API_URL, MAIN_SPACE_ID, MAIN_PROJECT_ID, MAIN_BOARD_ID
from tests.test_backend.data.endpoints.Board.constants import DEFAULT_BOARD_GROUPS
from tests.test_backend.data.endpoints.Project.project_endpoints import (
    create_project_endpoint,
    create_board_endpoint,
    get_project_endpoint,
)
from tests.test_backend.data.endpoints.Space.space_endpoints import (
    create_space_endpoint,
    remove_space_endpoint,
    get_space_endpoint, get_spaces_endpoint,
)


def pytest_configure(config):
    print(f'\n🧪 Running on stand: {settings.TEST_STAND_NAME}')
    print(f'🔗 API URL: {settings.API_URL}\n')

@pytest.fixture(scope="session")
def mongo_client():
    """Создает подключение к MongoDB на время всего прогона тестов."""
    # Получаем URI из переменных окружения (которые грузятся из .env)
    mongo_uri = os.getenv("MONGO_URI")

    # Подключаемся
    client = MongoClient(mongo_uri)

    yield client

    # Закрываем соединение после завершения всех тестов
    client.close()


@pytest.fixture(scope="session")
def db(mongo_client):
    """Возвращает конкретную базу данных для работы."""
    db_name = os.getenv("MONGO_DB_NAME")
    return mongo_client[db_name]


@pytest.fixture(scope="session", autouse=True)
def global_ssl_settings():
    """
    Глобальная настройка SSL для всех тестов.
    Если стенд 'local', отключает верификацию сертификатов для всех запросов requests.
    """
    # Получаем название стенда из переменных окружения (из .env)
    stand_name = os.getenv("TEST_STAND_NAME", "local")  # По умолчанию local, если не задано

    if stand_name == "local":
        # 1. Отключаем предупреждения InsecureRequestWarning, чтобы не засорять логи
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

        # 2. Сохраняем оригинальный метод request
        original_request = requests.Session.request

        # 3. Создаем обертку (патч), которая принудительно ставит verify=False
        def patched_request(self, method, url, *args, **kwargs):
            # Если verify не передан явно в тесте, ставим False
            if 'verify' not in kwargs:
                kwargs['verify'] = False
            return original_request(self, method, url, *args, **kwargs)

        # 4. Применяем патч глобально для всех сессий requests
        requests.Session.request = patched_request


@pytest.fixture(scope='session')
def main_client():
    return APIClient(base_url=API_URL, token=get_token('main'))

@pytest.fixture(scope='session')
def second_main_client():
    return APIClient(base_url=API_URL, token=get_token('second_main'))


# Фикстура: возвращает авторизованного API клиента с токеном владельца
@pytest.fixture(scope='session')
def owner_client():
    return APIClient(base_url=API_URL, token=get_token('owner'))


@pytest.fixture(scope='session')
def manager_client():
    return APIClient(base_url=API_URL, token=get_token('manager'))


@pytest.fixture(scope='session')
def member_client():
    return APIClient(base_url=API_URL, token=get_token('member'))


@pytest.fixture(scope='session')
def guest_client():
    return APIClient(base_url=API_URL, token=get_token('guest'))


# Пользователь не имеет доступ к spаce
@pytest.fixture(scope='session')
def foreign_client():
    return APIClient(base_url=API_URL, token=get_token('foreign_client'))

@pytest.fixture(scope="session")
def temp_client():
    """
    Регистрирует нового пользователя, авторизует его и
    возвращает готовый APIClient и ID спейса для тестов(на лимиты).
    """
    base_url = API_URL
    timestamp = int(time.time())
    email = f"space_{timestamp}@autotest.com"
    password = "123456"
    name = f"Rate Limit {timestamp}"

    # 1. Регистрация пользователя
    reg_data = register_endpoint(
        email=email,
        password=password,
        full_name=name,
        terms_accepted=True
    )
    reg_url = f"{base_url.rstrip('/')}{reg_data['path']}"
    reg_resp = requests.post(reg_url, json=reg_data['json'], headers=reg_data['headers'])
    assert reg_resp.status_code == 200, f"Ошибка регистрации: {reg_resp.text}"

    login_json = reg_resp.json()
    token = login_json.get("payload", {}).get("token")
    space_id = reg_resp.json().get("payload", {}).get("space", {}).get("_id")

    assert token and space_id, "Не удалось получить token или space_id"

    # Возвращаем стандартный клиент вашего фреймворка и space_id
    client = APIClient(base_url=base_url, token=token)
    return client, space_id


# Пользователь имеет доступ к spаce в роли member(и не имеет доступ к проекту и борде)
@pytest.fixture(scope='session')
def client_with_access_only_in_space():
    return APIClient(base_url=API_URL, token=get_token('space_client'))


# Пользователь имеет доступ к spаce и к проекту (и не имеет доступ к борде)
@pytest.fixture(scope='session')
def client_with_access_only_in_project():
    return APIClient(base_url=API_URL, token=get_token('project_client'))


@pytest.fixture(scope='session')
def main_space(main_client) -> str:
    """
    Отличие этого спейса в том, что в  этом спейсе уже есть мемберы с разными ролями.
    """

    assert MAIN_SPACE_ID, 'Не задана переменная окружения MAIN_SPACE_ID'
    resp = main_client.post(**get_space_endpoint(space_id=MAIN_SPACE_ID))
    assert resp.status_code == 200, f'Space {MAIN_SPACE_ID} not found: {resp.text}'
    return MAIN_SPACE_ID

@pytest.fixture(scope='session')
def second_space(main_client) -> str:
    """
    Отличие этого спейса в том, что в  этом спейсе уже есть мемберы с разными ролями(Дубликат).
    """
    assert SECOND_SPACE_ID, 'Не задана переменная окружения SECOND_SPACE_ID'
    resp = main_client.post(**get_space_endpoint(space_id=SECOND_SPACE_ID))
    assert resp.status_code == 200, f'Space {SECOND_SPACE_ID} not found: {resp.text}'
    return SECOND_SPACE_ID

@pytest.fixture(scope='session')
def main_project(main_client, main_space):
    assert MAIN_PROJECT_ID, 'Не задана переменная окружения MAIN_PROJECT_ID'
    resp = main_client.post(**get_project_endpoint(project_id=MAIN_PROJECT_ID, space_id=main_space))
    assert resp.status_code == 200, f'Space {MAIN_PROJECT_ID} not found: {resp.text}'
    return MAIN_PROJECT_ID

# Проект в котором есть пользователи с разными ролями, для разных сценариев (архивация, редактирования и пр)
@pytest.fixture(scope='session')
def main_project_2(main_client, main_space):
    assert MAIN_PROJECT_2_ID, 'Не задана переменная окружения MAIN_PROJECT_2_ID'
    resp = main_client.post(**get_project_endpoint(project_id=MAIN_PROJECT_2_ID, space_id=main_space))
    assert resp.status_code == 200, f'Space {MAIN_PROJECT_2_ID} not found: {resp.text}'
    return MAIN_PROJECT_2_ID

@pytest.fixture(scope='session')
def second_project(main_client, second_space):
    assert SECOND_PROJECT_ID, 'Не задана переменная окружения MAIN_PROJECT_ID'
    resp = main_client.post(**get_project_endpoint(project_id=SECOND_PROJECT_ID, space_id=second_space))
    assert resp.status_code == 200, f'Space {SECOND_PROJECT_ID} not found: {resp.text}'
    return SECOND_PROJECT_ID

# Доска в которой проверяются доступы для разных ролей
@pytest.fixture(scope='session')
def main_board(main_client, main_space):
    assert MAIN_BOARD_ID, 'Не задана переменная окружения MAIN_BOARD_ID'
    resp = main_client.post(**get_board_endpoint(board_id=MAIN_BOARD_ID, space_id=main_space))
    assert resp.status_code == 200, f'Space {MAIN_BOARD_ID} not found: {resp.text}'
    return MAIN_BOARD_ID

@pytest.fixture(scope='session')
def second_board(main_client, second_space):
    assert SECOND_BOARD_ID,'Не задана переменная окружения SECOND_BOARD_ID'
    resp = main_client.post(**get_board_endpoint(board_id=SECOND_BOARD_ID, space_id=second_space))
    assert resp.status_code == 200, f'Space {SECOND_BOARD_ID} not found: {resp.text}'
    return SECOND_BOARD_ID

# Доска с 10.000 тасок в main_space
@pytest.fixture(scope='session')
def board_with_10000_tasks(main_client, main_space):
    assert BOARD_WITH_TASKS, 'Не задана переменная окружения MAIN_BOARD_ID'
    resp = main_client.post(**get_board_endpoint(board_id=BOARD_WITH_TASKS, space_id=main_space))
    assert resp.status_code == 200, f'Board {BOARD_WITH_TASKS} not found: {resp.text}'
    return BOARD_WITH_TASKS

# Доска в которой заготовлены таски для разных сценариев
# (участвует в тестировании: creator, parentTask)
@pytest.fixture(scope='session')
def board_with_tasks(main_client, main_space):
    assert BOARD_FOR_TEST, 'Не задана переменная окружения MAIN_BOARD_ID'
    resp = main_client.post(**get_board_endpoint(board_id=BOARD_FOR_TEST, space_id=main_space))
    assert resp.status_code == 200, f'Space {MAIN_BOARD_ID} not found: {resp.text}'
    return BOARD_FOR_TEST


# Возвращает tasks_ids с board_with_tasks == 10.000 тасок в main_space
@pytest.fixture(scope='session')
def task_id_list(owner_client, main_space, board_with_10000_tasks):
    resp = owner_client.post(**get_tasks_endpoint(
        space_id=main_space,
        board=board_with_10000_tasks,
        limit=30
    ))
    assert resp.status_code == 200
    payload = resp.json().get("payload", {})
    tasks = payload.get("tasks", [])
    assert isinstance(tasks, list), "payload['tasks'] должен быть списком"

    ids = [t.get("_id") for t in tasks if isinstance(t, dict)]
    return [i for i in ids if i]

@pytest.fixture(scope='session')
def main_personal(main_client, main_space):
    """Возвращает персональные ID участников пространства по ролям."""
    response = main_client.post(**get_space_members_endpoint(space_id=main_space))
    response.raise_for_status()

    members = response.json()['payload']['members']
    roles = ['owner', 'manager', 'member', 'guest', 'main']

    # Собираем _id участников для каждой роли по имени (или другому признаку)
    member_id = {role: [m['_id'] for m in members if m.get('fullName') == role] for role in roles}
    return member_id

@pytest.fixture(scope='session')
def random_main_personal_id(main_personal: dict) -> str:
    """Возвращает случайный ID из словаря main_personal (из всех ролей)."""
    ids = [member_id for ids_by_role in main_personal.values() for member_id in ids_by_role]
    return random.choice(ids)

# Фикстура: создает временный спейс и возвращает member_id после прохождения тестов удаляет этот временный спейс
@pytest.fixture(scope='session')
def temp_member(main_client, temp_space):
    response = main_client.post(**get_space_members_endpoint(space_id=temp_space))
    response.raise_for_status()

    data = response.json()['payload']
    member_id = data['members'][0]['_id']

    yield member_id

@pytest.fixture(scope='session')
def temp_member_profile(main_client, temp_space):
    """Получение id пользователя который создает задачу"""
    resp = main_client.post(**get_profile_endpoint(space_id=temp_space))
    resp.raise_for_status()
    return resp.json()["payload"]["profile"]["memberId"]


# Фикстура: создает временный спейс и после прохождения тестов удаляет этот временный спейс
@pytest.fixture(scope='session')
def temp_space(main_client):
    name = generate_space_name()
    response = main_client.post(**create_space_endpoint(name=name))
    assert response.status_code == 200
    space_id = response.json()['payload']['space']['_id']

    yield space_id

    main_client.post(**remove_space_endpoint(space_id=space_id))


@pytest.fixture(scope='session')
def temp_project(main_client, temp_space):
    """Создаёт проект, который используется во всех тестах модуля."""
    name = generate_project_name()
    slug = generate_slug()
    common_kwargs = {'color': 'blue', 'icon': 'Dot', 'description': 'temporary project', 'space_id': temp_space}
    response = main_client.post(**create_project_endpoint(name=name, slug=slug, **common_kwargs))
    assert response.status_code == 200
    yield response.json()['payload']['project']['_id']


@pytest.fixture(scope='session')
def temp_board(main_client, temp_project, temp_space):
    """
    Создаёт временную борду в указанном проекте и спейсе.
    """
    board_name = generate_board_name()
    payload = create_board_endpoint(
        name=board_name,
        temp_project=temp_project,
        space_id=temp_space,
        groups=DEFAULT_BOARD_GROUPS,
        typesList=[],
        customFields=[],
    )
    response = main_client.post(**payload)
    assert response.status_code == 200

    yield response.json()['payload']['board']['_id']

@pytest.fixture
def temp_task(main_client, temp_space, temp_board):
    """
    Фикстура для создания временной задачи перед тестом и её удаления после теста.
    Возвращает ID созданной задачи.
    """
    task_name = "Temp task"

    create_resp = main_client.post(
        **create_task_endpoint(
            space_id=temp_space,
            board=temp_board,
            name=task_name
        ))
    assert create_resp.status_code == 200, f"Ошибка создания задачи в фикстуре: {create_resp.text}"
    task_id = create_resp.json()['payload']['task']['_id']

    # Передаем ID задачи в сам тест
    yield task_id

    with allure.step("Teardown [Fixture]: Удаление временной задачи"):
        delete_resp = main_client.post(
            **delete_task_endpoint(
                space_id=temp_space,
                task_id=task_id
            )
        )
        # Вместо жесткого assert == 200, мы допускаем, что задача уже удалена или конвертирована
        if delete_resp.status_code not in (200, 400, 404):
            pytest.fail(f"Ошибка при удалении задачи в фикстуре: {delete_resp.text}")



@pytest.fixture
def temp_task_on_board_with_tasks(main_client, main_space, board_with_tasks):
    """
    Фикстура для создания временной задачи перед тестом и её удаления после теста.
    Возвращает ID созданной задачи.
    """
    task_name = "Temp task for tests task events"

    create_resp = main_client.post(
        **create_task_endpoint(
            space_id=main_space,
            board=board_with_tasks,
            name=task_name
        ))
    assert create_resp.status_code == 200, f"Ошибка создания задачи в фикстуре: {create_resp.text}"
    task_id = create_resp.json()['payload']['task']['_id']

    # Передаем ID задачи в сам тест
    yield task_id

    with allure.step("Teardown [Fixture]: Удаление временной задачи"):
        delete_resp = main_client.post(
            **delete_task_endpoint(
                space_id=main_space,
                task_id=task_id
            )
        )
        # Вместо жесткого assert == 200, мы допускаем, что задача уже удалена или конвертирована
        if delete_resp.status_code not in (200, 400, 404):
            pytest.fail(f"Ошибка при удалении задачи в фикстуре: {delete_resp.text}")


@pytest.fixture(scope='session')
def temp_access_group(main_client, temp_space):
    """
    Создает временную группу доступа в temp_space.
    """
    group_name = f"Test Group {uuid.uuid4().hex[:4]}"
    group_desc = "Temporary access group for testing"

    response = main_client.post(**create_access_group_endpoint(
        space_id=temp_space,
        name=group_name,
        description=group_desc
    ))
    assert response.status_code == 200, f"Ошибка создания группы: {response.text}"

    group_id = response.json().get("payload", {}).get("accessGroup", {}).get("_id")
    assert group_id, "В ответе не вернулся _id созданной группы доступа"

    yield group_id


@pytest.fixture
def temp_milestone_on_board_with_tasks(owner_client, main_space, board_with_tasks, main_project):
    """
    Фикстура для создания временного майлстоуна перед тестом и его Архивация после теста.
    Возвращает ID созданного майлстоуна.
    """
    with allure.step("Setup [Fixture]: Создание временного майлстоуна"):
        milestone_name = "Temp Milestone " + generate_date()
        create_resp = owner_client.post(
            **create_milestone_endpoint(
                space_id=main_space,
                board=board_with_tasks,
                name=milestone_name,
                project=main_project
            )
        )
        assert create_resp.status_code == 200, f"Ошибка создания майлстоуна в фикстуре: {create_resp.text}"
        milestone_id = create_resp.json()['payload']['milestone']['_id']

    # Передаем ID майлстоуна в тест
    yield milestone_id

    with allure.step("Teardown [Fixture]: Архивация временного майлстоуна"):
        archive_resp = owner_client.post(
            **archive_milestone_endpoint(
                space_id=main_space,
                milestone_id=milestone_id
            )
        )
        assert archive_resp.status_code == 200, f"Ошибка при архивации майлстоуна в фикстуре: {archive_resp.text}"


@pytest.fixture(scope="session")
def get_invite_code(main_client):
    """
    Фабрика для получения кода приглашения.
    Принимает клиента, которого нужно пригласить, его email и ID пространства.
    """

    def _get_invite_code(client_to_invite, email_to_invite, space_id):
        # 1. Отправляем инвайт от лица owner'a (main_client)
        invite_resp = main_client.post(**invite_to_space_endpoint(
            space_id=space_id,
            email=email_to_invite,
            space_access="Member"
        ))

        # Игнорируем ошибку, если пользователь уже приглашен/состоит в пространстве
        if invite_resp.status_code != 200:
            error_code = invite_resp.json().get("error", {}).get("code")
            assert error_code in ["UserAlreadySpaceMember", "UserAlreadyInvited"], f"Ошибка инвайта: {invite_resp.text}"

        # 2. Запрашиваем спейсы от лица приглашенного клиента
        spaces_resp = client_to_invite.post(**get_spaces_endpoint())
        assert spaces_resp.status_code == 200

        spaces = spaces_resp.json().get('payload', {}).get('spaces', [])
        target_space = next((s for s in spaces if s.get('_id') == space_id), None)
        assert target_space is not None, f"Пространство {space_id} не найдено в списке инвайтов"

        return target_space.get('inviteCode')

    return _get_invite_code


@pytest.fixture(scope="session")
def space_with_members(
        request,
        main_client,
        owner_client,
        manager_client,
        member_client,
        guest_client
):
    """
    Создает временное пространство от имени main_client, приглашает туда
    owner, manager, member, guest с соответствующими ролями.
    Возвращает space_id.
    После прохождения тестов пространство удаляется, и проверяется, что оно больше
    недоступно ни одному из клиентов.
    """
    clients_to_invite = {
        "Owner": owner_client,
        "Manager": manager_client,
        "Member": member_client,
        "Guest": guest_client
    }

    # 1. main_client создает временное пространство
    with allure.step("Создание временного пространства (temp_space_with_members)"):
        name = generate_space_name()
        create_resp = main_client.post(**create_space_endpoint(name=name))
        assert create_resp.status_code == 200, f"Ошибка при создании пространства: {create_resp.text}"
        space_id = create_resp.json()['payload']['space']['_id']

    # 2. main_client приглашает всех пользователей и они подтверждают инвайт
    with allure.step("Приглашение пользователей и подтверждение инвайтов"):
        for role, client in clients_to_invite.items():
            client_email = settings.USERS[role.lower()]['email']
            client_password = settings.USERS[role.lower()]['password']

            # Отправка инвайта
            invite_resp = main_client.post(**invite_to_space_endpoint(
                space_id=space_id,
                email=client_email,
                space_access=role
            ))
            assert invite_resp.status_code == 200, f"Не удалось пригласить {role}: {invite_resp.text}"

            # Получение списка спейсов клиента для поиска inviteCode
            spaces_resp = client.post(**get_spaces_endpoint())
            assert spaces_resp.status_code == 200, f"Не удалось получить список спейсов для {role}: {spaces_resp.text}"

            spaces = spaces_resp.json().get('payload', {}).get('spaces', [])
            target_space = next((s for s in spaces if s.get('_id') == space_id), None)

            assert target_space, f"Пространство {space_id} не найдено у {role}"
            invite_code = target_space.get('inviteCode')
            assert invite_code, f"У пространства {space_id} нет inviteCode для пользователя {role}"

            # Подтверждение инвайта
            confirm_resp = client.post(**confirm_space_invite_endpoint(
                code=invite_code,
                full_name=f"Test {role}",
                password=client_password,
                termsAccepted=True
            ))
            assert confirm_resp.status_code == 200, f"Ошибка подтверждения инвайта для {role}: {confirm_resp.text}"

    # Передаем управление тестам
    yield space_id

    # 3. Teardown: удаляем пространство
    with allure.step("Удаление временного пространства"):
        remove_resp = main_client.post(**remove_space_endpoint(space_id=space_id))
        assert remove_resp.status_code == 200, f"Ошибка при удалении пространства: {remove_resp.text}"

    # 4. Проверяем, что спейс пропал у всех приглашенных клиентов и у создателя
    all_clients = [main_client] + list(clients_to_invite.values())
    with allure.step("Проверка, что удаленное пространство недоступно у всех клиентов"):
        for client in all_clients:
            check_resp = client.post(**get_space_endpoint(space_id=space_id))
            # Ожидаем, что пространство не будет найдено (статус код не 200, статус код == 400)
            assert check_resp.status_code != 200, (
                f"Уязвимость! Пространство {space_id} всё ещё доступно для одного из клиентов "
                f"после удаления. Ответ: {check_resp.text}"
            )



@pytest.fixture(scope='session')
def foreign_space(guest_client):
    """Создаёт space от имени другого пользователя"""
    response = guest_client.post(**create_space_endpoint(name='foreign space'))
    assert response.status_code == 200
    space_id = response.json()['payload']['space']['_id']

    yield space_id

    # Очистка
    guest_client.post(**remove_space_endpoint(space_id=space_id))


@pytest.fixture(scope='module')
def space_id_module(main_client):
    client = main_client
    name = generate_space_name()
    response = client.post(**create_space_endpoint(name=name))
    assert response.status_code == 200
    space_id = response.json()['payload']['space']['_id']

    yield space_id

    client.post(**remove_space_endpoint(space_id=space_id))


@pytest.fixture(scope='module')
def space_id_(second_main_client):
    """
    спейс созданный для тестирования инвайтов,
    т.к. есть ограничение и на количество инвайтов от пользователя (10/час),
    и на количество участников в одном спейсе (не больше 10 для бесплатного тарифа)
    """
    client = second_main_client
    name = generate_space_name()
    response = client.post(**create_space_endpoint(name=name))
    assert response.status_code == 200
    space_id = response.json()['payload']['space']['_id']

    yield space_id

    client.post(**remove_space_endpoint(space_id=space_id))

@pytest.fixture(scope='module')
def project_id_module(main_client, space_id_module):
    name = generate_project_name()
    slug = generate_slug()
    common_kwargs = {'color': 'blue', 'icon': 'Dot', 'description': 'temporary project', 'space_id': space_id_module}
    response = main_client.post(**create_project_endpoint(name=name, slug=slug, **common_kwargs))
    assert response.status_code == 200
    project_id = response.json()['payload']['project']['_id']

    yield project_id

@pytest.fixture(scope='module')
def board_id_module(main_client, project_id_module, space_id_module):
    board_name = generate_board_name()
    payload = create_board_endpoint(
        name=board_name,
        temp_project=project_id_module,
        space_id=space_id_module,
        groups=DEFAULT_BOARD_GROUPS,
        typesList=[],
        customFields=[],
    )
    response = main_client.post(**payload)
    assert response.status_code == 200

    yield response.json()['payload']['board']['_id']


@pytest.fixture(scope='module')
def group_in_module(main_client, space_id_module):
    """
    Создает временную группу доступа в space_id_module.
    """
    group_name = f"Test Group {uuid.uuid4().hex[:4]}"
    group_desc = "Temporary access group for testing"

    response = main_client.post(**create_access_group_endpoint(
        space_id=space_id_module,
        name=group_name,
        description=group_desc
    ))
    assert response.status_code == 200, f"Ошибка создания группы: {response.text}"

    group_id = response.json().get("payload", {}).get("accessGroup", {}).get("_id")
    assert group_id, "В ответе не вернулся _id созданной группы доступа"

    yield group_id

@pytest.fixture(scope='module')
def member_id_module(main_client, space_id_module):
    response = main_client.post(**get_space_members_endpoint(space_id=space_id_module))
    response.raise_for_status()

    data = response.json()['payload']
    member_id = data['members'][0]['_id']

    yield member_id


@pytest.fixture(scope='function')
def space_id_function(owner_client):
    client = owner_client
    name = generate_space_name()
    response = client.post(**create_space_endpoint(name=name))
    assert response.status_code == 200
    space_id = response.json()['payload']['space']['_id']

    yield space_id

    client.post(**remove_space_endpoint(space_id=space_id))


@pytest.fixture(scope='function')
def project_id_function(owner_client, space_id_function):
    name = generate_project_name()
    slug = generate_slug()
    common_kwargs = {'color': 'blue', 'icon': 'Dot', 'description': 'temporary project', 'space_id': space_id_function}
    response = owner_client.post(**create_project_endpoint(name=name, slug=slug, **common_kwargs))
    assert response.status_code == 200
    project_id = response.json()['payload']['project']['_id']

    yield project_id


@pytest.fixture(scope='function')
def member_id_function(owner_client, space_id_function):
    response = owner_client.post(**get_space_members_endpoint(space_id=space_id_function))
    response.raise_for_status()

    data = response.json()['payload']
    member_id = data['members'][0]['_id']

    yield member_id


@pytest.fixture
def temp_document(main_client, request, kind, kind_id_fixture):
    kind_id = request.getfixturevalue(kind_id_fixture)
    space_id = request.getfixturevalue('temp_space')

    response = main_client.post(
        **create_document_endpoint(
            kind=kind,
            kind_id=kind_id,
            space_id=space_id,
            title='Документ для дублирования',
        )
    )

    assert response.status_code == 200
    doc_id = response.json()['payload']['document']

    yield doc_id

    main_client.post(**archive_document_endpoint(space_id=space_id, document_id=doc_id))


@pytest.fixture
def create_main_documents(request, main_space):
    """
    Фикстура для создания тестовых документов разными ролями в main_space
    """
    created_docs = []

    def _create_docs(kind, kind_id, creator_roles):
        """
        Внутренняя функция для создания документов
        Args:
            kind (str): Тип документа (Space/Project/Member)
            kind_id (str): ID контейнера (space_id/project_id/member_id)
            creator_roles (dict): Словарь {fixture_name: role_name} для создания документов
        """
        with allure.step(f'Создание тестовых документов в {kind} разными ролями'):
            for creator_fixture, creator_role in creator_roles.items():
                creator_client = request.getfixturevalue(creator_fixture)

                with allure.step(f'Создание документа пользователем {creator_role}'):
                    title = f'{kind} doc by {creator_role} {datetime.datetime.now().strftime("%Y.%m.%d_%H:%M:%S")}'
                    create_resp = creator_client.post(
                        **create_document_endpoint(kind=kind, kind_id=kind_id, space_id=main_space, title=title)
                    )
                    assert create_resp.status_code == 200, (
                        f'Ошибка при создании документа пользователем {creator_role}: '
                        f'статус {create_resp.status_code}'
                    )

                    doc_id = create_resp.json()['payload']['document']['_id']
                    created_docs.append(
                        {'id': doc_id, 'title': title, 'creator': creator_client, 'creator_role': creator_role}
                    )
        return created_docs

    yield _create_docs

    # Очистка тестовых данных
    with allure.step('Очистка тестовых данных'):
        for doc in created_docs:
            with allure.step(f'Удаление документа "{doc["title"]}" (создан {doc["creator_role"]})'):
                doc['creator'].post(**archive_document_endpoint(space_id=main_space, document_id=doc['id']))


@pytest.fixture(scope='session')
def main_space_doc():
    """
    Возвращает ID документа MAIN_SPACE_DOC_ID из переменных окружения.
    """
    doc_id = os.getenv('MAIN_SPACE_DOC_ID')
    assert doc_id, 'Переменная окружения MAIN_SPACE_DOC_ID не задана или пуста'
    return doc_id


@pytest.fixture(scope='session')
def main_project_doc():
    """
    Возвращает ID документа MAIN_PROJECT_DOC_ID из переменных окружения.
    """
    doc_id = os.getenv('MAIN_PROJECT_DOC_ID')
    assert doc_id, 'Переменная окружения MAIN_PROJECT_DOC_ID не задана или пуста'
    return doc_id


@pytest.fixture(scope='session')
def main_personal_doc():
    """
    Возвращает ID документа MAIN_PERSONAL_DOC_ID из переменных окружения.
    """
    doc_id = os.getenv('MAIN_PERSONAL_DOC_ID')
    assert doc_id, 'Переменная окружения MAIN_PERSONAL_DOC_ID не задана или пуста'
    return doc_id
