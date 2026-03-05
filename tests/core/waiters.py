import time


def wait_until(condition_func, timeout=10, poll_interval=0.5, error_msg="Превышено время ожидания"):
    """
    Универсальная функция для поллинга (ожидания).

    Периодически вызывает `condition_func()`. Если она возвращает истинное значение
    (например, найденный словарь, список или True), поллинг завершается и возвращает это значение.
    Если время вышло, выбрасывается исключение TimeoutError.

    :param condition_func: Функция без аргументов, возвращающая искомый результат или None/False.
    :param timeout: Максимальное время ожидания в секундах.
    :param poll_interval: Интервал между проверками в секундах.
    :param error_msg: Сообщение об ошибке при таймауте.
    """
    start_time = time.time()

    while time.time() - start_time < timeout:
        result = condition_func()
        if result:
            return result
        time.sleep(poll_interval)

    raise TimeoutError(error_msg)