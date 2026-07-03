"""Telegram 机器人被动交互：底部按钮、订阅查询与快速续费。"""
from __future__ import annotations

from datetime import date, timedelta
import re
import time

from sqlalchemy import select

from app import activity, database
from app.billing import add_cycle
from app.models import Subscription, User
from app.services import exchange, telegram

_offsets: dict[tuple[str, str, str], int] = {}
_RENEW_RE = re.compile(r"^续费\s*(\d+)$")
_STARTED_AT = int(time.time())


def _escape_md(text: str) -> str:
    if not text:
        return ""
    for ch in ("_", "*", "`", "["):
        text = text.replace(ch, "\\" + ch)
    return text


def run_bot_poll() -> None:
    """轮询已绑定用户的 Telegram 消息。"""
    if database.SessionLocal is None:
        return
    db = database.SessionLocal()
    try:
        users = db.scalars(
            select(User).where(
                User.telegram_enabled.is_(True),
                User.telegram_bot_token.is_not(None),
                User.telegram_chat_id.is_not(None),
            )
        ).all()
        groups: dict[tuple[str, str, str], dict[str, User]] = {}
        for user in users:
            if not user.telegram_bot_token or not user.telegram_chat_id:
                continue
            key = (
                user.telegram_bot_token,
                user.telegram_api_base or "",
                user.telegram_proxy or "",
            )
            groups.setdefault(key, {})[str(user.telegram_chat_id)] = user

        for key, users_by_chat in groups.items():
            token, api_base, proxy = key
            offset = _offsets.get(key)
            data = telegram.get_updates(
                token=token,
                api_base=api_base or None,
                proxy=proxy or None,
                offset=offset,
            )
            updates = data.get("result") or []
            if not updates:
                continue

            next_offset = max(int(u.get("update_id", 0)) for u in updates) + 1
            first_poll = key not in _offsets
            if key not in _offsets:
                # 首次启动时跳过历史消息，但保留服务启动后刚点的按钮。
                _offsets[key] = next_offset
                updates = [
                    u
                    for u in updates
                    if int(
                        (
                            u.get("message")
                            or u.get("edited_message")
                            or {}
                        ).get("date", 0)
                    )
                    >= _STARTED_AT - 5
                ]
                if not updates:
                    continue
            else:
                _offsets[key] = next_offset

            for update in updates:
                msg = update.get("message") or update.get("edited_message") or {}
                chat = msg.get("chat") or {}
                text = (msg.get("text") or "").strip()
                chat_id = str(chat.get("id") or "")
                user = users_by_chat.get(chat_id)
                if not user or not text:
                    continue
                if first_poll:
                    print(f"[telegram-bot] processing recent message from chat {chat_id}: {text}")
                _handle_text(db, user, text)
        db.commit()
    except Exception as e:  # noqa: BLE001
        print(f"[telegram-bot] poll failed: {e}")
    finally:
        db.close()


def _send(user: User, text: str) -> None:
    telegram.send_message(
        user.telegram_chat_id,
        text,
        token=user.telegram_bot_token,
        api_base=user.telegram_api_base,
        proxy=user.telegram_proxy,
        reply_markup=telegram.main_keyboard(),
    )


def _handle_text(db, user: User, text: str) -> None:
    if text == "/start":
        _send(
            user,
            "已连接到 EasySub。\n\n"
            "底部按钮可以查看：服务状态、订阅列表、编辑订阅。\n"
            "快速续费可发送：`续费 订阅ID`",
        )
        return
    if text == "服务状态":
        _send(user, _service_status(db, user))
        return
    if text == "订阅列表":
        _send(user, _subscription_list(db, user))
        return
    if text == "编辑订阅":
        _send(user, _edit_help(db, user))
        return

    match = _RENEW_RE.match(text)
    if match:
        _renew_subscription(db, user, int(match.group(1)))


def _monthly_cost(db, sub: Subscription, base: str) -> float:
    amt = exchange.convert(db, sub.amount, sub.currency, base)
    count = max(1, sub.cycle_count)
    if sub.cycle == "day":
        return amt / count * 30
    if sub.cycle == "week":
        return amt / count * 52 / 12
    if sub.cycle == "month":
        return amt / count
    if sub.cycle == "year":
        return amt / count / 12
    return amt


def _service_status(db, user: User) -> str:
    today = date.today()
    horizon = today + timedelta(days=30)
    subs = db.scalars(select(Subscription).where(Subscription.user_id == user.id)).all()
    active = [s for s in subs if s.is_active]
    recurring = [s for s in active if s.billing_type == "recurring"]
    upcoming = [
        s for s in recurring if s.next_renewal_date and today <= s.next_renewal_date <= horizon
    ]
    expired = [s for s in recurring if s.next_renewal_date and s.next_renewal_date < today]
    month_spend = sum(_monthly_cost(db, s, user.base_currency) for s in recurring)
    return (
        "📊 *EasySub 服务状态*\n\n"
        f"生效订阅：*{len(active)}* 个\n"
        f"30 天内到期：*{len(upcoming)}* 个\n"
        f"已过期：*{len(expired)}* 个\n"
        f"月度折算：*{month_spend:.2f} {user.base_currency}*"
    )


def _subscription_list(db, user: User) -> str:
    today = date.today()
    subs = db.scalars(
        select(Subscription)
        .where(Subscription.user_id == user.id, Subscription.is_active.is_(True))
        .order_by(Subscription.next_renewal_date.is_(None), Subscription.next_renewal_date)
    ).all()
    if not subs:
        return "暂无生效订阅。"
    lines = ["📋 *订阅列表*", ""]
    for sub in subs[:25]:
        if sub.billing_type == "one_time":
            when = "一次性买断"
        elif sub.next_renewal_date:
            days = (sub.next_renewal_date - today).days
            when = f"{sub.next_renewal_date}（{days} 天）"
        else:
            when = "未设置到期日"
        lines.append(
            f"`{sub.id}` · *{_escape_md(sub.name)}* · {when} · {sub.amount:.2f} {sub.currency}"
        )
    if len(subs) > 25:
        lines.append(f"\n仅显示前 25 个，共 {len(subs)} 个。")
    return "\n".join(lines)


def _edit_help(db, user: User) -> str:
    today = date.today()
    horizon = today + timedelta(days=30)
    subs = db.scalars(
        select(Subscription).where(
            Subscription.user_id == user.id,
            Subscription.is_active.is_(True),
            Subscription.billing_type == "recurring",
            Subscription.next_renewal_date.is_not(None),
        )
    ).all()
    targets = sorted(
        [s for s in subs if s.next_renewal_date <= horizon],
        key=lambda s: s.next_renewal_date,
    )
    if not targets:
        return "30 天内没有需要处理的周期订阅。\n\n快速续费格式：`续费 订阅ID`"
    lines = ["🛠️ *编辑订阅*", "", "发送 `续费 订阅ID` 可按保号模式从今天重算周期。", ""]
    for sub in targets[:15]:
        days = (sub.next_renewal_date - today).days
        lines.append(f"`{sub.id}` · *{_escape_md(sub.name)}* · {sub.next_renewal_date}（{days} 天）")
    return "\n".join(lines)


def _renew_subscription(db, user: User, sub_id: int) -> None:
    sub = db.get(Subscription, sub_id)
    if not sub or sub.user_id != user.id:
        _send(user, f"没有找到订阅 ID：`{sub_id}`")
        return
    if sub.billing_type != "recurring":
        _send(user, f"`{sub.id}` · *{_escape_md(sub.name)}* 是一次性买断项目，无需续费。")
        return

    today = date.today()
    sub.start_date = today
    sub.next_renewal_date = add_cycle(today, sub.cycle, sub.cycle_count)
    sub.last_renewed_at = today
    activity.log(
        "telegram.renew",
        f"通过 Telegram 续费「{sub.name}」，下次到期 {sub.next_renewal_date}",
        user=user,
    )
    _send(user, f"✅ 已续费 *{_escape_md(sub.name)}*\n\n下次到期：*{sub.next_renewal_date}*")
