import allure
import pytest

from test_backend.data.endpoints.Task.task_endpoints import edit_task_endpoint

pytestmark = [pytest.mark.backend]


@allure.title("Edit Task: Проверка редактирования поля 'coverImage'")
def test_edit_task_only_cover_image(owner_client, main_space, make_task_in_main, main_board, main_project):
    """
    Проверяет успешное редактирование поля 'coverImage' задачи.
    """
    initial_task_data = make_task_in_main({"name": "Edit Task with cover image"})
    task_id = initial_task_data.get("_id")
    initial_name = initial_task_data.get("name")
    initial_cover_ar = initial_task_data.get("coverAR")
    initial_cover_color = initial_task_data.get("coverColor")
    initial_cover_url = initial_task_data.get("coverUrl")

    new_cover_image = "69440700136ecd5583dae514"  # Пример существующего coverImage ID

    with allure.step(f"Отправляем запрос EditTask для редактирования только coverImage задачи {task_id}"):
        edit_payload = {"coverImage": new_cover_image}
        resp = owner_client.post(**edit_task_endpoint(space_id=main_space, task_id=task_id, **edit_payload))

    with allure.step("Проверяем успешный статус и обновленное coverImage"):
        assert resp.status_code == 200, f"Ожидался статус 200, получен {resp.status_code}"
        task = resp.json()["payload"]["task"]
        assert task.get("_id") == task_id
        assert task.get("coverAR") is not None, "coverAR должен быть установлен"
        assert task.get("coverColor") is not None, "coverColor должен быть установлен"
        assert task.get("coverUrl") is not None, "coverUrl должен быть установлен"
        assert task.get("name") == initial_name, "Другие поля не должны были измениться"
        # Проверяем, что coverImage изменился по сравнению с изначальным (если был)
        # Учитывая, что initial_task_data может не иметь coverImage,
        # проверяем, что поля обложки теперь установлены.
        if initial_cover_ar is not None: # Если изначально была обложка
            assert task.get("coverAR") != initial_cover_ar
        if initial_cover_color is not None:
            assert task.get("coverColor") != initial_cover_color
        if initial_cover_url is not None:
            assert task.get("coverUrl") != initial_cover_url
        # assert_task_payload(task, main_board, main_project)
