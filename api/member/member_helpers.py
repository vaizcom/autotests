import random

from api.user.profile_endpoint import get_profile_endpoint
from api.member.member_endpoints import get_space_members_endpoint


def get_member_profile(client, space_id):
    """Получение memberId текущего пользователя."""
    resp = client.post(**get_profile_endpoint(space_id=space_id))
    resp.raise_for_status()
    return resp.json()["payload"]["profile"]["memberId"]


def get_assignee(client, space_id):
    """Возвращает случайный member_id из списка участников пространства."""
    response = client.post(**get_space_members_endpoint(space_id))
    response.raise_for_status()

    members = response.json().get("payload", {}).get("members", [])
    assert members, "Ошибка: список участников пуст или недоступен"

    filtered_members = [member for member in members if member.get("nickName") != "automation_bot"]
    assert filtered_members, "Ошибка: после фильтрации список участников пуст"

    roles = ['owner', 'manager', 'member', 'guest', 'main']
    member_id = {role: [m['_id'] for m in members if m.get('fullName') == role] for role in roles}

    random_member = random.choice(roles)
    return member_id[random_member]


def get_user_id(client, space_id, member_name):
    """Возвращает _id участника с указанным именем из списка участников пространства."""
    response = client.post(**get_space_members_endpoint(space_id))
    response.raise_for_status()

    members = response.json().get("payload", {}).get("members", [])
    assert members, "Ошибка: список участников пуст или недоступен"

    for member in members:
        if member.get("fullName") == member_name:
            return member["_id"]

    raise AssertionError(f"Ошибка: участник '{member_name}' не найден в пространстве")
