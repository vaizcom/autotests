from typing import Dict, Any, Tuple

# Константа с валидным содержимым PNG-картинки размером 1x1 пиксель
DUMMY_PNG_CONTENT = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82'


def upload_avatar_endpoint(
        file_tuple: Tuple[str, bytes, str],
        kind: str,
        kind_id: str,
        crop_area_x: int = 30,
        crop_area_y: int = 30,
        crop_area_width: int = 100,
        crop_area_height: int = 100,
        crop_area_background_color: str = "#000000",
) -> Dict[str, Any]:
    """
    Формирует данные для эндпоинта загрузки аватара (UploadAvatarInputDto).
    """
    payload: Dict[str, Any] = {
        "kind": kind,
        "kindId": kind_id,
        "cropAreaX": str(crop_area_x),
        "cropAreaY": str(crop_area_y),
        "cropAreaWidth": str(crop_area_width),
        "cropAreaHeight": str(crop_area_height),
        "cropAreaBackgroundColor": crop_area_background_color,
    }

    return {
        "path": "/UploadAvatar",
        "data": payload,
        "files": {"file": file_tuple},
    }


def get_uploaded_avatar_url(
        client,
        kind_id: str,
        kind: str,
        headers: dict,
        file_content: bytes,
        file_name: str = "avatar.png",
        content_type: str = "image/png"
) -> str:
    """
    Вспомогательная функция для отправки multipart/form-data запроса и извлечения URL аватара.
    """
    req = upload_avatar_endpoint(
        file_tuple=(file_name, file_content, content_type),
        kind=kind,
        kind_id=kind_id,
    )

    # ВАЖНО: Удаляем Content-Type из заголовков, чтобы requests
    # сам поставил правильный multipart/form-data с нужным boundary
    # Создаем копию, чтобы не менять оригинальный словарь
    upload_headers = dict(headers)
    upload_headers.pop("Content-Type", None)

    response = client.post(
        req["path"],
        data=req["data"],
        files=req["files"],
        headers=upload_headers
    )

    if response.status_code != 200:
        print(f"\n[ОШИБКА ЗАГРУЗКИ] Ответ сервера: {response.text}\n")

    assert response.status_code == 200, f"Ошибка загрузки аватара: {response.text}"
    return response.json()["payload"]["avatar"]["avatar"]