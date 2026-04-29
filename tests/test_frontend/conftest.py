import io
from pathlib import Path

import allure
import pytest
import pytest_check as check
import requests
from PIL import Image, ImageChops, ImageDraw

from tests.test_frontend.core.settings import BASE_URL, FRONTEND_EMAIL, FRONTEND_PASSWORD, FRONTEND_STAND

# API URL для teardown-операций (удаление Space, Project и т.д.)
API_URL = "https://api.vaiz.dev/v4"


@pytest.fixture(scope="session")
def api_token():
    """Получает API-токен один раз на сессию для teardown-операций."""
    resp = requests.post(
        f"{API_URL}/Login",
        json={"email": FRONTEND_EMAIL, "password": FRONTEND_PASSWORD},
        timeout=30,
        verify=False,
    )
    return resp.json()["payload"]["token"]


def pytest_addoption(parser):
    """Регистрирует флаг --update-snapshots для обновления VRT-baseline.

    Использование:
        pytest --update-snapshots       # обновить все baseline
        pytest test.py --update-snapshots  # обновить baseline конкретного теста
    """
    parser.addoption(
        "--update-snapshots",
        action="store_true",
        default=False,
        help="Обновить baseline скриншоты",
    )


def pytest_collection_finish(session):
    """Выводит в консоль стенд и URL перед запуском frontend-тестов.

    Срабатывает после сбора тестов, перед их запуском.
    Помогает убедиться что тесты запускаются на нужном стенде.
    """
    has_frontend = any(item.get_closest_marker("frontend") for item in session.items)
    if has_frontend:
        print(f"\n🧪 Running on stand: {FRONTEND_STAND}")
        print(f"🌐 UI URL: {BASE_URL}\n")


@pytest.fixture(scope="session")
def auth_state(playwright):
    """Логинится один раз на сессию и сохраняет состояние браузера.

    Открывает отдельный браузер, проходит логин и сохраняет куки и localStorage
    через storage_state(). Результат передаётся в browser_context_args и
    переиспользуется всеми тестами — каждый тест стартует уже залогиненным.

    Scope session означает что логин происходит ровно один раз за весь прогон.
    """
    browser = playwright.chromium.launch()
    context = browser.new_context(ignore_https_errors=True)
    page = context.new_page()
    page.goto(f"{BASE_URL}/auth/sign-in")
    page.get_by_role("textbox", name="Email").fill(FRONTEND_EMAIL)
    page.get_by_role("textbox", name="Password").fill(FRONTEND_PASSWORD)
    page.get_by_role("button", name="Continue with Email").click()
    page.get_by_role("link", name="Home").wait_for(state="visible")
    state = context.storage_state()
    context.close()
    browser.close()
    return state


@pytest.fixture(scope="session")
def browser_context_args(browser_context_args, auth_state):
    """Настраивает браузерный контекст для всех тестов.

    Переопределяет стандартные настройки pytest-playwright:
    - storage_state: внедряет сохранённую сессию, тест стартует залогиненным
    - ignore_https_errors: игнорирует SSL-ошибки на dev-стенде
    - viewport: фиксирует размер окна для стабильных VRT-скриншотов
    """
    return {
        **browser_context_args,
        "ignore_https_errors": True,
        "storage_state": auth_state,
        "viewport": {"width": 1280, "height": 720},
        "record_video_dir": "test-results/videos",
    }


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """Сохраняет результат каждой фазы теста в атрибуты тест-айтема.

    Нужен чтобы фикстура attach_on_failure могла узнать упал ли тест —
    внутри фикстуры эта информация иначе недоступна.
    tryfirst=True гарантирует что хук выполняется до других хуков.
    """
    outcome = yield
    rep = outcome.get_result()
    setattr(item, f"rep_{rep.when}", rep)


@pytest.fixture
def soft_step(page):
    """Обёртка для шагов с soft assertion — тест продолжается при ошибке.

    При падении шага:
    - Классифицирует ошибку Playwright в человекочитаемую подсказку
    - Прикладывает скриншот страницы и краткий лог к Allure
    - Регистрирует soft failure через pytest-check (тест не останавливается)

    Использование:
        with allure.step("Приоритет: Medium"):
            soft_step("Приоритет", lambda: page.get_by_text("Medium").click())
    """
    def _soft_step(name, fn, timeout=15000):
        page.set_default_timeout(timeout)
        try:
            fn()
        except Exception as e:
            full = str(e)
            short = full.split("\nCall log:")[0].split("\n")[0]

            if "intercepts pointer events" in full:
                hint = "Элемент перекрыт другим элементом — попап, оверлей или изменилась вёрстка"
                for line in full.split("\n"):
                    if "intercepts pointer events" in line:
                        blocker = line.strip().lstrip("- ")
                        detail = f"{short}\nБлокирует: {blocker}"
                        break
                else:
                    detail = short
            elif "strict mode violation" in full:
                hint = "Найдено несколько элементов — уточните локатор"
                detail = short
            elif "Target closed" in full or "browser has been closed" in full:
                hint = "Браузер или страница закрылись — возможно предыдущий шаг сломал сессию"
                detail = short
            elif "disabled" in full and "enabled" in full:
                hint = "Элемент заблокирован (disabled) — проверьте состояние UI"
                detail = short
            elif "Timeout" in full and "waiting for" in full:
                hint = "Элемент не найден — возможно изменился UI или локатор устарел"
                detail = short
            elif "not visible" in full or "not attached" in full:
                hint = "Элемент не виден на странице — проверьте, что поле отображается"
                detail = short
            else:
                hint = "Непредвиденная ошибка"
                detail = short

            log_text = f"Причина: {hint}\n{detail}"
            allure.attach(page.screenshot(), name=f"{name} — скриншот", attachment_type=allure.attachment_type.PNG)
            allure.attach(log_text, name=f"{name} — лог", attachment_type=allure.attachment_type.TEXT)
            check.fail(f"[{name}] {hint}")
        finally:
            page.set_default_timeout(30000)

    return _soft_step


@pytest.fixture(autouse=True)
def attach_on_failure(request, page):
    """Прикладывает артефакты к Allure-отчёту при падении теста.

    Подключается автоматически к каждому тесту (autouse=True).

    До теста: запускает запись Playwright-трейса — видеозапись всех действий
    браузера со скриншотами и сетевыми запросами.

    После теста:
    - Упал: прикладывает к Allure скриншот страницы в момент падения,
      URL и Playwright-трейс в zip-архиве.
    - Прошёл: останавливает трейс без сохранения, удаляет старый zip
      от предыдущего падения если он остался.
    """
    allure.dynamic.parameter("test_name", request.node.originalname)

    context = page.context
    context.tracing.start(screenshots=True, snapshots=True)

    yield

    trace_path = Path(request.node.fspath).parent / "__snapshots__" / f"{request.node.name}.zip"
    failed = getattr(getattr(request.node, "rep_call", None), "failed", False)

    # Снимаем скриншот и URL до закрытия страницы
    if failed:
        try:
            failure_screenshot = page.screenshot()
            failure_url = page.url
        except Exception:
            failure_screenshot = None
            failure_url = None

    # Закрываем страницу чтобы видео финализировалось
    video_path = page.video.path() if page.video else None
    page.close()

    if failed:
        try:
            if failure_screenshot:
                allure.attach(failure_screenshot, name="screenshot on failure", attachment_type=allure.attachment_type.PNG)
            if failure_url:
                allure.attach(failure_url, name="page URL", attachment_type=allure.attachment_type.TEXT)
            if video_path and Path(video_path).exists():
                allure.attach(Path(video_path).read_bytes(), name="video", attachment_type=allure.attachment_type.WEBM)
            context.tracing.stop(path=str(trace_path))
            allure.attach(trace_path.read_bytes(), name="playwright trace", attachment_type=allure.attachment_type.ZIP)
        except Exception:
            context.tracing.stop()
    else:
        context.tracing.stop()
        trace_path.unlink(missing_ok=True)

    # Удаляем видеофайл — уже приложен к Allure или не нужен
    if video_path and Path(video_path).exists():
        Path(video_path).unlink(missing_ok=True)


@pytest.fixture
def assert_snapshot(request):
    """Фикстура для визуального сравнения скриншотов (VRT).

    Сравнивает переданный скриншот с сохранённым baseline попиксельно.
    Baseline хранится в __snapshots__/<stand>/<name>.png рядом с тест-файлом.
    При падении прикладывает к Allure три картинки: baseline, actual, diff.

    Аргументы:
        screenshot: байты скриншота, полученные через page.screenshot()
        name:       имя файла baseline, например "sign_in_success.png"
        threshold:  допустимый процент отличающихся пикселей (по умолчанию 0.1%)

    Пример использования:
        screenshot = page.screenshot(mask=[...])
        assert_snapshot(screenshot, name="my_page.png", threshold=3.0)

    Обновление baseline:
        pytest --update-snapshots           # все тесты
        pytest test.py --update-snapshots   # конкретный файл
    """
    def _assert(screenshot: bytes, name: str, threshold: float = 1.0):
        snapshot_dir = Path(request.fspath).parent / "__snapshots__" / FRONTEND_STAND
        snapshot_dir.mkdir(parents=True, exist_ok=True)
        snapshot_path = snapshot_dir / name
        test_name = request.node.originalname

        if not snapshot_path.exists():
            snapshot_path.write_bytes(screenshot)
            return

        if request.config.getoption("--update-snapshots"):
            snapshot_path.write_bytes(screenshot)
            pytest.skip(f"Baseline обновлён: {snapshot_path.name}.")

        # Удаляем артефакты прошлого падения перед новым сравнением
        (snapshot_dir / name.replace(".png", "_actual.png")).unlink(missing_ok=True)
        (snapshot_dir / name.replace(".png", "_diff.png")).unlink(missing_ok=True)

        baseline = Image.open(snapshot_path).convert("RGB")
        actual = Image.open(io.BytesIO(screenshot)).convert("RGB")

        if baseline.size != actual.size:
            allure.attach(snapshot_path.read_bytes(), name="baseline", attachment_type=allure.attachment_type.PNG)
            allure.attach(screenshot, name="actual", attachment_type=allure.attachment_type.PNG)
            check.fail(
                f"[VRT {name}] Размер изменился: baseline {baseline.size} → actual {actual.size}. "
                f"Для обновления: pytest --update-snapshots / в CI: snapshot_test={test_name}"
            )
            return

        # Пиксель считается отличающимся если хоть один RGB-канал отличается больше чем на 10 единиц.
        # Порог 10 отфильтровывает субпиксельный шум рендеринга.
        diff = ImageChops.difference(baseline, actual)
        diff_pixels = sum(1 for p in diff.getdata() if any(c > 10 for c in p))
        total_pixels = baseline.width * baseline.height
        diff_pct = diff_pixels / total_pixels * 100

        # Генерируем diff-картинку если есть пиксельные различия
        diff_coords = [
            (i % baseline.width, i // baseline.width)
            for i, pixel in enumerate(diff.getdata())
            if any(c > 10 for c in pixel)
        ]

        allure.attach(snapshot_path.read_bytes(), name="baseline", attachment_type=allure.attachment_type.PNG)
        allure.attach(screenshot, name="actual", attachment_type=allure.attachment_type.PNG)

        if diff_pct > threshold:
            if diff_coords:
                diff_highlighted = baseline.copy()
                draw = ImageDraw.Draw(diff_highlighted)
                for x, y in diff_coords:
                    draw.point((x, y), fill=(255, 0, 0))
                buf = io.BytesIO()
                diff_highlighted.save(buf, format="PNG")
                allure.attach(buf.getvalue(), name=f"diff ({diff_pct:.2f}%)", attachment_type=allure.attachment_type.PNG)

                diff_path = snapshot_dir / name.replace(".png", "_diff.png")
                diff_path.write_bytes(buf.getvalue())

            actual_path = snapshot_dir / name.replace(".png", "_actual.png")
            actual_path.write_bytes(screenshot)
            check.fail(
                f"[VRT {name}] Скриншот отличается от baseline на {diff_pct:.2f}% "
                f"(допустимо {threshold}%). "
                f"Для обновления: pytest --update-snapshots / в CI: snapshot_test={test_name}"
            )

    return _assert
