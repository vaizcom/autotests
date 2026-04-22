import io
from pathlib import Path

import allure
import pytest
from PIL import Image, ImageChops, ImageDraw

from tests.test_frontend.core.settings import BASE_URL, FRONTEND_EMAIL, FRONTEND_PASSWORD, FRONTEND_STAND


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
    context = page.context
    context.tracing.start(screenshots=True, snapshots=True)

    yield

    trace_path = Path(request.node.fspath).parent / "__snapshots__" / f"{request.node.name}.zip"
    failed = getattr(getattr(request.node, "rep_call", None), "failed", False)

    if failed:
        try:
            allure.attach(
                page.screenshot(),
                name="screenshot on failure",
                attachment_type=allure.attachment_type.PNG,
            )
            allure.attach(
                page.url,
                name="page URL",
                attachment_type=allure.attachment_type.TEXT,
            )
            context.tracing.stop(path=str(trace_path))
            allure.attach(
                trace_path.read_bytes(),
                name="playwright trace",
                attachment_type=allure.attachment_type.ZIP,
            )
        except Exception:
            context.tracing.stop()
    else:
        context.tracing.stop()
        trace_path.unlink(missing_ok=True)


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
        assert_snapshot(screenshot, name="my_page.png", threshold=1.5)

    Обновление baseline:
        pytest --update-snapshots           # все тесты
        pytest test.py --update-snapshots   # конкретный файл
    """
    def _assert(screenshot: bytes, name: str, threshold: float = 0.1):
        snapshot_dir = Path(request.fspath).parent / "__snapshots__" / FRONTEND_STAND
        snapshot_dir.mkdir(parents=True, exist_ok=True)
        snapshot_path = snapshot_dir / name
        test_name = request.node.originalname

        if not snapshot_path.exists() or request.config.getoption("--update-snapshots"):
            snapshot_path.write_bytes(screenshot)
            pytest.skip(f"Baseline сохранён: {snapshot_path.name}. Запусти тест снова.")

        # Удаляем артефакты прошлого падения перед новым сравнением
        (snapshot_dir / name.replace(".png", "_actual.png")).unlink(missing_ok=True)
        (snapshot_dir / name.replace(".png", "_diff.png")).unlink(missing_ok=True)

        baseline = Image.open(snapshot_path).convert("RGB")
        actual = Image.open(io.BytesIO(screenshot)).convert("RGB")

        if baseline.size != actual.size:
            allure.attach(snapshot_path.read_bytes(), name="baseline", attachment_type=allure.attachment_type.PNG)
            allure.attach(screenshot, name="actual", attachment_type=allure.attachment_type.PNG)
            pytest.fail(
                f"Размер изменился: baseline {baseline.size} → actual {actual.size}.\n"
                f"Для обновления запусти: pytest --update-snapshots\n"
                f"В CI укажи в поле snapshot_test: {test_name}"
            )

        # Пиксель считается отличающимся если хоть один RGB-канал отличается больше чем на 10 единиц.
        # Порог 10 отфильтровывает субпиксельный шум рендеринга.
        diff = ImageChops.difference(baseline, actual)
        diff_pixels = sum(1 for p in diff.getdata() if any(c > 10 for c in p))
        total_pixels = baseline.width * baseline.height
        diff_pct = diff_pixels / total_pixels * 100

        if diff_pct > threshold:
            actual_path = snapshot_dir / name.replace(".png", "_actual.png")
            actual_path.write_bytes(screenshot)

            # Строим diff-картинку: копия baseline с красными точками в местах различий
            # и красным прямоугольником вокруг всей зоны отличий
            diff_highlighted = baseline.copy()
            draw = ImageDraw.Draw(diff_highlighted)
            diff_coords = [
                (i % baseline.width, i // baseline.width)
                for i, pixel in enumerate(diff.getdata())
                if any(c > 10 for c in pixel)
            ]
            for x, y in diff_coords:
                draw.point((x, y), fill=(255, 0, 0))

            if diff_coords:
                xs = [p[0] for p in diff_coords]
                ys = [p[1] for p in diff_coords]
                padding = 5
                draw.rectangle(
                    [min(xs) - padding, min(ys) - padding,
                     max(xs) + padding, max(ys) + padding],
                    outline=(255, 0, 0), width=2,
                )

            diff_path = snapshot_dir / name.replace(".png", "_diff.png")
            diff_highlighted.save(diff_path)

            allure.attach(snapshot_path.read_bytes(), name="baseline", attachment_type=allure.attachment_type.PNG)
            allure.attach(screenshot, name="actual", attachment_type=allure.attachment_type.PNG)
            allure.attach(diff_path.read_bytes(), name="diff", attachment_type=allure.attachment_type.PNG)

            pytest.fail(
                f"Скриншот отличается от baseline на {diff_pct:.2f}% пикселей "
                f"(допустимо {threshold}%).\n"
                f"Baseline:  {snapshot_path}\n"
                f"Actual:    {actual_path}\n"
                f"Diff:      {diff_path}\n"
                f"Для обновления запусти: pytest --update-snapshots\n"
                f"В CI укажи в поле snapshot_test: {test_name}"
            )

    return _assert
