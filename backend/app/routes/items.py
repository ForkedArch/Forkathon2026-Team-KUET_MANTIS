from fastapi import APIRouter, Depends, HTTPException, Request, File, UploadFile, Form, status
from sqlalchemy.orm import Session
from typing import Optional, List
from .. import schemas, models, auth, database
from ..utils.file_upload import save_upload_file
import os
import json

router = APIRouter(prefix="/api/items", tags=["items"])


@router.get("", response_model=List[schemas.ItemOut])
@router.get("/", response_model=List[schemas.ItemOut])
def list_items(
    category: Optional[str] = None,
    type: Optional[str] = None,
    zone: Optional[str] = None,
    zone_id: Optional[str] = None,
    search: Optional[str] = None,
    q: Optional[str] = None,
    available_only: Optional[bool] = None,
    db: Session = Depends(database.get_db)
):
    query = db.query(models.Item)
    if available_only is None or available_only:
        query = query.filter(models.Item.is_available == True)

    if category and category.upper() != "ALL":
        query = query.filter(models.Item.category.ilike(category))

    if type and type.upper() != "ALL":
        query = query.filter(models.Item.type == type.lower())

    target_zone = zone or zone_id
    if target_zone:
        query = query.filter(
            (models.Item.zone == target_zone) | (models.Item.zone_id == target_zone)
        )

    term = search or q
    if term:
        term_clean = term.strip()
        query = query.join(models.User, models.Item.owner_id == models.User.id).filter(
            models.Item.title.ilike(f"%{term_clean}%") |
            models.Item.description.ilike(f"%{term_clean}%") |
            models.Item.specs.ilike(f"%{term_clean}%") |
            models.User.name.ilike(f"%{term_clean}%") |
            models.User.dept.ilike(f"%{term_clean}%")
        )

    return query.order_by(models.Item.id.desc()).all()


@router.post("", status_code=201)
@router.post("/", status_code=201)
async def create_item(
    request: Request,
    db: Session = Depends(database.get_db),
    current_user: Optional[models.User] = Depends(auth.get_current_user_optional)
):
    content_type = request.headers.get("content-type", "")

    if "application/json" in content_type:
        try:
            payload = await request.json()
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid JSON payload")

        title = payload.get("title")
        category = payload.get("category", "Other")
        item_type = payload.get("type", "lend")
        description = payload.get("description") or payload.get("specs")
        specs = payload.get("specs") or description
        condition = payload.get("condition", "Good")
        zone = payload.get("zone") or payload.get("zone_id")
        lat = payload.get("latitude") if payload.get("latitude") is not None else payload.get("lat")
        lng = payload.get("longitude") if payload.get("longitude") is not None else payload.get("lng")
        image_url = payload.get("image_url") or payload.get("image")
        tags = payload.get("tags") or []
        status_val = payload.get("status") or ("beacon" if item_type == "borrow" else "available")
        roll = payload.get("roll")
        owner_id = payload.get("owner_id")
    else:
        form = await request.form()
        title = form.get("title")
        category = form.get("category", "Other")
        item_type = form.get("type", "lend")
        description = form.get("description") or form.get("specs")
        specs = form.get("specs") or description
        condition = form.get("condition", "Good")
        zone = form.get("zone") or form.get("zone_id")
        lat_val = form.get("latitude") or form.get("lat")
        lat = float(lat_val) if lat_val is not None and str(lat_val).strip() != "" else None
        lng_val = form.get("longitude") or form.get("lng")
        lng = float(lng_val) if lng_val is not None and str(lng_val).strip() != "" else None
        image_url = form.get("image_url") or form.get("image")
        image_file = form.get("image")
        if image_file and hasattr(image_file, "filename") and image_file.filename:
            image_url = await save_upload_file(image_file, os.getenv("UPLOAD_DIR", "./uploads"))
        tags_raw = form.get("tags")
        if tags_raw:
            if isinstance(tags_raw, str) and tags_raw.startswith("["):
                try:
                    tags = json.loads(tags_raw)
                except Exception:
                    tags = [tags_raw]
            else:
                tags = [tags_raw]
        else:
            tags = []
        status_val = form.get("status") or ("beacon" if item_type == "borrow" else "available")
        roll = form.get("roll")
        owner_id = form.get("owner_id")

    if not title or not str(title).strip():
        raise HTTPException(status_code=422, detail="Title is required and cannot be empty")
    title = str(title).strip()

    if item_type not in ("lend", "borrow"):
        raise HTTPException(status_code=422, detail="Item type must be 'lend' or 'borrow'")

    # Resolve owner
    owner = current_user
    if not owner and owner_id:
        owner = db.query(models.User).filter(models.User.id == int(owner_id)).first()
    if not owner and roll:
        owner = db.query(models.User).filter(models.User.roll == str(roll)).first()
    if not owner:
        owner = db.query(models.User).first()
    if not owner:
        raise HTTPException(status_code=401, detail="No authenticated user or student owner available")

    new_item = models.Item(
        title=title,
        category=category,
        type=item_type,
        description=description,
        specs=specs,
        condition=condition,
        zone=zone,
        zone_id=zone,
        latitude=lat,
        longitude=lng,
        image_url=image_url,
        tags=tags,
        status=status_val,
        is_available=True,
        owner_id=owner.id
    )
    db.add(new_item)
    db.commit()
    db.refresh(new_item)

    item_out = schemas.ItemOut.model_validate(new_item).model_dump()
    return {
        "success": True,
        "item": item_out,
        **item_out
    }


@router.get("/{item_id}", response_model=schemas.ItemOut)
def get_item(item_id: int, db: Session = Depends(database.get_db)):
    item = db.query(models.Item).filter(models.Item.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    return item


@router.put("/{item_id}", response_model=schemas.ItemOut)
def update_item(
    item_id: int,
    item_update: schemas.ItemBase,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    item = db.query(models.Item).filter(models.Item.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    if item.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    for key, value in item_update.model_dump(exclude_unset=True).items():
        if hasattr(item, key):
            setattr(item, key, value)
    db.commit()
    db.refresh(item)
    return item


@router.delete("/{item_id}")
def delete_item(
    item_id: int,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    item = db.query(models.Item).filter(models.Item.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    if item.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    db.delete(item)
    db.commit()
    return {"detail": "Item deleted"}


@router.post("/{item_id}/save")
def toggle_save_item(
    item_id: int,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    """Toggle save/bookmark for an item."""
    item = db.query(models.Item).filter(models.Item.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")

    saved = (
        db.query(models.SavedItem)
        .filter(models.SavedItem.user_id == current_user.id, models.SavedItem.item_id == item_id)
        .first()
    )
    if saved:
        db.delete(saved)
        db.commit()
        return {"saved": False, "message": "Item removed from wishlist"}
    else:
        new_saved = models.SavedItem(user_id=current_user.id, item_id=item_id)
        db.add(new_saved)
        db.commit()
        return {"saved": True, "message": "Item added to wishlist"}


@router.get("/saved/all", response_model=List[schemas.ItemOut])
def get_saved_items(
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    """Get all saved items for the current user."""
    saved_entries = (
        db.query(models.SavedItem)
        .filter(models.SavedItem.user_id == current_user.id)
        .order_by(models.SavedItem.created_at.desc())
        .all()
    )
    return [entry.item for entry in saved_entries if entry.item]


@router.post("/{item_id}/report", response_model=schemas.ReportOut)
def report_item(
    item_id: int,
    report_data: schemas.ReportCreate,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    """Report an inappropriate or broken listing."""
    item = db.query(models.Item).filter(models.Item.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")

    report = models.Report(
        item_id=item_id,
        reporter_id=current_user.id,
        reason=report_data.reason,
        details=report_data.details,
    )
    db.add(report)
    db.commit()
    db.refresh(report)
    return report

