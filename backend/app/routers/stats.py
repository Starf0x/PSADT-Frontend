from collections import Counter

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..db import Export, User, get_db
from ..security import current_user

router = APIRouter(prefix="/api/stats", tags=["stats"])


@router.get("")
def stats(db: Session = Depends(get_db), user: User = Depends(current_user)):
    """How many packages were made: in total, by the signed-in user and per user.

    A package counts once per version, however often it is downloaded and in whichever
    format (ZIP and .intunewin of the same build are one package). It is credited to
    whoever downloaded it first.
    """
    first: dict[tuple, int | None] = {}
    for pid, name, version, uid in db.execute(
            select(Export.package_id, Export.package_name, Export.app_version, Export.user_id).order_by(Export.id)):
        first.setdefault((pid if pid is not None else name, version or ""), uid)
    counts = Counter(first.values())
    names = {u.id: u.display_name or u.username for u in db.scalars(select(User).where(User.id.in_([k for k in counts if k])))}
    per_user = sorted(({"name": names.get(uid, "") if uid else "", "count": n, "me": uid == user.id}
                       for uid, n in counts.items()), key=lambda r: -r["count"])
    return {"total": len(first), "mine": counts.get(user.id, 0), "per_user": per_user}
