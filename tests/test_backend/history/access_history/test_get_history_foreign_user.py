import allure
import pytest

from core.response_utils import short_resp
from test_backend.data.endpoints.History.get_history_endpoint import get_history_endpoint

pytestmark = [pytest.mark.backend]


@allure.parent_suite("History Service")
@allure.suite("GetHistory Access")
@allure.sub_suite("Без доступа к спейсу")
@pytest.mark.parametrize("kind,kind_id_fixture", [
    ("Space",     "main_space"),
    ("Project",   "main_project"),
    ("Task",      "task_id_list"),
    ("Document",  "main_space_doc"),
    ("Milestone", "temp_milestone_on_temp_board"),
], ids=["space", "project", "task", "document", "milestone"])
def test_get_history_foreign_user(request, foreign_client, main_space, kind, kind_id_fixture):
    """
    Пользователь без доступа к спейсу не может получить историю ни для одного kind.
    foreign_client не является участником main_space.
    Бек отклоняет на уровне проверки Current-Space-Id → 400 (SpaceIdNotSpecified).
    """
    kind_id = request.getfixturevalue(kind_id_fixture)
    if isinstance(kind_id, list):
        kind_id = kind_id[0]

    allure.dynamic.title(f"Пользователь без доступа: {kind} → 400")

    with allure.step("Участник: foreign_client (не является участником спейса)"):
        pass

    with allure.step(f"Отправляем POST /GetHistory: kind='{kind}' от имени foreign_client"):
        resp = foreign_client.post(
            path="/GetHistory",
            json={"kind": kind, "kindId": kind_id},
            headers={"Content-Type": "application/json", "Current-Space-Id": main_space},
        )

    with allure.step("Получаем 400 (SpaceIdNotSpecified)"):
        assert resp.status_code == 400, f"Ожидали 400 (SpaceIdNotSpecified), получили: {short_resp(resp)}"
        assert resp.json()["error"]["code"] == "SpaceIdNotSpecified"


@allure.parent_suite("History Service")
@allure.suite("GetHistory Access")
@allure.sub_suite("Без доступа к спейсу")
def test_cross_space_direct_access_denied(main_client, main_space, foreign_space):
    """
    main_client находится в main_space, но НЕ в foreign_space.
    Запрос истории foreign_space → 403.
    """
    allure.dynamic.title("Запрос к спейсу без доступа → 403")

    with allure.step("Участник: main_client (main_space — да, foreign_space — нет)"):
        pass

    with allure.step("main_client запрашивает GetHistory kind='Space' для foreign_space → 403"):
        resp = main_client.post(
            **get_history_endpoint(space_id=main_space, kind="Space", kind_id=foreign_space)
        )

    with allure.step("Получаем 403 (Forbidden)"):
        assert resp.status_code == 403, f"Ожидали 403, получили: {short_resp(resp)}"
