"""Telegram Bot API 封装。

支持：
- 自定义 Bot Token
- TG API 反代（api_base，默认 https://api.telegram.org）
- HTTP 代理（proxy，如 http://127.0.0.1:7890）
"""
import httpx

DEFAULT_API_BASE = "https://api.telegram.org"


def _client(proxy: str | None) -> httpx.Client:
    kwargs = {"timeout": 15}
    if proxy:
        kwargs["proxy"] = proxy
    return httpx.Client(**kwargs)


def _url(api_base: str | None, token: str, method: str) -> str:
    base = (api_base or DEFAULT_API_BASE).rstrip("/")
    return f"{base}/bot{token}/{method}"


def get_me(token: str, api_base: str | None = None, proxy: str | None = None) -> dict:
    if not token:
        raise RuntimeError("未配置 Bot Token")
    with _client(proxy) as c:
        resp = c.get(_url(api_base, token, "getMe"))
        resp.raise_for_status()
        return resp.json()


def main_keyboard() -> dict:
    """Telegram 底部常驻键盘。"""
    return {
        "keyboard": [["服务状态", "订阅列表", "编辑订阅"]],
        "resize_keyboard": True,
        "is_persistent": True,
    }


def send_message(
    chat_id: str,
    text: str,
    token: str,
    api_base: str | None = None,
    proxy: str | None = None,
    parse_mode: str = "Markdown",
    reply_markup: dict | None = None,
) -> dict:
    if not token:
        raise RuntimeError("未配置 Bot Token")
    with _client(proxy) as c:
        payload = {"chat_id": chat_id, "text": text, "parse_mode": parse_mode}
        if reply_markup:
            payload["reply_markup"] = reply_markup
        resp = c.post(
            _url(api_base, token, "sendMessage"),
            json=payload,
        )
        resp.raise_for_status()
        return resp.json()


def get_updates(
    token: str,
    api_base: str | None = None,
    proxy: str | None = None,
    offset: int | None = None,
) -> dict:
    """辅助绑定：用户向 Bot 发消息后，从这里读取 chat_id。"""
    if not token:
        raise RuntimeError("未配置 Bot Token")
    with _client(proxy) as c:
        params = {}
        if offset is not None:
            params["offset"] = offset
        resp = c.get(_url(api_base, token, "getUpdates"), params=params)
        resp.raise_for_status()
        return resp.json()
