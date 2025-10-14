from datetime import datetime, timedelta
import re
import random
import allure
import time
from test_backend.data.endpoints.Board.board_endpoints import get_board_endpoint
from test_backend.data.endpoints.Project.project_endpoints import get_project_endpoint
from test_backend.data.endpoints.Task.task_endpoints import delete_task_endpoint
from test_backend.data.endpoints.User.profile_endpoint import get_profile_endpoint
from test_backend.data.endpoints.member.member_endpoints import get_space_members_endpoint
from test_backend.data.endpoints.milestone.milestones_endpoints import get_milestones_endpoint, get_milestone_endpoint


def validate_hrid(client, space_id, project_id, task_hrid):
    """
    Проверяет, что hrid соответствует формату <slug>-<число>.
    """
    # Проверяем, что клиент является объектом APIClient
    assert hasattr(client, 'post'), "Клиент должен быть экземпляром APIClient"

    with allure.step("Получаем slug проекта"):
        response = client.post(**get_project_endpoint(project_id=project_id, space_id=space_id))
        response.raise_for_status()

        # Получаем slug проекта
        project_slug = response.json().get("payload", {}).get("project", {}).get("slug", None)
        assert project_slug, "Ошибка: не удалось получить slug проекта"

    # Проверяем, что hrid соответствует формату <slug>-<число>
    hrid_pattern = rf"^{project_slug}-\d+$"
    with allure.step(f"Проверка, что hrid '{task_hrid}' соответствует шаблону '{hrid_pattern}'"):
        assert re.match(hrid_pattern, task_hrid), f"Поле 'hrid' имеет некорректный формат: {task_hrid}"

def get_member_profile(client, space_id):
    """Получение id пользователя который создает задачу"""
    resp = client.post(**get_profile_endpoint(space_id=space_id))
    resp.raise_for_status()
    return resp.json()["payload"]["profile"]["memberId"]

def create_task(client, payload):
    """Helper function to create task."""
    return client.post(**payload)

def get_client(request, client_fixture):
    """Получение клиента из тестового фикстура."""
    with allure.step(f"Получение клиента для {client_fixture}"):
        return request.getfixturevalue(client_fixture)


def get_random_type_id(client, board_id, space_id):
    """
    Получение случайного `_id` из typesList борды.
    """
    with allure.step(f"Запрашиваем данные борды с ID: {board_id}"):
        response = client.post(**get_board_endpoint(board_id=board_id, space_id=space_id))
        response.raise_for_status()

    board_data = response.json().get("payload", {}).get("board", {})
    types_list = board_data.get("typesList", [])

    with allure.step("Проверяем наличие typesList"):
        assert types_list, "Ошибка: typesList пуст или не существует."

    with allure.step("Рандомно выбираем `type` из typesList"):
        random_type = random.choice(types_list)
        return random_type["_id"]


def get_random_group_id(client, board_id, space_id):
    """
    Получение случайного `_id` группы из списка groups борды.
    """
    with allure.step(f"Запрашиваем данные борды с ID: {board_id}"):
        response = client.post(**get_board_endpoint(board_id=board_id, space_id=space_id))
        response.raise_for_status()

    board_data = response.json().get("payload", {}).get("board", {})
    groups = board_data.get("groups", [])

    with allure.step("Проверяем наличие списка групп"):
        assert groups, "Ошибка: groups пуст или не существует."

    with allure.step("Рандомно выбираем группу из списка"):
        random_group = random.choice(groups)
        return random_group["_id"]


def get_current_timestamp():
    """
    Возвращает текущую дату и время в формате "YYYY-MM-DDTHH:MM:SS.sss+00:00".
    :return: строка с датой и временем.
    """
    current_time = datetime.utcnow()
    return current_time.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "+00:00"

def get_due_end():
    """
    Возвращает дату и время через неделю от текущего момента в формате "YYYY-MM-DDTHH:MM:SS.sss+00:00".
    :return: строка с датой и временем.
    """
    current_time = datetime.utcnow()  # OK: datetime импортирован
    due_end = current_time + timedelta(weeks=1)  # OK: timedelta импортирован
    return due_end.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "+00:00"

def get_priority():
    """
    Возвращает случайный priority от 0 до 3.
    """
    return random.randint(0, 3)

def get_assignee(client, space_id):
    """
    Возвращает случайный member_id из списка участников пространства (space).
    :return: случайный member_id
    """
    # Делаем запрос к endpoint для получения списка участников
    response = client.post(**get_space_members_endpoint(space_id))
    response.raise_for_status()  # Поднимаем исключение, если статус код != 2xx

    # Извлекаем список участников
    members = response.json().get("payload", {}).get("members", [])
    assert members, "Ошибка: список участников пуст или недоступен"

    # Фильтруем список, исключая участника с nickName "automation_bot"
    filtered_members = [member for member in members if member.get("nickName") != "automation_bot"]
    assert filtered_members, "Ошибка: после фильтрации список участников пуст"

    # Рандомно выбираем member_id из отфильтрованного списка
    random_member = random.choice(filtered_members)
    return random_member["_id"]


def get_milestone(client, space_id, board_id):
    """
    Получает список майлстоунов из указанной борды и возвращает случайный milestone_id.
    :return: Случайный идентификатор майлстоуна.
    """
    # Делаем запрос к эндпоинту для получения майлстоунов
    response = client.post(**get_milestones_endpoint(space_id=space_id, board_id=board_id))
    response.raise_for_status()  # Проверяем успешность запроса

    # Извлекаем список майлстоунов
    milestones = response.json().get("payload", {}).get("milestones", [])
    assert milestones, "Ошибка: список майлстоунов пуст или недоступен"

    # Возвращаем случайный milestone_id
    random_milestone = random.choice(milestones)
    return random_milestone["_id"]

def assert_task_keys(doc, expected_keys):
    actual = set(doc.keys())
    extra = actual - expected_keys
    missing = expected_keys - actual
    info_msg = (
        f"\nВсе ключи в ответе: {sorted(list(actual))}\n"
        f"Ожидались ключи:    {sorted(list(expected_keys))}\n"
    )
    assert not extra, f"Есть лишние ключи в задаче: {sorted(list(extra))}" + info_msg
    assert not missing, f"Нет обязательных ключей в задаче: {sorted(list(missing))}" + info_msg


def delete_task_with_retry(client, task_id, space_id, retries=2, delay=0.5):
    """
    Пытается удалить задачу с несколькими попытками.
    """
    for attempt in range(retries):
        del_resp = client.post(**delete_task_endpoint(task_id=task_id, space_id=space_id))
        if del_resp.status_code == 200:
            return True
        time.sleep(delay)
    print(f"Не удалось удалить задачу {task_id} после {retries} попыток: статус {del_resp.status_code}, ответ: {del_resp.text}")
    return False

def delete_all_group_tasks(client, board_id, space_id, group_id):
    """
    Удаляет все задачи из указанной группы на борде.
    """
    with allure.step(f'Удаляем все задачи из группы {group_id}'):
        resp = client.post(**get_board_endpoint(board_id, space_id))
        resp.raise_for_status()
        board = resp.json()['payload']['board']
        task_ids = board['taskOrderByGroups'].get(group_id, [])
        for task_id in task_ids:
            time.sleep(0.5)
            delete_task_with_retry(client, task_id, space_id)

def safe_delete_all_tasks_in_group(client, main_board, main_space, group_id, max_retries=3):
    """
    Удаляет все задачи из конкретной группы.
    Для каждой задачи делает несколько попыток, если не получилось — пишет причину, но не падает жестко.
    """
    with allure.step(f"Удаляем все задачи из группы {group_id} (безаварийно)"):
        resp = client.post(**get_board_endpoint(main_board, main_space))
        board = resp.json()["payload"]["board"]
        task_ids = board["taskOrderByGroups"].get(group_id, [])
        if not task_ids:
            return
        # Чтобы не пропустить "зависшие" задачи (если get_tasks_endpoint вдруг отличается), проходим по списку task_ids
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


def wait_group_empty(client, board_id, space_id, group_id, timeout=10, poll_interval=0.5):
    """Ожидает, пока группа не станет пустой, либо истекает timeout (сек)"""
    start_time = time.time()
    while time.time() - start_time < timeout:
        board = client.post(**get_board_endpoint(board_id, space_id)).json()["payload"]["board"]
        tasks = board["taskOrderByGroups"].get(group_id, [])
        if not tasks:
            return
        time.sleep(poll_interval)
    # Если tasks не пуст — значит, что-то не так
    raise AssertionError(f"Группа {group_id} осталась не пустой: {tasks}")


def get_named_milestone_id(client, space_id, board_id, milestone_name):
    """
    Возвращает _id майлстоуна с заданным именем в текущей доске.
    Ошибка, если не найден.
    """
    resp = client.post(**get_milestones_endpoint(space_id=space_id, board_id=board_id))
    resp.raise_for_status()
    milestones = resp.json().get("payload", {}).get("milestones", [])
    for ms in milestones:
        if ms.get("name") == milestone_name:
            return ms["_id"]
    raise AssertionError(f"Milestone с именем '{milestone_name}' не найден на борде {board_id}")

def get_parent_ms_1(client, space_id, board_id):
    """ID milestone для родительской задачи (A)."""
    return get_named_milestone_id(client, space_id, board_id, "parent_ms_1")

def get_parent_ms_2(client, space_id, board_id):
    """ID milestone для родительской задачи (A)."""
    return get_named_milestone_id(client, space_id, board_id, "parent_ms_2")

def get_subtask_ms_1(client, space_id, board_id):
    """ID milestone для сабтаска 1 (B)."""
    return get_named_milestone_id(client, space_id, board_id, "subtask_ms_1")

def get_subtask_ms_2(client, space_id, board_id):
    """ID milestone для сабтаска 2 (C)."""
    return get_named_milestone_id(client, space_id, board_id, "subtask_ms_2")

def get_milestone_id(client, space_id: str, ms_id: str):
    """Получить подробности по одному milestone по его _id."""
    endpoint = get_milestone_endpoint(ms_id, space_id)
    response = client.post(**endpoint)
    response.raise_for_status()
    return response.json()['payload']['milestone']


def create_parent_and_subtasks(create_task_in_main, client_fixture, owner_client, main_space, main_board):
    """
    Создает родительскую задачу с milestone parent_ms_1,
    три подзадачи: первая с milestone subtask_ms_1,
    вторая с milestone subtask_ms_2, третья без milestone.

    Возвращает:
        created_tasks (list): список всех созданных задач
        ids (dict): словарь с ключами 'parent', 'subtask1', 'subtask2', 'subtask3' и их _id
    """
    parent_ms_1 = get_parent_ms_1(owner_client, main_space, main_board)
    subtask_ms_1 = get_subtask_ms_1(owner_client, main_space, main_board)
    subtask_ms_2 = get_subtask_ms_2(owner_client, main_space, main_board)

    ms = {
        "parent_ms_1": parent_ms_1,
        "subtask_ms_1": subtask_ms_1,
        "subtask_ms_2": subtask_ms_2
    }

    created_tasks = []

    with allure.step('Создание родительской задачи с milestone parent_ms_1'):
        parent_task = create_task_in_main(
            client_fixture,
            name="Parent Task with milestone parent_ms_1",
            milestones=[parent_ms_1],
        )
        created_tasks.append(parent_task)
        parent_task_id = parent_task["_id"]

    with allure.step('Создание первой подзадачи с milestone subtask_ms_1'):
        subtask1 = create_task_in_main(
            client_fixture,
            name="Subtask 1 with milestone subtask_ms_1",
            milestones=[subtask_ms_1],
            parent_task=parent_task_id,
        )
        created_tasks.append(subtask1)
        subtask1_id = subtask1["_id"]

    with allure.step('Создание второй подзадачи с milestone subtask_ms_2'):
        subtask2 = create_task_in_main(
            client_fixture,
            name="Subtask 2 with milestone subtask_ms_2",
            milestones=[subtask_ms_2],
            parent_task=parent_task_id,
        )
        created_tasks.append(subtask2)
        subtask2_id = subtask2["_id"]

    with allure.step('Создание третьей подзадачи без milestone'):
        subtask3 = create_task_in_main(
            client_fixture,
            name="Subtask 3 without milestone",
            milestones=[],
            parent_task=parent_task_id,
        )
        created_tasks.append(subtask3)
        subtask3_id = subtask3["_id"]

    ids = {
        "parent": parent_task_id,
        "subtask1": subtask1_id,
        "subtask2": subtask2_id,
        "subtask3": subtask3_id,
    }

    return ids, ms