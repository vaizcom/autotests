import allure
import pytest

pytestmark = [pytest.mark.backend]


@allure.parent_suite("History Service")
@allure.suite("GetHistory Access")
@allure.sub_suite("Negative: GetHistory — нет доступа к спейсу")
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
    Бек отклоняет на уровне проверки Current-Space-Id → 400 SpaceIdNotSpecified.
    """
    kind_id = request.getfixturevalue(kind_id_fixture)
    if isinstance(kind_id, list):
        kind_id = kind_id[0]

    allure.dynamic.title(f"GetHistory: foreign_client запрашивает kind='{kind}' → 400 SpaceIdNotSpecified")

    with allure.step(f"Отправляем POST /GetHistory: kind='{kind}' от имени foreign_client"):
        resp = foreign_client.post(
            path="/GetHistory",
            json={"kind": kind, "kindId": kind_id},
            headers={"Content-Type": "application/json", "Current-Space-Id": main_space},
        )

    with allure.step("Получаем 400 SpaceIdNotSpecified"):
        assert resp.status_code == 400
        assert resp.json()["error"]["code"] == "SpaceIdNotSpecified"
