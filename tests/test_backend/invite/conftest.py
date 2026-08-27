import uuid

import allure
import pytest

from config import settings
from config.generators import generate_space_name, generate_project_name, generate_slug, generate_board_name
from core.response_utils import short_resp
from test_backend.data.endpoints.Board.constants import DEFAULT_BOARD_GROUPS
from test_backend.data.endpoints.Project.project_endpoints import create_project_endpoint, create_board_endpoint
from test_backend.data.endpoints.Space.space_endpoints import (
    create_space_endpoint, remove_space_endpoint, get_space_endpoint, get_spaces_endpoint,
)
from test_backend.data.endpoints.access_group.access_group_endpoints import create_access_group_endpoint
from test_backend.data.endpoints.invite.invite_endpoint import invite_to_space_endpoint, confirm_space_invite_endpoint


# ── Rate-limit: skip remaining invite tests on 429 ─────────────────────────

_rate_limited = False
_rate_limit_retry_after = None


def _rate_limit_message():
    msg = "429 — рейт-лимит исчерпан (20 инвайтов в час на пользователя), инвайт-тесты пропущены"
    if _rate_limit_retry_after:
        msg += f". Повторить после {_rate_limit_retry_after}"
    return msg


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    global _rate_limited, _rate_limit_retry_after
    outcome = yield
    report = outcome.get_result()
    if report.failed and "429" in str(report.longrepr):
        _rate_limited = True
        if _rate_limit_retry_after is None:
            from datetime import datetime, timedelta, timezone
            retry_utc = datetime.now(timezone.utc) + timedelta(hours=1)
            retry_msk = retry_utc + timedelta(hours=3)
            _rate_limit_retry_after = f"{retry_utc.strftime('%H:%M')} (UTC) / {retry_msk.strftime('%H:%M')} (MSK)"
        report.longrepr = str(report.longrepr) + f"\n\n>>> {_rate_limit_message()}"


@pytest.fixture(autouse=True)
def _skip_if_rate_limited():
    if _rate_limited:
        pytest.skip(_rate_limit_message())


# ── Invite fixtures ──────────────────────────────────────────────────────────

@pytest.fixture(scope="session")
def get_invite_code(second_main_client):
    """
    Фабрика для получения кода приглашения.
    Принимает клиента, которого нужно пригласить, его email и ID пространства.
    """

    def _get_invite_code(client_to_invite, email_to_invite, space_id):
        # 1. Отправляем инвайт от лица second_main_client (чтобы не упереться в рейт-лимит main)
        invite_resp = second_main_client.post(**invite_to_space_endpoint(
            space_id=space_id,
            email=email_to_invite,
            space_access="Member"
        ))

        # Игнорируем ошибку, если пользователь уже приглашен/состоит в пространстве
        if invite_resp.status_code != 200:
            error_code = invite_resp.json().get("error", {}).get("code")
            assert error_code in ["UserAlreadySpaceMember", "UserAlreadyInvited"], f"Ошибка инвайта: {short_resp(invite_resp)}"

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
        assert create_resp.status_code == 200, f"Ошибка при создании пространства: {short_resp(create_resp)}"
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
            assert invite_resp.status_code == 200, f"Не удалось пригласить {role}: {short_resp(invite_resp)}"

            # Получение списка спейсов клиента для поиска inviteCode
            spaces_resp = client.post(**get_spaces_endpoint())
            assert spaces_resp.status_code == 200, f"Не удалось получить список спейсов для {role}: {short_resp(spaces_resp)}"

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
            assert confirm_resp.status_code == 200, f"Ошибка подтверждения инвайта для {role}: {short_resp(confirm_resp)}"

    # Передаем управление тестам
    yield space_id

    # 3. Teardown: удаляем пространство (без assert — чтобы не ронять всю сессию)
    with allure.step("Удаление временного пространства"):
        if space_id:
            remove_resp = main_client.post(**remove_space_endpoint(space_id=space_id))
            if remove_resp.status_code != 200:
                allure.attach(
                    f"Не удалось удалить пространство {space_id}: {short_resp(remove_resp)}",
                    "Teardown warning", "text/plain",
                )


@pytest.fixture(scope='module')
def second_space_id(second_main_client):
    """Спейс от second_main_client — для инвайт-тестов (изоляция от рейт-лимита main)."""
    client = second_main_client
    name = generate_space_name()
    response = client.post(**create_space_endpoint(name=name))
    assert response.status_code == 200
    space_id = response.json()['payload']['space']['_id']

    yield space_id

    client.post(**remove_space_endpoint(space_id=space_id))


@pytest.fixture(scope='module')
def second_project_id(second_main_client, second_space_id):
    """Проект в second_space_id (owned by second_main_client) — для инвайт-тестов."""
    name = generate_project_name()
    slug = generate_slug()
    response = second_main_client.post(**create_project_endpoint(
        name=name, slug=slug, color='blue', icon='Dot',
        description='invite test project', space_id=second_space_id
    ))
    assert response.status_code == 200
    yield response.json()['payload']['project']['_id']


@pytest.fixture(scope='module')
def second_board_id(second_main_client, second_project_id, second_space_id):
    """Борда в second_space_id (owned by second_main_client) — для инвайт-тестов."""
    board_name = generate_board_name()
    response = second_main_client.post(**create_board_endpoint(
        name=board_name, temp_project=second_project_id, space_id=second_space_id,
        groups=DEFAULT_BOARD_GROUPS, typesList=[], customFields=[]
    ))
    assert response.status_code == 200
    yield response.json()['payload']['board']['_id']


@pytest.fixture(scope='module')
def second_group_id(second_main_client, second_space_id):
    """Группа доступа в second_space_id (owned by second_main_client) — для инвайт-тестов."""
    group_name = f"Test Group {uuid.uuid4().hex[:4]}"
    response = second_main_client.post(**create_access_group_endpoint(
        space_id=second_space_id, name=group_name, description="Invite test group"
    ))
    assert response.status_code == 200, f"Ошибка создания группы: {short_resp(response)}"
    yield response.json().get("payload", {}).get("accessGroup", {}).get("_id")
