from typing import List, Dict, Any, Optional


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