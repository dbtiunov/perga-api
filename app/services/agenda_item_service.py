import logging
from enum import Enum
from sqlalchemy.orm import Session
from typing import List, Optional

from app.core.db_utils import atomic_transaction, TransactionRollback
from app.models.planner import PlannerAgendaItem
from app.schemas.planner_agenda import PlannerAgendaItemCreate, PlannerAgendaItemUpdate
from app.services.base_service import BaseService

logger = logging.getLogger(__name__)


class PlannerAgendaItemService(BaseService[PlannerAgendaItem]):
    model = PlannerAgendaItem

    @classmethod
    def get_new_item_index(cls, db: Session, agenda_id: int, user_id: int) -> int:
        query = cls.get_base_query(db).filter(
            PlannerAgendaItem.user_id == user_id,
            PlannerAgendaItem.agenda_id == agenda_id
        )
        max_index: PlannerAgendaItem = query.order_by(PlannerAgendaItem.index.desc()).first()
        return max_index.index + 1 if max_index else 0

    @classmethod
    def get_planner_item(cls, db: Session, item_id: int, user_id: int) -> Optional[PlannerAgendaItem]:
        query = cls.get_base_query(db).filter(
            PlannerAgendaItem.user_id == user_id,
            PlannerAgendaItem.id == item_id
        )
        return query.first()

    @classmethod
    def get_planner_items_by_agendas(cls, db: Session, agenda_id: int, user_id: int) -> List[PlannerAgendaItem]:
        query = cls.get_base_query(db).filter(
            PlannerAgendaItem.user_id == user_id,
            PlannerAgendaItem.agenda_id == agenda_id
        )
        return query.order_by(PlannerAgendaItem.index).all()

    @classmethod
    def create_planner_item(cls, db: Session, item: PlannerAgendaItemCreate, user_id: int) -> PlannerAgendaItem:
        new_index = cls.get_new_item_index(db, item.agenda_id, user_id)

        db_item = PlannerAgendaItem(**item.model_dump(), index=new_index, user_id=user_id)
        db.add(db_item)
        db.commit()

        db.refresh(db_item)
        return db_item

    @classmethod
    def update_planner_item(cls, db: Session, item_id: int, item: PlannerAgendaItemUpdate, user_id: int) -> Optional[PlannerAgendaItem]:
        db_item = cls.get_planner_item(db, item_id, user_id)
        if not db_item:
            return None

        update_data = item.model_dump(exclude_unset=True)
        for field, new_value in update_data.items():
            if isinstance(new_value, Enum):
                new_value = new_value.value
            setattr(db_item, field, new_value)
        db.commit()

        db.refresh(db_item)
        return db_item

    @classmethod
    def archive_planner_item(cls, db: Session, item_id: int, user_id: int) -> bool:
        db_item = cls.get_planner_item(db, item_id, user_id)
        if not db_item:
            return False

        db_item.archive()
        db.commit()

        return True

    @classmethod
    def reorder_items(cls, db: Session, ordered_item_ids: list[int], user_id: int) -> bool:
        try:
            with atomic_transaction(db):
                new_index = 0
                for item_id in ordered_item_ids:
                    db_item = cls.get_planner_item(db, item_id, user_id)
                    if db_item:
                        db_item.index = new_index
                    new_index += 1
        except TransactionRollback as e:
            logger.warning(f'reorder_items: {str(e)}')
            return False

        return True
