def unarchive_task_endpoint(task_id: str, space_id: str, group_id: str = None, index: int = None):
    body = {"taskId": task_id}
    if group_id is not None:
        body["groupId"] = group_id
    if index is not None:
        body["index"] = index
    return {
        "path": "/UnarchiveTask",
        "json": body,
        "headers": {"Content-Type": "application/json", "Current-Space-Id": space_id}
    }
