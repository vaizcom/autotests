import allure
import pytest
from playwright.sync_api import expect, Page

from tests.test_frontend.tests.tasks.conftest import (
    TASK_NAME, _TS, open_card,
    create_milestone_from_dropdown, remove_milestone_from_dropdown,
)

pytestmark = [pytest.mark.frontend]

_MILESTONE_NAME = f"MS Alpha {_TS}"
_MILESTONE_NAME_2 = f"MS Beta {_TS}"


@allure.parent_suite("Frontend")
@allure.suite("Tasks")
@allure.sub_suite("Milestones")
@allure.title("01. Создать, выбрать и удалить Milestones")
def test_01_create_multiselect_remove_task_milestone(page: Page, soft_step, sidebar):
    """Создаёт майлстоуны из dropdown задачи, проверяет мульти-назначение и удаление."""
    open_card(page, soft_step, TASK_NAME)

    milestones_btn = sidebar.get_by_role("button", name="Milestones")

    # ── Создание МС 1 ──

    with allure.step(f"Создание майлстоуна: {_MILESTONE_NAME}"):
        soft_step("Создание MILESTONE 1", lambda: create_milestone_from_dropdown(page, _MILESTONE_NAME))

    # ── Создание МС 2 (добавляется к МС 1) → оба видны ──

    def create_second():
        create_milestone_from_dropdown(page, _MILESTONE_NAME_2)
        expect(milestones_btn.filter(has_text=_MILESTONE_NAME)).to_be_visible(timeout=5000)

    with allure.step(f"Создание и проверка обоих: {_MILESTONE_NAME_2}"):
        soft_step("Создание MILESTONE 2 + оба видны", create_second)

    # ── Удалить МС 1 → остался только МС 2 ──

    def remove_first():
        remove_milestone_from_dropdown(page, _MILESTONE_NAME)
        expect(milestones_btn.filter(has_text=_MILESTONE_NAME_2)).to_be_visible(timeout=5000)

    with allure.step(f"Удаление майлстоуна: {_MILESTONE_NAME}"):
        soft_step("Удаление MILESTONE 1", remove_first)

    # ── Удалить МС 2 → пустое состояние ──

    def remove_second():
        remove_milestone_from_dropdown(page, _MILESTONE_NAME_2)
        expect(milestones_btn.filter(has_text=_MILESTONE_NAME_2)).not_to_be_visible(timeout=5000)

    with allure.step(f"Удаление майлстоуна: {_MILESTONE_NAME_2}"):
        soft_step("Удаление MILESTONE 2", remove_second)
