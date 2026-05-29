import os
import uuid

from fastapi import APIRouter, Depends, HTTPException, UploadFile
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models.manual import DeviceManual
from app.schemas.manual import ManualCreate, ManualResponse, ManualSummary, ManualUpdate

router = APIRouter(prefix="/api/v1/manuals", tags=["manuals"])


@router.get("", response_model=list[ManualSummary])
def list_manuals(db: Session = Depends(get_db)):
    return db.query(DeviceManual).order_by(DeviceManual.created_at.desc()).all()


@router.post("", response_model=ManualResponse)
def create_manual(body: ManualCreate, db: Session = Depends(get_db)):
    manual = DeviceManual(**body.model_dump())
    db.add(manual)
    db.commit()
    db.refresh(manual)
    return manual


@router.post("/upload", response_model=ManualResponse)
async def upload_manual_pdf(
    file: UploadFile,
    name: str = "",
    brand: str = "",
    category: str = "",
    db: Session = Depends(get_db),
):
    if not file.filename or not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="只支持 PDF 文件")

    content = await file.read()
    file_id = str(uuid.uuid4())
    manuals_dir = os.path.join(settings.DATA_DIR, "manuals")
    os.makedirs(manuals_dir, exist_ok=True)
    file_path = os.path.join(manuals_dir, f"{file_id}.pdf")

    with open(file_path, "wb") as f:
        f.write(content)

    manual = DeviceManual(
        name=name or file.filename.replace(".pdf", ""),
        brand=brand or None,
        category=category or None,
        content=f"[PDF文件: {file.filename}]",
        file_path=file_path,
    )
    db.add(manual)
    db.commit()
    db.refresh(manual)
    return manual


@router.get("/search", response_model=list[ManualSummary])
def search_manuals(q: str, db: Session = Depends(get_db)):
    try:
        sql = text("""
            SELECT dm.id, dm.name, dm.brand, dm.category, dm.tags, dm.created_at, dm.updated_at, dm.content, dm.file_path, dm.model_number
            FROM device_manuals_fts
            JOIN device_manuals dm ON dm.id = device_manuals_fts.rowid
            WHERE device_manuals_fts MATCH :query
            LIMIT 20
        """)
        rows = db.execute(sql, {"query": q}).fetchall()
        return [
            ManualSummary(id=r.id, name=r.name, brand=r.brand, category=r.category, tags=r.tags, created_at=r.created_at)
            for r in rows
        ]
    except Exception:
        like_q = f"%{q}%"
        return db.query(DeviceManual).filter(
            (DeviceManual.name.like(like_q)) | (DeviceManual.content.like(like_q))
        ).limit(20).all()


@router.get("/{manual_id}", response_model=ManualResponse)
def get_manual(manual_id: int, db: Session = Depends(get_db)):
    manual = db.get(DeviceManual, manual_id)
    if not manual:
        raise HTTPException(status_code=404, detail="说明书不存在")
    return manual


@router.put("/{manual_id}", response_model=ManualResponse)
def update_manual(manual_id: int, body: ManualUpdate, db: Session = Depends(get_db)):
    manual = db.get(DeviceManual, manual_id)
    if not manual:
        raise HTTPException(status_code=404, detail="说明书不存在")
    for field, value in body.model_dump(exclude_none=True).items():
        setattr(manual, field, value)
    db.commit()
    db.refresh(manual)
    return manual


@router.delete("/{manual_id}")
def delete_manual(manual_id: int, db: Session = Depends(get_db)):
    manual = db.get(DeviceManual, manual_id)
    if not manual:
        raise HTTPException(status_code=404, detail="说明书不存在")
    if manual.file_path and os.path.exists(manual.file_path):
        os.unlink(manual.file_path)
    db.delete(manual)
    db.commit()
    return {"deleted": True}
