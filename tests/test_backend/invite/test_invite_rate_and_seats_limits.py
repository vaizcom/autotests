import allure
import pytest

from test_backend.data.endpoints.invite.invite_endpoint import remove_invite_endpoint

from test_backend.data.endpoints.invite.invite_endpoint import (
    invite_to_space_endpoint
)

pytestmark = [pytest.mark.backend]


@allure.parent_suite("Invite Service")
@allure.suite("Rate Limits & Seats Limits")
@allure.title("Проверка лимитов: SeatsLimitReached и Too Many Requests")
def test_invite_rate_and_seats_limits(temp_client):
    """
    Лимиты: 10 мест в спейсе (1 занято создателем) и 20 инвайтов в час.
    Сценарий:
    1. Отправляем 9 инвайтов (успешно), 10-й возвращает SeatsLimitReached.
    2. Удаляем 9 инвайтов.
    3. Отправляем еще 9 инвайтов (успешно), 20-й возвращает SeatsLimitReached.
    4. Удаляем 9 инвайтов.
    5. Отправляем 21-й инвайт и получаем 429 Too Many Requests.
    """
    client, space_id = temp_client

    emails_batch_1 = [f"rate_limit_1_{i}@autotest.com" for i in range(1, 10)]  # 9 email-ов
    emails_batch_2 = [f"rate_limit_2_{i}@autotest.com" for i in range(1, 10)]  # 9 email-ов

    successful_invites = []

    with allure.step("Шаг 1: Заполняем свободные 9 мест в спейсе"):
        for email in emails_batch_1:
            response = client.post(**invite_to_space_endpoint(
                space_id=space_id,
                email=email,
                space_access="Guest"
            ))
            assert response.status_code == 200, f"Ошибка при отправке инвайта {email}: {response.text}"

            invite_id = response.json().get("payload", {}).get("invite", {}).get("_id")
            successful_invites.append(invite_id)

    with allure.step("Шаг 2: Отправляем 10-й запрос и получаем SeatsLimitReached"):
        resp_10 = client.post(**invite_to_space_endpoint(
            space_id=space_id,
            email="limit_10@autotest.com",
            space_access="Guest"
        ))
        error_code = resp_10.json().get("error", {}).get("code")
        assert error_code == "SeatsLimitReached", f"Ожидали SeatsLimitReached на 10-м запросе, а получили: {resp_10.text}"

    with allure.step("Шаг 3: Удаляем 9 созданных инвайтов для освобождения мест"):
        for invite_id in successful_invites:
            del_resp = client.post(**remove_invite_endpoint(
                space_id=space_id,
                member_id=invite_id
            ))
            assert del_resp.status_code == 200, f"Не удалось удалить инвайт {invite_id}: {del_resp.text}"
        successful_invites.clear()

    with allure.step("Шаг 4: Снова заполняем свободные 9 мест (запросы 11-19)"):
        for email in emails_batch_2:
            response = client.post(**invite_to_space_endpoint(
                space_id=space_id,
                email=email,
                space_access="Guest"
            ))
            assert response.status_code == 200, f"Ошибка при отправке инвайта {email}: {response.text}"

            invite_id = response.json().get("payload", {}).get("invite", {}).get("_id")
            successful_invites.append(invite_id)

    with allure.step("Шаг 5: Отправляем 20-й запрос (в сумме) и снова получаем SeatsLimitReached"):
        resp_20 = client.post(**invite_to_space_endpoint(
            space_id=space_id,
            email="limit_20@autotest.com",
            space_access="Guest"
        ))
        error_code = resp_20.json().get("error", {}).get("code")
        assert error_code == "SeatsLimitReached", f"Ожидали SeatsLimitReached на 20-м запросе, а получили: {resp_20.text}"

    with allure.step("Шаг 6: Снова удаляем 9 созданных инвайтов"):
        for invite_id in successful_invites:
            del_resp = client.post(**remove_invite_endpoint(
                space_id=space_id,
                member_id=invite_id
            ))
            assert del_resp.status_code == 200, f"Не удалось удалить инвайт {invite_id}: {del_resp.text}"

    with allure.step("Шаг 7: Отправляем 21-й инвайт и ловим 429 Too Many Requests"):
        resp_21 = client.post(**invite_to_space_endpoint(
            space_id=space_id,
            email="limit_21@autotest.com",
            space_access="Guest"
        ))
        assert resp_21.status_code == 429, f"Ожидали 429 Too Many Requests на 21-м запросе, а получили: {resp_21.status_code} - {resp_21.text}"