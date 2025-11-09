import logging
from datetime import datetime, timezone
from sqlalchemy.orm import Session

from app.const import PlannerItemState
from app.core.db_utils import atomic_transaction, TransactionRollback
from app.models.planner import PlannerAgendaItem
from app.schemas.planner_agenda import PlannerAgendaItemCreate, PlannerAgendaItemUpdate
from app.services.base_service import BaseService

logger = logging.getLogger(__name__)


class PlannerAgendaItemService(BaseService[PlannerAgendaItem]):
    model = PlannerAgendaItem

    @classmethod
    def get_new_agenda_item_index(cls, db: Session, agenda_id: int, user_id: int) -> int:
        query = cls.get_base_query(db).filter(
            PlannerAgendaItem.user_id == user_id,
            PlannerAgendaItem.agenda_id == agenda_id
        )
        max_index: PlannerAgendaItem = query.order_by(PlannerAgendaItem.index.desc()).first()
        return max_index.index + 1 if max_index else 0

    @classmethod
    def get_agenda_item(cls, db: Session, item_id: int, user_id: int) -> PlannerAgendaItem | None:
        query = cls.get_base_query(db).filter(
            PlannerAgendaItem.user_id == user_id,
            PlannerAgendaItem.id == item_id
        )
        return query.first()

    @classmethod
    def get_items_by_agendas(cls, db: Session, agenda_id: int, user_id: int) -> list[PlannerAgendaItem]:
        query = cls.get_base_query(db).filter(
            PlannerAgendaItem.user_id == user_id,
            PlannerAgendaItem.agenda_id == agenda_id
        )
        return query.order_by(PlannerAgendaItem.index).all()

    @classmethod
    def create_agenda_item(cls, db: Session, item: PlannerAgendaItemCreate, user_id: int) -> PlannerAgendaItem:
        new_index = cls.get_new_agenda_item_index(db, item.agenda_id, user_id)

        db_item = PlannerAgendaItem(**item.model_dump(), index=new_index, user_id=user_id)
        db.add(db_item)
        db.commit()

        db.refresh(db_item)
        return db_item

    @classmethod
    def update_agenda_item(
        cls, db: Session, item_id: int, item: PlannerAgendaItemUpdate, user_id: int
    ) -> PlannerAgendaItem | None:
        db_item = cls.get_agenda_item(db, item_id, user_id)
        if not db_item:
            return None

        update_data = item.model_dump(exclude_unset=True)
        for field, new_value in update_data.items():
            setattr(db_item, field, new_value)
        db.commit()

        db.refresh(db_item)
        return db_item

    @classmethod
    def delete_agenda_item(cls, db: Session, item_id: int, user_id: int) -> bool:
        db_item = cls.get_agenda_item(db, item_id, user_id)
        if not db_item:
            return False

        db_item.mark_as_deleted()
        db.commit()

        return True

    @classmethod
    def reorder_agenda_items(cls, db: Session, ordered_item_ids: list[int], user_id: int) -> bool:
        try:
            with atomic_transaction(db):
                new_index = 0
                for item_id in ordered_item_ids:
                    db_item = cls.get_agenda_item(db, item_id, user_id)
                    if db_item:
                        db_item.index = new_index
                    new_index += 1
        except TransactionRollback as e:
            logger.warning(f'reorder_items: {str(e)}')
            return False

        return True


    @classmethod
    def copy_agenda_item(cls, db: Session, item_id: int, agenda_id: int, user_id: int) -> PlannerAgendaItem | None:
        """ Create new item in specified agenda copying text from the original """
        db_item = cls.get_agenda_item(db, item_id, user_id)
        if not db_item:
            return None

        new_index = cls.get_new_agenda_item_index(db, agenda_id, user_id)
        new_db_item = PlannerAgendaItem(
            user_id=user_id,
            agenda_id=agenda_id,
            text=db_item.text,
            index=new_index,
        )
        db.add(new_db_item)
        db.commit()

        db.refresh(new_db_item)
        return new_db_item

    @classmethod
    def move_agenda_item(cls, db: Session, item_id: int, agenda_id: int, user_id: int) -> PlannerAgendaItem | None:
        """ Create a new copy in specified agenda and remove original agenda item """
        db_item = cls.get_agenda_item(db, item_id, user_id)
        if not db_item:
            return None

        try:
            with atomic_transaction(db):
                db_item.mark_as_deleted()

                new_index = cls.get_new_agenda_item_index(db, agenda_id, user_id)
                new_db_item = PlannerAgendaItem(
                    user_id=user_id,
                    agenda_id=agenda_id,
                    text=db_item.text,
                    state=db_item.state,
                    index=new_index,
                )
                db.add(new_db_item)
        except TransactionRollback as e:
            logger.warning(f'move_agenda_item: {str(e)}')
            return None

        db.refresh(new_db_item)
        return new_db_item

    @classmethod
    def delete_finished_agenda_items(cls, db: Session, agenda_id: int, user_id: int) -> bool:
        """ Marks all finished (completed, dropped, snoozed) items in agenda as deleted """
        cls.get_base_query(db).filter(
            PlannerAgendaItem.user_id == user_id,
            PlannerAgendaItem.agenda_id == agenda_id,
            PlannerAgendaItem.state.in_([
                PlannerItemState.COMPLETED, PlannerItemState.DROPPED, PlannerItemState.SNOOZED
            ])
        ).update({
            "is_deleted": True,
            "deleted_dt": datetime.now(timezone.utc),
        }, synchronize_session=False)
        db.commit()
        return True

    @classmethod
    def sort_agenda_items_by_state(cls, db: Session, agenda_id: int, user_id: int) -> bool:
        """ Reorders items so that completed come first, keeping relative order within groups """
        try:
            with atomic_transaction(db):
                items = cls.get_base_query(db).filter(
                    PlannerAgendaItem.user_id == user_id,
                    PlannerAgendaItem.agenda_id == agenda_id,
                ).order_by(PlannerAgendaItem.index).all()

                completed_items = [item for item in items if item.state == PlannerItemState.COMPLETED]
                snoozed_items = [item for item in items if item.state == PlannerItemState.SNOOZED]
                dropped_items = [item for item in items if item.state == PlannerItemState.DROPPED]
                todo_items = [item for item in items if item.state == PlannerItemState.TODO]

                for index, item in enumerate(completed_items + snoozed_items + dropped_items + todo_items):
                    item.index = index
        except TransactionRollback as e:
            logger.warning(f'sort_items_by_state: {str(e)}')
            return False

        return True
