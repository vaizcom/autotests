from typing import Optional, Dict, Any, List


def invite_to_space_endpoint(
    space_id: str,
    email: str,
    space_access: str,  # EAccessLevel
    project_accesses: Optional[List[Dict[str, str]]] = None,
    board_accesses: Optional[List[Dict[str, str]]] = None,
    access_group_id: Optional[str] = None,
    full_name: Optional[str] = None,
    avatar_url: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Эндпоинт приглашения пользователя в пространство (InviteToSpaceInputDto).
    """
    payload: Dict[str, Any] = {
        "email": email,
        "spaceAccess": space_access,
    }

    if project_accesses is not None:
        payload["projectAccesses"] = project_accesses
    if board_accesses is not None:
        payload["boardAccesses"] = board_accesses
    if access_group_id is not None:
        payload["accessGroupId"] = access_group_id
    if full_name is not None:
        payload["fullName"] = full_name
    if avatar_url is not None:
        payload["avatarUrl"] = avatar_url

    return {
        "path": "/InviteToSpace",
        "json": payload,
        "headers": {
            "Content-Type": "application/json",
            "Current-Space-Id": space_id,
        },
    }

def remove_invite_endpoint(space_id: str, member_id: str) -> dict:
    return {
        "path": "/RemoveInvite",
        "json": {
            "memberId": member_id,
        },
        "headers": {
            "Content-Type": "application/json",
            "Current-Space-Id": space_id,
        },
    }


def resend_invite_endpoint(space_id: str, member_id: str) -> dict:
    return {
        "path": "/ResendInvite",
        "json": {
            "memberId": member_id,
        },
        "headers": {
            "Content-Type": "application/json",
            "Current-Space-Id": space_id,
        },
    }

def deactivate_member_endpoint(space_id: str, member_id: str) -> dict:
    return {
        "path": "/DeactivateMember",
        "json": {
            "memberId": member_id,
        },
        "headers": {
            "Content-Type": "application/json",
            "Current-Space-Id": space_id,
        },
    }

def reactivate_member_endpoint(space_id: str, member_id: str) -> dict:
    return {
        "path": "/ReactivateMember",
        "json": {
            "memberId": member_id,
        },
        "headers": {
            "Content-Type": "application/json",
            "Current-Space-Id": space_id,
        },
    }


def confirm_space_invite_endpoint(code: str, full_name: str, password: str, termsAccepted: bool) -> dict:
    """
    Эндпоинт для подтверждения инвайта в пространство.
    """
    return {
        "path": "/ConfirmSpaceInvite",
        "json": {
            "code": code,
            "profileFields": {
                "password": password,
                "fullName": full_name,
                "termsAccepted": termsAccepted,
                "emailSubscriptions": {}
            }
        },
        "headers": {
            "Content-Type": "application/json",
        },
    }