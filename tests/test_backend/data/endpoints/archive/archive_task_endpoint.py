def archive_task_endpoint(task_id: str, space_id: str):
    return {
        "path": "/ArchiveTask",
        "json": {"taskId": task_id},
        "headers": {"Content-Type": "application/json", "Current-Space-Id": space_id}
    }