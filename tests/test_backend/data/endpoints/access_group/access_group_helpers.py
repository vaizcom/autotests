import pytest

from core.waiters import wait_until
from test_backend.data.endpoints.access_group.access_group_endpoints import get_access_groups_endpoint


def get_member_access_group(client, space_id, member_id, group_id=None, timeout=10):
    """
    Ожидает появления участника в accessGroups.

    Если group_id не указан — ищет автоматически созданную группу,
    где members == [member_id] (единственный участник).

    Если group_id указан — ищет конкретную группу и проверяет,
    что member_id есть в её members.

    Возвращает найденную группу (dict).
    """

    def _poll():
        resp = client.post(**get_access_groups_endpoint(space_id=space_id))
        assert resp.status_code == 200, f"Ошибка GetAccessGroups: {resp.text}"
        groups = resp.json().get("payload", {}).get("accessGroups", [])

        if group_id:
            target = next((g for g in groups if g.get("_id") == group_id), None)
            if target and member_id in target.get("members", []):
                return target
            return None

        return next((g for g in groups if g.get("members") == [member_id]), None)

    try:
        return wait_until(
            condition_func=_poll,
            timeout=timeout,
            error_msg=f"Участник {member_id} не появился в accessGroups за {timeout} сек."
        )
    except TimeoutError as e:
        pytest.fail(str(e))
