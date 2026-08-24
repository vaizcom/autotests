import allure
import pytest

from config.settings import USERS, API_URL
from core.auth import get_token
from core.client import APIClient
from test_backend.data.endpoints.Space.space_endpoints import (
    create_space_endpoint,
    get_spaces_endpoint,
    remove_space_endpoint,
)
from test_backend.data.endpoints.invite.invite_endpoint import (
    invite_to_space_endpoint,
    confirm_space_invite_endpoint,
)
from test_backend.data.endpoints.member.member_endpoints import get_space_members_endpoint
from test_backend.data.endpoints.Project.project_endpoints import (
    create_project_endpoint,
    create_board_endpoint,
)
from test_backend.data.endpoints.Board.constants import DEFAULT_BOARD_GROUPS, typesList as DEFAULT_TYPES_LIST
from test_backend.data.endpoints.access_group.access_group_endpoints import (
    update_access_group_rights_endpoint,
)
from test_backend.data.endpoints.access_group.access_group_helpers import get_member_access_group
from config.generators import generate_slug

_SPACE_NAME = "_autotest_access_group_space"


# ─── helpers ──────────────────────────────────────────────────────────────────


def _invite_and_get_member(main_client, space_id, email, password, role):
    """
    Инвайтит существующего тестового пользователя в спейс и возвращает его member_id.

    Пользователь уже зарегистрирован в БД — OTP не нужен, инвайт подтверждается
    напрямую через пароль (confirm_space_invite_endpoint).

    Если пользователь уже в спейсе (повторный прогон) — инвайт вернёт ошибку,
    но member_id всё равно найдётся через GetSpaceMembers.
    """
    invite_resp = main_client.post(**invite_to_space_endpoint(
        space_id=space_id, email=email, space_access=role,
    ))
    if invite_resp.status_code == 200:
        user_key = next(k for k, v in USERS.items() if v["email"] == email)
        client = APIClient(base_url=API_URL, token=get_token(user_key))
        spaces_resp = client.post(**get_spaces_endpoint())
        assert spaces_resp.status_code == 200
        spaces = spaces_resp.json().get("payload", {}).get("spaces", [])
        target = next((s for s in spaces if s.get("_id") == space_id), None)
        assert target is not None, f"Спейс {space_id} не найден у пользователя {email}"
        confirm_resp = client.post(**confirm_space_invite_endpoint(
            code=target["inviteCode"],
            full_name=role,
            password=password,
            termsAccepted=True,
        ))
        assert confirm_resp.status_code == 200, f"Ошибка принятия инвайта: {confirm_resp.text}"

    members_resp = main_client.post(**get_space_members_endpoint(space_id=space_id))
    assert members_resp.status_code == 200
    members = members_resp.json()["payload"]["members"]
    member = next((m for m in members if m.get("email") == email), None)
    assert member is not None, f"Участник {email} не найден в спейсе"
    return member["_id"]


def _get_self_group_id(client, space_id, member_id):
    """
    Находит и возвращает _id selfAccessGroup для конкретного участника.

    selfAccessGroup — персональная группа доступа, создаётся автоматически
    при инвайте участника. Может создаваться асинхронно — делегируем ожидание
    в get_member_access_group, которая использует wait_until с таймаутом 10 с.
    """
    group = get_member_access_group(client, space_id, member_id)
    return group["_id"]


def _invite_member_with_access(main_client, space_id, project_id, board_id, email, password, role):
    """
    Инвайтит пользователя в спейс и явно выдаёт ему указанную роль на Project и Board.

    Бэкенд не наследует Space-уровень вниз при проверке прав на Project/Board:
    hasAccessLevelOrDie(EKind.Board, boardId) смотрит только boardAccesses[boardId].
    Поэтому после инвайта явно выдаём указанную роль на Project и Board через selfGroup.

    Возвращает member_id.
    """
    with allure.step(f"Setup: инвайтим {role} ({email}) в access_space"):
        member_id = _invite_and_get_member(main_client, space_id, email, password, role)

    self_group_id = _get_self_group_id(main_client, space_id, member_id)

    with allure.step(f"Setup: выдаём {role} явный доступ {role} на Project"):
        resp = main_client.post(**update_access_group_rights_endpoint(
            space_id=space_id, group_id=self_group_id,
            kind="Project", kind_id=project_id, level=role,
        ))
        assert resp.status_code == 200, f"Setup: не удалось выдать {role} на Project: {resp.text}"

    with allure.step(f"Setup: выдаём {role} явный доступ {role} на Board"):
        resp = main_client.post(**update_access_group_rights_endpoint(
            space_id=space_id, group_id=self_group_id,
            kind="Board", kind_id=board_id, level=role,
        ))
        assert resp.status_code == 200, f"Setup: не удалось выдать {role} на Board: {resp.text}"

    return member_id


# ─── fixtures ─────────────────────────────────────────────────────────────────


@pytest.fixture(scope="session")
def access_space(main_client):
    """
    Изолированный спейс для тестов управления правами доступа (UpdateAccessGroupRights).

    Создаётся отдельно от других тестовых спейсов — все изменения прав происходят
    только здесь и не влияют на main_space и другие тест-сьюты.

    Перед созданием ищет и удаляет спейс с тем же именем — защита от незачищенных прогонов.
    Удаляется вместе со всеми дочерними сущностями после завершения сессии.

    Возвращает: {"space_id": str, "name": str}
    """
    resp = main_client.post(**get_spaces_endpoint())
    if resp.status_code == 200:
        for space in resp.json().get("payload", {}).get("spaces", []):
            if space.get("name") == _SPACE_NAME:
                main_client.post(**remove_space_endpoint(space_id=space["_id"]))

    with allure.step(f"Setup: создаём спейс '{_SPACE_NAME}'"):
        resp = main_client.post(**create_space_endpoint(name=_SPACE_NAME))
        assert resp.status_code == 200, f"Setup: не удалось создать спейс: {resp.text}"
        space_id = resp.json()["payload"]["space"]["_id"]

    yield {"space_id": space_id, "name": _SPACE_NAME}

    main_client.post(**remove_space_endpoint(space_id=space_id))


@pytest.fixture(scope="session")
def access_project(main_client, access_space):
    """
    Проект внутри access_space.

    Нужен для позитивных сценариев (Manager меняет права на Project)
    и для негативных (Member/Guest пытается поменять права на Project).
    Удаляется каскадно вместе с access_space.

    Возвращает: {"project_id": str, "name": str}
    """
    space_id = access_space["space_id"]
    name = "_autotest_access_project"
    slug = generate_slug()
    with allure.step(f"Setup: создаём проект '{name}'"):
        resp = main_client.post(**create_project_endpoint(
            name=name, slug=slug, color="blue", icon="Dot",
            description="access group test project", space_id=space_id,
        ))
        assert resp.status_code == 200, f"Setup: не удалось создать проект: {resp.text}"
        project_id = resp.json()["payload"]["project"]["_id"]
    yield {"project_id": project_id, "name": name}


@pytest.fixture(scope="session")
def access_board(main_client, access_space, access_project):
    """
    Борда внутри access_project.

    Нужна для тестов прав на уровне Board — отдельно от Project,
    т.к. права на борду и проект проверяются независимо.
    Удаляется каскадно вместе с access_space.

    Возвращает: {"board_id": str, "name": str}
    """
    space_id = access_space["space_id"]
    project_id = access_project["project_id"]
    name = "_autotest_access_board"
    with allure.step(f"Setup: создаём борду '{name}'"):
        resp = main_client.post(**create_board_endpoint(
            name=name, temp_project=project_id, space_id=space_id,
            groups=DEFAULT_BOARD_GROUPS, typesList=DEFAULT_TYPES_LIST, customFields=[],
        ))
        assert resp.status_code == 200, f"Setup: не удалось создать борду: {resp.text}"
        board_id = resp.json()["payload"]["board"]["_id"]
    yield {"board_id": board_id, "name": name}


@pytest.fixture(scope="session")
def access_manager(main_client, access_space, access_project, access_board):
    """
    Участник с ролью Manager в access_space с явным Manager-доступом на Project и Board.

    Бэкенд не наследует Space-уровень вниз при проверке прав на Project/Board:
    hasAccessLevelOrDie(EKind.Board, boardId) смотрит только boardAccesses[boardId].
    Поэтому после инвайта явно выдаём Manager на Project и Board через selfGroup.

    Субъект позитивных сценариев — вызывает UpdateAccessGroupRights на Space/Project/Board.
    Его selfGroup нужна для теста CreatorAccessChangeNotAllowed.

    Возвращает: {"member_id": str, "email": str}
    """
    space_id = access_space["space_id"]
    project_id = access_project["project_id"]
    board_id = access_board["board_id"]
    email = USERS["manager"]["email"]
    password = USERS["manager"]["password"]

    member_id = _invite_member_with_access(
        main_client, space_id, project_id, board_id, email, password, "Manager",
    )
    yield {"member_id": member_id, "email": email}


@pytest.fixture(scope="session")
def access_member(main_client, access_space, access_project, access_board):
    """
    Участник с ролью Member в access_space с явным Member-доступом на Project и Board.

    Бэкенд не наследует Space-уровень вниз на Project/Board — доступ выдаётся явно
    через selfGroup, аналогично access_manager.

    Используется в негативных сценариях — Member не имеет права вызывать
    UpdateAccessGroupRights, должен получать AccessDenied.
    Его selfGroup нужна для тестов смены прав конкретного участника.

    Возвращает: {"member_id": str, "email": str}
    """
    space_id = access_space["space_id"]
    project_id = access_project["project_id"]
    board_id = access_board["board_id"]
    email = USERS["member"]["email"]
    password = USERS["member"]["password"]

    member_id = _invite_member_with_access(
        main_client, space_id, project_id, board_id, email, password, "Member",
    )
    yield {"member_id": member_id, "email": email}


@pytest.fixture(scope="session")
def access_member_self_group_id(main_client, access_space, access_member):
    """
    _id selfAccessGroup мембера в access_space.

    Нужен для тестов смены прав конкретного участника через его персональную группу:
    Manager меняет права Member на Project/Board.
    """
    return _get_self_group_id(main_client, access_space["space_id"], access_member["member_id"])
