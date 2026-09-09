import re
import time

from api.board.board_endpoints import get_board_endpoint
from api.project.project_endpoints import get_project_endpoint
from api.task.task_endpoints import delete_task_endpoint


def validate_hrid(client, space_id, project_id, task_hrid):
    """Проверяет, что hrid соответствует формату <slug>-<число>."""
    assert hasattr(client, 'post'), "Клиент должен быть экземпляром APIClient"

    response = client.post(**get_project_endpoint(project_id=project_id, space_id=space_id))
    response.raise_for_status()

    project_slug = response.json().get("payload", {}).get("project", {}).get("slug", None)
    assert project_slug, "Ошибка: не удалось получить slug проекта"

    hrid_pattern = rf"^{project_slug}-\d+$"
    assert re.match(hrid_pattern, task_hrid), f"Поле 'hrid' имеет некорректный формат: {task_hrid}"


def assert_task_keys(task, expected_keys):
    """Проверяет, что словарь задачи содержит ровно ожидаемые ключи."""
    actual = set(task.keys())
    extra = actual - expected_keys
    missing = expected_keys - actual
    info_msg = (
        f"\nВсе ключи в ответе: {sorted(list(actual))}\n"
        f"Ожидались ключи:    {sorted(list(expected_keys))}\n"
    )
    assert not extra, f"Есть лишние ключи в задаче: {sorted(list(extra))}" + info_msg
    assert not missing, f"Нет обязательных ключей в задаче: {sorted(list(missing))}" + info_msg


def delete_task_with_retry(client, task_id, space_id, retries=3, delay=0.5):
    """Пытается удалить задачу с несколькими попытками."""
    for attempt in range(retries):
        del_resp = client.post(**delete_task_endpoint(task_id=task_id, space_id=space_id))
        if del_resp.status_code == 200:
            return True
        time.sleep(delay)
    print(f"Не удалось удалить задачу {task_id} после {retries} попыток: статус {del_resp.status_code}, ответ: {del_resp.text}")
    return False


def delete_all_group_tasks(client, board_id, space_id, group_id):
    """Удаляет все задачи из указанной группы на борде."""
    resp = client.post(**get_board_endpoint(board_id, space_id))
    resp.raise_for_status()
    board = resp.json()['payload']['board']
    task_ids = board['taskOrderByGroups'].get(group_id, [])
    for task_id in task_ids:
        time.sleep(0.5)
        delete_task_with_retry(client, task_id, space_id)


def safe_delete_all_tasks_in_group(client, main_board, main_space, group_id, max_retries=3):
    """Удаляет все задачи из конкретной группы с несколькими попытками на каждую."""
    resp = client.post(**get_board_endpoint(main_board, main_space))
    board = resp.json()["payload"]["board"]
    task_ids = board["taskOrderByGroups"].get(group_id, [])
    if not task_ids:
        return
    for tid in task_ids:
        time.sleep(0.5)
        for attempt in range(max_retries):
            del_resp = client.post(
                path="/DeleteTask",
                json={"taskId": tid},
                headers={"Content-Type": "application/json", "Current-Space-Id": main_space}
            )
            if del_resp.status_code == 200:
                break
            time.sleep(0.5)
        else:
            print(f"Не удалось удалить задачу {tid} после {max_retries} попыток: статус {del_resp.status_code}, ответ: {del_resp.text}")
