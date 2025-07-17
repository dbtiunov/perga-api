from datetime import date
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Dict

from app.core.database import get_db
from app.schemas.planner_day import (
    PlannerDayItem, PlannerDayItemCreate, PlannerDayItemUpdate,
    ReorderDayItemsRequest, CopyDayItemRequest, SnoozeDayItemRequest,
)
from app.services.planner_day_service import PlannerDayItemService
from app.services.auth_service import AuthService
from app.schemas.user import User

router = APIRouter()


@router.get("/items/", response_model=Dict[str, List[PlannerDayItem]])
def get_items_by_days(
    days: List[date] = Query(..., description="List of dates in ISO format (YYYY-MM-DD)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(AuthService.get_current_user)
):
    """
    Get multiple days by their dates and return a dictionary with date strings as keys and their items as values.
    Example request: /items/?days=2023-01-01&days=2023-01-02
    Result: {'2023-01-01': [...], '2023-01-02': [...]}
    """
    result = {}
    for day in days:
        items = PlannerDayItemService.get_items_by_day(db, day, current_user.id)
        result[day.isoformat()] = items
    return result


@router.post("/items/", response_model=PlannerDayItem)
def create_day_item(
    item: PlannerDayItemCreate, 
    db: Session = Depends(get_db),
    current_user: User = Depends(AuthService.get_current_user)
):
    return PlannerDayItemService.create_day_item(db=db, item=item, user_id=current_user.id)


@router.put("/items/{item_id}/", response_model=PlannerDayItem)
def update_day_item(
    item_id: int, 
    item: PlannerDayItemUpdate, 
    db: Session = Depends(get_db),
    current_user: User = Depends(AuthService.get_current_user)
):
    # Validate that the item exists and belongs to the current user
    db_item = PlannerDayItemService.get_day_item(db, item_id=item_id, user_id=current_user.id)
    if not db_item:
        raise HTTPException(status_code=404, detail="Item not found")

    db_item = PlannerDayItemService.update_day_item(db, item_id=item_id, item=item, user_id=current_user.id)
    return db_item


@router.delete("/items/{item_id}/", response_model=dict)
def delete_day_item(
    item_id: int, 
    db: Session = Depends(get_db),
    current_user: User = Depends(AuthService.get_current_user)
):
    # Validate that the item exists and belongs to the current user
    db_item = PlannerDayItemService.get_day_item(db, item_id=item_id, user_id=current_user.id)
    if not db_item:
        raise HTTPException(status_code=404, detail="Item not found")

    success = PlannerDayItemService.delete_day_item(db, item_id=item_id, user_id=current_user.id)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to delete item, try again later")
    return {"detail": "Item deleted successfully"}


@router.post("/items/reorder/", response_model=dict)
def reorder_day_items(
    request: ReorderDayItemsRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(AuthService.get_current_user)
):
    # Validate that the items exist and belong to the current user
    for item_id in request.ordered_item_ids:
        db_item = PlannerDayItemService.get_day_item(db, item_id=item_id, user_id=current_user.id)
        if not db_item:
            raise HTTPException(status_code=404, detail=f"One of the items was not found")

    success = PlannerDayItemService.reorder_day_items(db, request.ordered_item_ids, user_id=current_user.id)
    if not success:
        raise HTTPException(status_code=400, detail="Failed to reorder items, try again later")
    return {"detail": "Items reordered successfully"}


@router.post("/items/{item_id}/copy/", response_model=PlannerDayItem)
def copy_day_item(
    request: CopyDayItemRequest,
    item_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(AuthService.get_current_user)
):
    # Validate that the item exists and belongs to the current user
    db_item = PlannerDayItemService.get_day_item(db, item_id=item_id, user_id=current_user.id)
    if not db_item:
        raise HTTPException(status_code=404, detail="Item not found")

    new_db_item = PlannerDayItemService.copy_day_item(db, item_id=item_id, day=request.day, user_id=current_user.id)
    if not new_db_item:
        raise HTTPException(status_code=404, detail="Failed to copy item, try again later.")
    return new_db_item


@router.post("/items/{item_id}/snooze/", response_model=PlannerDayItem)
def snooze_day_item(
    request: SnoozeDayItemRequest,
    item_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(AuthService.get_current_user)
):
    # Validate that the item exists and belongs to the current user
    db_item = PlannerDayItemService.get_day_item(db, item_id=item_id, user_id=current_user.id)
    if not db_item:
        raise HTTPException(status_code=404, detail="Item not found")

    new_db_item = PlannerDayItemService.snooze_day_item(db, item_id=item_id, day=request.day, user_id=current_user.id)
    if not new_db_item:
        raise HTTPException(status_code=404, detail="Failed to snooze item, try again later")
    return new_db_item
