import pytest


@pytest.fixture()
def cleanup_task(request):
    """Регистрирует таймстемп теста для удаления всех созданных задач.

    Удаление происходит в attach_on_failure до page.close(),
    на той же странице — без отдельного браузера.

    Использование:
        cleanup_task["ts"] = _TS
    """
    task_info = {}
    request.node._cleanup_task_info = task_info
    yield task_info
