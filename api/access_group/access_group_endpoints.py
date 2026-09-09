def get_access_group_endpoint(space_id: str, group_id: str):
    """
    Получение информации о группе доступа (GetAccessGroupInputDto).
    """
    return {
        "path": "/GetAccessGroup",
        "json": {"groupId": group_id},
        "headers": {
            "Content-Type": "application/json",
            "Current-Space-Id": space_id
        }
    }

def get_access_groups_endpoint(space_id: str):
    """
    Получение всех групп доступа в спейсе (GetAccessGroupsInputDto).

    Возвращает список всех accessGroup в спейсе. Бывают двух видов:
      - Кастомные группы — созданные вручную через CreateAccessGroup.
      - Персональные (selfAccessGroup) — создаются автоматически при
        добавлении участника в спейс, по одной на каждого мембера.
        В поле members такой группы — ровно один участник.

    Флоу смены прав конкретного участника:
      1. Вызвать GetAccessGroups → найти группу где members == [member_id]
      2. Взять _id этой группы (это groupId)
      3. Вызвать UpdateAccessGroupRights(groupId, kind, kindId, level)

    Ответ: payload.accessGroups — список dict с полями:
      _id, members, spaceAccesses, projectAccesses, boardAccesses, ...
    """
    return {
        "path": "/GetAccessGroups",
        "headers": {
            "Content-Type": "application/json",
            "Current-Space-Id": space_id
        }
    }


def create_access_group_endpoint(
        space_id: str,
        name: str,
        description: str,
        space_accesses: dict = None,
        project_accesses: dict = None,
        board_accesses: dict = None
):
    """
    Создание группы доступа (CreateAccessGroupInputDto).
    """
    json_payload = {
        "name": name,
        "description": description,
    }

    if space_accesses is not None:
        json_payload["spaceAccesses"] = space_accesses
    if project_accesses is not None:
        json_payload["projectAccesses"] = project_accesses
    if board_accesses is not None:
        json_payload["boardAccesses"] = board_accesses

    return {
        "path": "/CreateAccessGroup",
        "json": json_payload,
        "headers": {
            "Content-Type": "application/json",
            "Current-Space-Id": space_id
        }
    }


def update_access_group_endpoint(space_id: str, group_id: str, name: str = None, description: str = None):
    """
    Обновление имени/описания группы доступа (UpdateAccessGroupInputDto).
    """
    json_payload = {"groupId": group_id}
    if name is not None:
        json_payload["name"] = name
    if description is not None:
        json_payload["description"] = description

    return {
        "path": "/UpdateAccessGroup",
        "json": json_payload,
        "headers": {
            "Content-Type": "application/json",
            "Current-Space-Id": space_id,
        },
    }


def update_access_group_rights_endpoint(space_id: str, group_id: str, kind: str, kind_id: str, level: str):
    """
    Обновление прав группы доступа на сущность (UpdateAccessGroupRightsInputDto).

    Работает и с кастомными группами, и с персональными selfAccessGroup.
    kind: 'Space' | 'Project' | 'Board'
    level: EAccessLevel ('Member', 'Manager', 'Owner', 'Guest', 'NoAccess')

    Ограничения для selfAccessGroup:
      - Нельзя менять права своей группы (OwnAccessChangeNotAllowed)
      - Нельзя менять права создателя спейса (CreatorAccessChangeNotAllowed)
      - Нельзя менять права Owner-уровня (GrandAccessChangeNotAllowed)
    """
    return {
        "path": "/UpdateAccessGroupRights",
        "json": {
            "groupId": group_id,
            "kind": kind,
            "kindId": kind_id,
            "level": level,
        },
        "headers": {
            "Content-Type": "application/json",
            "Current-Space-Id": space_id,
        },
    }


def remove_access_group_endpoint(space_id: str, group_id: str):
    """
    Удаление группы доступа (RemoveAccessGroupInputDto).
    """
    return {
        "path": "/RemoveAccessGroup",
        "json": {"groupId": group_id},
        "headers": {
            "Content-Type": "application/json",
            "Current-Space-Id": space_id,
        },
    }


def set_access_group_member_endpoint(space_id: str, member_id: str, access_group_id: str):
    """
    Добавление участника в группу доступа (SetAccessGroupsMemberInputDto).
    Триггерит MEMBER_SET_ACCESS.
    """
    return {
        "path": "/SetAccessGroupsMember",
        "json": {
            "memberId": member_id,
            "accessGroupId": access_group_id,
        },
        "headers": {
            "Content-Type": "application/json",
            "Current-Space-Id": space_id,
        },
    }


def remove_access_group_member_endpoint(space_id: str, member_id: str, access_group_id: str):
    """
    Удаление участника из группы доступа (RemoveAccessGroupMemberInputDto).
    Триггерит MEMBER_REMOVE_ACCESS.
    """
    return {
        "path": "/RemoveAccessGroupMember",
        "json": {
            "memberId": member_id,
            "accessGroupId": access_group_id,
        },
        "headers": {
            "Content-Type": "application/json",
            "Current-Space-Id": space_id,
        },
    }