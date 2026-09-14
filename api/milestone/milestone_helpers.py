import random

from api.milestone.milestones_endpoints import get_milestones_endpoint, get_milestone_endpoint


def get_milestone(client, space_id, board_id):
    """Возвращает случайный milestone_id из указанной борды."""
    response = client.post(**get_milestones_endpoint(space_id=space_id, board_id=board_id))
    response.raise_for_status()

    milestones = response.json().get("payload", {}).get("milestones", [])
    assert milestones, "Ошибка: список майлстоунов пуст или недоступен"

    random_milestone = random.choice(milestones)
    return random_milestone["_id"]


def get_named_milestone_id(client, space_id, board_id, milestone_name):
    """Возвращает _id майлстоуна с заданным именем. Ошибка, если не найден."""
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
    """ID milestone для родительской задачи (B)."""
    return get_named_milestone_id(client, space_id, board_id, "parent_ms_2")


def get_subtask_ms_1(client, space_id, board_id):
    """ID milestone для сабтаска 1."""
    return get_named_milestone_id(client, space_id, board_id, "subtask_ms_1")


def get_subtask_ms_2(client, space_id, board_id):
    """ID milestone для сабтаска 2."""
    return get_named_milestone_id(client, space_id, board_id, "subtask_ms_2")


def get_milestone_id(client, space_id, ms_id):
    """Получить подробности по одному milestone по его _id."""
    endpoint = get_milestone_endpoint(ms_id, space_id)
    response = client.post(**endpoint)
    response.raise_for_status()
    return response.json()['payload']['milestone']
