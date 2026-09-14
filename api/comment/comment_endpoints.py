from typing import List, Dict, Any, Optional


def get_comments_endpoint(space_id: str, document_id: str) -> Dict[str, Any]:
    """
    Эндпоинт для получения списка комментариев по документу (GetCommentsInputDto).
    """
    return {
        "path": "/GetComments",
        "json": {"documentId": document_id},
        "headers": {
            "Content-Type": "application/json",
            "Current-Space-Id": space_id,
        },
    }


def edit_comment_endpoint(
        space_id: str,
        comment_id: str,
        content: str,
        add_file_ids: Optional[List[str]] = None,
        remove_file_ids: Optional[List[str]] = None,
        order_file_ids: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """
    Эндпоинт для редактирования комментария (EditComment).
    """
    return {
        "path": "/EditComment",
        "json": {
            "commentId": comment_id,
            "content": content,
            "addFileIds": add_file_ids or [],
            "removeFileIds": remove_file_ids or [],
            "orderFileIds": order_file_ids or [],
        },
        "headers": {
            "Content-Type": "application/json",
            "Current-Space-Id": space_id,
        },
    }


def create_comment_endpoint(
        space_id: str,
        document_id: str,
        content: str,
        file_ids: Optional[List[str]] = None,
        reply_to: Optional[str] = None
) -> Dict[str, Any]:
    """
    Эндпоинт для создания комментария (ICreateCommentInputDto).
    document_id - это ID сущности, к которой прикрепляется комментарий (например, task_id).
    """
    payload: Dict[str, Any] = {
        "documentId": document_id,
        "content": content,
        "fileIds": file_ids or []  # По DTO это обязательный массив, если файлов нет - передаем пустой
    }

    if reply_to is not None:
        payload["replyTo"] = reply_to

    return {
        "path": "/PostComment",
        "json": payload,
        "headers": {
            "Content-Type": "application/json",
            "Current-Space-Id": space_id,
        },
    }