from datetime import date
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.models.choices import PlannerAgendaType
from app.services.auth_service import AuthService
from app.core.database import get_db
from app.schemas.planner_agenda import (
    PlannerAgenda, PlannerAgendaCreate, PlannerAgendaUpdate,
    PlannerAgendaItem, PlannerAgendaItemCreate, PlannerAgendaItemUpdate,
    ReorderAgendaItemsRequest, ReorderAgendasRequest,
    CopyAgendaItemRequest, MoveAgendaItemRequest,
)
from app.services.agenda_service import PlannerAgendaService
from app.services.agenda_item_service import PlannerAgendaItemService
from app.schemas.user import User

router = APIRouter()


@router.get("/", response_model=list[PlannerAgenda])
def get_agendas(
    agenda_types: list[PlannerAgendaType] | None = Query(
        None, description="Agenda types to include: monthly, custom, archived"
    ),
    selected_day: date | None = Query(
        None, description="Reference day to resolve monthly agenda (defaults to today)"
    ),
    with_counts: bool | None = Query(False, description="Include agenda items counts"),
    db: Session = Depends(get_db),
    current_user: User = Depends(AuthService.get_current_user)
):
    agendas = PlannerAgendaService.get_planner_agendas(db, current_user.id, agenda_types, selected_day, with_counts)
    return agendas


@router.post("/", response_model=PlannerAgenda)
def create_planner_agenda(
    agenda_item: PlannerAgendaCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(AuthService.get_current_user)
):
    db_agenda = PlannerAgendaService.create_planner_agenda(db=db, agenda_item=agenda_item, user_id=current_user.id)
    return db_agenda


@router.put("/{agenda_id}/", response_model=PlannerAgenda)
def update_planner_agenda(
    agenda_id: int,
    agenda_item: PlannerAgendaUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(AuthService.get_current_user)
):
    # validate agenda_type for archive/unarchive actions
    if agenda_item.agenda_type and agenda_item.agenda_type not in [
        PlannerAgendaType.ARCHIVED.value, PlannerAgendaType.CUSTOM.value
    ]:
        raise HTTPException(status_code=400, detail="Bad request")

    # Check if the agenda belongs to the current user
    db_agenda = PlannerAgendaService.get_planner_agenda(db, agenda_id=agenda_id, user_id=current_user.id)
    if not db_agenda:
        raise HTTPException(status_code=404, detail="Planner agenda not found")

    # Then update it
    db_agenda = PlannerAgendaService.update_planner_agenda(
        db, agenda_id=agenda_id, agenda_item=agenda_item, user_id=current_user.id
    )
    return db_agenda


@router.delete("/{agenda_id}/", response_model=dict)
def delete_planner_agenda(
    agenda_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(AuthService.get_current_user)
):
    # First check if the agenda belongs to the current user
    db_agenda = PlannerAgendaService.get_planner_agenda(db, agenda_id=agenda_id, user_id=current_user.id)
    if not db_agenda:
        raise HTTPException(status_code=404, detail="Planner agenda not found")

    # Then delete it
    success = PlannerAgendaService.delete_planner_agenda(db, agenda_id=agenda_id, user_id=current_user.id)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to delete planner agenda")
    return {"detail": "Planner agenda and its items deleted successfully"}


@router.post("/reorder/", response_model=dict)
def reorder_agendas(
    request: ReorderAgendasRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(AuthService.get_current_user)
):
    # First verify all agendas belong to the current user
    for agenda_id in request.ordered_agenda_ids:
        db_agenda = PlannerAgendaService.get_planner_agenda(db, agenda_id=agenda_id, user_id=current_user.id)
        if not db_agenda:
            raise HTTPException(status_code=404, detail=f"Planner agenda with id {agenda_id} not found")

    # Then reorder them
    success = PlannerAgendaService.reorder_agendas(db, request.ordered_agenda_ids, user_id=current_user.id)
    if not success:
        raise HTTPException(status_code=400, detail="Failed to reorder agendas")
    return {"detail": "Agendas reordered successfully"}


# Item routes
@router.post("/items/", response_model=PlannerAgendaItem)
def create_planner_agenda_item(
    item: PlannerAgendaItemCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(AuthService.get_current_user)
):
    # Check if agenda exists and belongs to the current user
    db_agenda = PlannerAgendaService.get_planner_agenda(db, item.agenda_id, user_id=current_user.id)
    if not db_agenda:
        raise HTTPException(status_code=404, detail="Planner agenda not found")

    return PlannerAgendaItemService.create_planner_item(db=db, item=item, user_id=current_user.id)


@router.put("/items/{item_id}/", response_model=PlannerAgendaItem)
def update_planner_agenda_item(
    item_id: int,
    item: PlannerAgendaItemUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(AuthService.get_current_user)
):
    # First check if the item exists and belongs to the current user
    db_item = PlannerAgendaItemService.get_planner_item(db, item_id=item_id, user_id=current_user.id)
    if not db_item:
        raise HTTPException(status_code=404, detail="Planner agenda item not found")

    # If agenda is being updated, check if it exists and belongs to the current user
    if item.agenda_id is not None:
        db_agenda = PlannerAgendaService.get_planner_agenda(db, item.agenda_id, user_id=current_user.id)
        if not db_agenda:
            raise HTTPException(status_code=404, detail="Target planner agenda not found")

    # Then update the item
    db_item = PlannerAgendaItemService.update_planner_item(db, item_id=item_id, item=item, user_id=current_user.id)
    return db_item


@router.delete("/items/{item_id}/", response_model=dict)
def delete_planner_agenda_item(
    item_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(AuthService.get_current_user)
):
    # First check if the item exists and belongs to the current user
    db_item = PlannerAgendaItemService.get_planner_item(db, item_id=item_id, user_id=current_user.id)
    if not db_item:
        raise HTTPException(status_code=404, detail="Planner agenda item not found")

    # Then delete it
    success = PlannerAgendaItemService.delete_planner_item(db, item_id=item_id, user_id=current_user.id)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to delete planner agenda item")
    return {"detail": "Planner agenda item deleted successfully"}


@router.post("/items/reorder/", response_model=dict)
def reorder_agenda_items(
    request: ReorderAgendaItemsRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(AuthService.get_current_user)
):
    # First verify all items belong to the current user
    for item_id in request.ordered_item_ids:
        db_item = PlannerAgendaItemService.get_planner_item(db, item_id=item_id, user_id=current_user.id)
        if not db_item:
            raise HTTPException(status_code=404, detail=f"Planner agenda item with id {item_id} not found")

    # Then reorder them
    success = PlannerAgendaItemService.reorder_items(db, request.ordered_item_ids, user_id=current_user.id)
    if not success:
        raise HTTPException(status_code=400, detail="Failed to reorder agenda items")
    return {"detail": "Agenda items reordered successfully"}


@router.get("/items/", response_model=dict[int, list[PlannerAgendaItem]])
def get_planner_items_by_agendas(
    agenda_ids: list[int] = Query(..., description="List of agenda IDs"),
    db: Session = Depends(get_db),
    current_user: User = Depends(AuthService.get_current_user)
):
    result = {}
    for agenda_id in agenda_ids:
        # Check if agenda exists and belongs to the current user
        db_agenda = PlannerAgendaService.get_planner_agenda(db, agenda_id, user_id=current_user.id)
        if not db_agenda:
            continue

        # Get items for this agenda
        items = PlannerAgendaItemService.get_planner_items_by_agendas(db, agenda_id, user_id=current_user.id)
        result[agenda_id] = items

    return result


@router.post("/items/{item_id}/copy/", response_model=PlannerAgendaItem)
def copy_planner_agenda_item(
    request: CopyAgendaItemRequest,
    item_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(AuthService.get_current_user)
):
    # Check that the item exists and belongs to the current user
    db_item = PlannerAgendaItemService.get_planner_item(db, item_id=item_id, user_id=current_user.id)
    if not db_item:
        raise HTTPException(status_code=404, detail="Planner agenda item not found")

    # Check that target agenda exists and belongs to the current user
    db_agenda = PlannerAgendaService.get_planner_agenda(db, request.agenda_id, user_id=current_user.id)
    if not db_agenda:
        raise HTTPException(status_code=404, detail="Target planner agenda not found")

    new_db_item = PlannerAgendaItemService.copy_agenda_item(
        db, item_id=item_id, agenda_id=request.agenda_id, user_id=current_user.id
    )
    if not new_db_item:
        raise HTTPException(status_code=400, detail="Failed to copy planner agenda item")
    return new_db_item


@router.post("/items/{item_id}/move/", response_model=PlannerAgendaItem)
def move_planner_agenda_item(
    request: MoveAgendaItemRequest,
    item_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(AuthService.get_current_user)
):
    # Check that the item exists and belongs to the current user
    db_item = PlannerAgendaItemService.get_planner_item(db, item_id=item_id, user_id=current_user.id)
    if not db_item:
        raise HTTPException(status_code=404, detail="Planner agenda item not found")

    # Check that target agenda exists and belongs to the current user
    db_agenda = PlannerAgendaService.get_planner_agenda(db, request.agenda_id, user_id=current_user.id)
    if not db_agenda:
        raise HTTPException(status_code=404, detail="Target planner agenda not found")

    new_db_item = PlannerAgendaItemService.move_agenda_item(
        db, item_id=item_id, agenda_id=request.agenda_id, user_id=current_user.id
    )
    if not new_db_item:
        raise HTTPException(status_code=400, detail="Failed to snooze planner agenda item")
    return new_db_item
