import re


def short_resp(resp) -> str:
    """Возвращает краткое описание ответа для assert-сообщений.

    - HTML (Cloudflare 504, etc.) → одна строка вместо полотна
    - JSON с ошибкой → код + описание
    - Остальное → обрезка до 300 символов
    """
    text = resp.text or ""
    status = resp.status_code

    # HTML-ответ (Cloudflare, nginx, etc.)
    if "<html" in text.lower() or "<!doctype" in text.lower():
        title_match = re.search(r"<title>(.*?)</title>", text, re.IGNORECASE)
        title = title_match.group(1).strip() if title_match else "HTML response"
        return f"HTTP {status} — {title}"

    # JSON с ошибкой
    try:
        body = resp.json()
        if isinstance(body, dict):
            error = body.get("error", {})
            if error:
                code = error.get("code", "?")
                meta = error.get("meta", {})
                msg = meta.get("message", "") if meta else ""
                fields = error.get("fields", [])
                parts = [f"HTTP {status} — {code}"]
                if msg:
                    parts.append(msg)
                if fields:
                    field_codes = [
                        f"{f.get('name')}: {f.get('codes', [])}"
                        for f in fields if f.get("name")
                    ]
                    if field_codes:
                        parts.append(f"fields=[{', '.join(field_codes)}]")
                return " | ".join(parts)
    except (ValueError, AttributeError):
        pass

    # Обычный текст — обрезаем
    if len(text) > 300:
        return f"HTTP {status} — {text[:300]}..."
    return f"HTTP {status} — {text}"
