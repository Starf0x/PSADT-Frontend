from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..db import Export, User, get_db
from ..security import current_user

router = APIRouter(prefix="/api/stats", tags=["stats"])


@router.get("")
def stats(db: Session = Depends(get_db), user: User = Depends(current_user)):
    """How many packages were exported: in total, by the signed-in user and per user."""
    rows = db.execute(
        select(Export.user_id, User.display_name, User.username, func.count(Export.id))
        .outerjoin(User, User.id == Export.user_id).group_by(Export.user_id).order_by(func.count(Export.id).desc())
    ).all()
    per_user = [{"name": (dn or un or "") if uid is not None else "", "count": n, "me": uid == user.id}
                for uid, dn, un, n in rows]
    return {"total": sum(r["count"] for r in per_user),
            "mine": next((r["count"] for r in per_user if r["me"]), 0),
            "per_user": per_user}
