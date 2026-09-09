from fastapi import APIRouter, Depends, HTTPException, File, UploadFile, Form
from sqlalchemy.orm import Session
from typing import Optional, List
from .. import schemas, models, auth, database
from ..utils.file_upload import save_upload_file
import os

router = APIRouter(prefix="/api/items", tags=["items"])

@router.get("/", response_model=List[schemas.ItemOut])
def list_items(
    category: Optional[str] = None,
    zone: Optional[str] = None,
    search: Optional[str] = None,
    db: Session = Depends(database.get_db)
):
    query = db.query(models.Item).filter(models.Item.is_available == True)
    if category:
        query = query.filter(models.Item.category == category)
    if zone:
        query = query.filter(models.Item.zone == zone)
    if search:
        query = query.filter(
            models.Item.title.ilike(f"%{search}%") |
            models.Item.description.ilike(f"%{search}%")
        )
    return query.all()

@router.post("/", response_model=schemas.ItemOut)
async def create_item(
    title: str = Form(...),
    category: str = Form(...),
    description: Optional[str] = Form(None),
    condition: Optional[str] = Form(None),
    zone: Optional[str] = Form(None),
    latitude: Optional[float] = Form(None),
    longitude: Optional[float] = Form(None),
    image: Optional[UploadFile] = File(None),
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    # Save image if uploaded. save_upload_file validates type/size and
    # raises HTTPException on anything not allowed.
    image_url = None
    if image:
        image_url = await save_upload_file(image, os.getenv("UPLOAD_DIR", "./uploads"))
    new_item = models.Item(
        title=title,
        category=category,
        description=description,
        condition=condition,
        zone=zone,
        latitude=latitude,
        longitude=longitude,
        image_url=image_url,
        owner_id=current_user.id
    )
    db.add(new_item)
    db.commit()
    db.refresh(new_item)
    return new_item

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
    for key, value in item_update.dict(exclude_unset=True).items():
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
