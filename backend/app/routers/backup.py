"""数据备份与恢复：导出/导入当前用户的全部数据。

应对场景：重新部署后数据丢失。用户可随时把自己的订阅及自定义分类/付款方式/
捆绑包/货币导出为一个 JSON 文件离线保存，重装后再导入恢复。
数据按用户隔离——只导出/导入当前登录用户自己的数据。
"""
from datetime import date, datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app import activity
from app.billing import compute_next_renewal
from app.database import get_db
from app.deps import get_current_user
from app.models import Bundle, Category, Currency, PaymentMethod, Subscription, User

router = APIRouter(prefix="/api/backup", tags=["backup"])

EXPORT_VERSION = 1


def _sub_dict(s: Subscription) -> dict:
    return {
        "name": s.name,
        "plan": s.plan,
        "icon": s.icon,
        "url": s.url,
        "notes": s.notes,
        "remark": s.remark,
        "ipv4": s.ipv4,
        "ipv6": s.ipv6,
        "category_id": s.category_id,
        "payment_method_id": s.payment_method_id,
        "bundle_id": s.bundle_id,
        "amount": s.amount,
        "currency": s.currency,
        "billing_type": s.billing_type,
        "cycle": s.cycle,
        "cycle_count": s.cycle_count,
        "start_date": s.start_date.isoformat() if s.start_date else None,
        "next_renewal_date": s.next_renewal_date.isoformat() if s.next_renewal_date else None,
        "end_date": s.end_date.isoformat() if s.end_date else None,
        "last_renewed_at": s.last_renewed_at.isoformat() if s.last_renewed_at else None,
        "is_active": s.is_active,
        "auto_renew": s.auto_renew,
        "show_in_calendar": s.show_in_calendar,
        "sort": s.sort,
        "family_members": s.family_members,
        "remind_days_before": s.remind_days_before,
    }


@router.get("/export")
def export_data(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """导出当前用户的全部数据为 JSON。"""
    subs = db.scalars(select(Subscription).where(Subscription.user_id == user.id)).all()
    cats = db.scalars(select(Category).where(Category.user_id == user.id)).all()
    pms = db.scalars(select(PaymentMethod).where(PaymentMethod.user_id == user.id)).all()
    bundles = db.scalars(select(Bundle).where(Bundle.user_id == user.id)).all()
    currencies = db.scalars(
        select(Currency).where(Currency.is_custom.is_(True), Currency.user_id == user.id)
    ).all()

    return {
        "export_version": EXPORT_VERSION,
        "app": "EasySub",
        "exported_at": datetime.utcnow().isoformat(timespec="seconds"),
        "user": {
            "username": user.username,
            "base_currency": user.base_currency,
            "locale": user.locale,
            "theme": user.theme,
        },
        "categories": [
            {"id": c.id, "name": c.name, "icon": c.icon, "color": c.color, "sort": c.sort}
            for c in cats
        ],
        "payment_methods": [{"id": p.id, "name": p.name, "icon": p.icon} for p in pms],
        "bundles": [{"id": b.id, "name": b.name, "note": b.note} for b in bundles],
        "currencies": [
            {"code": c.code, "name": c.name, "symbol": c.symbol} for c in currencies
        ],
        "subscriptions": [_sub_dict(s) for s in subs],
    }


class ImportIn(BaseModel):
    data: dict
    replace: bool = False  # True：导入前先清空当前用户的全部订阅


def _parse_date(v):
    try:
        return date.fromisoformat(v) if v else None
    except (TypeError, ValueError):
        return None


@router.post("/import")
def import_data(
    payload: ImportIn,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """从导出的 JSON 恢复数据。自定义分类/付款方式/捆绑包按名称匹配，缺失则新建。"""
    data = payload.data or {}
    subs_in = data.get("subscriptions")
    if not isinstance(subs_in, list):
        raise HTTPException(400, "备份文件格式不正确：缺少 subscriptions")

    if payload.replace:
        for s in db.scalars(
            select(Subscription).where(Subscription.user_id == user.id)
        ).all():
            db.delete(s)
        db.flush()

    # 现有可用实体（当前用户的 + 系统预置的），按名称去重，避免重复创建
    existing_cats = {
        c.name: c
        for c in db.scalars(
            select(Category).where(
                or_(Category.user_id == user.id, Category.is_system.is_(True))
            )
        ).all()
    }
    existing_pms = {
        p.name: p
        for p in db.scalars(
            select(PaymentMethod).where(
                or_(PaymentMethod.user_id == user.id, PaymentMethod.is_system.is_(True))
            )
        ).all()
    }
    existing_bundles = {
        b.name: b
        for b in db.scalars(select(Bundle).where(Bundle.user_id == user.id)).all()
    }

    cat_map: dict[int, int] = {}
    pm_map: dict[int, int] = {}
    bundle_map: dict[int, int] = {}

    for c in data.get("categories", []) or []:
        name = c.get("name")
        if not name:
            continue
        target = existing_cats.get(name)
        if not target:
            target = Category(
                name=name, icon=c.get("icon"), color=c.get("color"),
                sort=c.get("sort", 0), user_id=user.id, is_system=False,
            )
            db.add(target)
            db.flush()
            existing_cats[name] = target
        if c.get("id") is not None:
            cat_map[c["id"]] = target.id

    for p in data.get("payment_methods", []) or []:
        name = p.get("name")
        if not name:
            continue
        target = existing_pms.get(name)
        if not target:
            target = PaymentMethod(name=name, icon=p.get("icon"), user_id=user.id, is_system=False)
            db.add(target)
            db.flush()
            existing_pms[name] = target
        if p.get("id") is not None:
            pm_map[p["id"]] = target.id

    for b in data.get("bundles", []) or []:
        name = b.get("name")
        if not name:
            continue
        target = existing_bundles.get(name)
        if not target:
            target = Bundle(name=name, note=b.get("note"), user_id=user.id)
            db.add(target)
            db.flush()
            existing_bundles[name] = target
        if b.get("id") is not None:
            bundle_map[b["id"]] = target.id

    for cu in data.get("currencies", []) or []:
        code = (cu.get("code") or "").upper()
        if code and not db.get(Currency, code):
            db.add(
                Currency(
                    code=code, name=cu.get("name", code), symbol=cu.get("symbol", ""),
                    is_custom=True, user_id=user.id,
                )
            )
    db.flush()

    count = 0
    for s in subs_in:
        start = _parse_date(s.get("start_date")) or date.today()
        billing_type = s.get("billing_type", "recurring")
        sub = Subscription(
            user_id=user.id,
            name=s.get("name") or "导入订阅",
            plan=s.get("plan"),
            icon=s.get("icon"),
            url=s.get("url"),
            notes=s.get("notes"),
            remark=s.get("remark"),
            ipv4=s.get("ipv4"),
            ipv6=s.get("ipv6"),
            category_id=cat_map.get(s.get("category_id")),
            payment_method_id=pm_map.get(s.get("payment_method_id")),
            bundle_id=bundle_map.get(s.get("bundle_id")),
            amount=s.get("amount", 0.0) or 0.0,
            currency=s.get("currency") or user.base_currency,
            billing_type=billing_type,
            cycle=s.get("cycle", "month"),
            cycle_count=s.get("cycle_count", 1) or 1,
            start_date=start,
            next_renewal_date=_parse_date(s.get("next_renewal_date")),
            end_date=_parse_date(s.get("end_date")),
            last_renewed_at=_parse_date(s.get("last_renewed_at")),
            is_active=s.get("is_active", True),
            auto_renew=s.get("auto_renew", True),
            show_in_calendar=s.get("show_in_calendar", True),
            sort=s.get("sort", 0) or 0,
            family_members=s.get("family_members"),
            remind_days_before=s.get("remind_days_before", "7,1") or "7,1",
        )
        if billing_type == "recurring" and not sub.next_renewal_date:
            sub.next_renewal_date = compute_next_renewal(start, sub.cycle, sub.cycle_count)
        if billing_type == "one_time":
            sub.next_renewal_date = None
        db.add(sub)
        count += 1

    db.commit()
    activity.log("backup.import", f"导入恢复了 {count} 个订阅", user=user)
    return {"ok": True, "imported": count}
