import allure
import pytest

from test_public_api.data.endpoints.public_history_endpoint import public_history_endpoint

pytestmark = [pytest.mark.public_api]


@allure.parent_suite("Public API")
@allure.suite("History")
@allure.sub_suite("Rate Limit")
def test_public_history_rate_limit(public_client_no_retry, public_space_id):
    """Множественные запросы подряд без пауз вызывают 429 Too Many Requests."""
    allure.dynamic.title("Быстрые последовательные запросы — 429 Rate Limit")

    got_429 = False
    attempts = 20

    with allure.step(f"Отправляем {attempts} запросов подряд без пауз"):
        for i in range(attempts):
            resp = public_client_no_retry.get(
                **public_history_endpoint(
                    space_id=public_space_id, kind="Space", kind_id=public_space_id,
                )
            )
            if resp.status_code == 429:
                got_429 = True
                with allure.step(f"Получен 429 на запросе #{i + 1}"):
                    pass
                break

    with allure.step("Хотя бы один запрос вернул 429"):
        assert got_429, f"Ни один из {attempts} запросов не вернул 429"
