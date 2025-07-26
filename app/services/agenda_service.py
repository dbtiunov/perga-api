import logging
from datetime import datetime, date
from sqlalchemy.orm import Session

from app.core.db_utils import atomic_transaction, TransactionRollback
from app.models.choices import PlannerAgendaType
from app.models.planner import PlannerAgenda, PlannerAgendaItem
from app.schemas.planner_agenda import PlannerAgendaCreate, PlannerAgendaUpdate
from app.services.base_service import BaseService

logger = logging.getLogger(__name__)


class PlannerAgendaService(BaseService[PlannerAgenda]):
    model = PlannerAgenda

    @classmethod
    def get_new_agenda_index(cls, db: Session, user_id) -> int:
        query = cls.get_base_query(db).filter(PlannerAgenda.user_id == user_id)
        max_index_agenda = query.order_by(PlannerAgenda.index.desc()).first()
        return max_index_agenda.index + 1 if max_index_agenda else 0

    @classmethod
    def get_planner_agenda(cls, db: Session, agenda_id: int, user_id: int) -> PlannerAgenda | None:
        query = cls.get_base_query(db).filter(
            PlannerAgenda.user_id == user_id,
            PlannerAgenda.id == agenda_id
        )
        return query.first()

    @classmethod
    def get_planner_agendas_by_day(cls, db: Session, user_id: int, day: date) -> PlannerAgenda | None:
        base_query = cls.get_base_query(db).filter(PlannerAgenda.user_id == user_id)

        # Check if "Backlog" agenda exists for this user
        backlog_agenda = base_query.filter(
            PlannerAgenda.agenda_type == PlannerAgendaType.BACKLOG.value
        ).first()

        # If "Backlog" agenda doesn't exist for this user, create it
        if not backlog_agenda:
            from app.schemas.planner_agenda import PlannerAgendaCreate
            backlog_agenda_create = PlannerAgendaCreate(
                name="Backlog",
                agenda_type=PlannerAgendaType.BACKLOG.value,
                index=1
            )
            cls.create_planner_agenda(db, backlog_agenda_create, user_id)

        if not day:
            day = datetime.now()

        monthly_name = day.strftime("%B %Y")
        monthly_agenda = base_query.filter(
            PlannerAgenda.name == monthly_name,
            PlannerAgenda.agenda_type == PlannerAgendaType.MONTHLY.value
        ).first()

        # If month agenda doesn't exist for this user, create it
        if not monthly_agenda:
            from app.schemas.planner_agenda import PlannerAgendaCreate
            monthly_agenda_create = PlannerAgendaCreate(
                name=monthly_name,
                agenda_type=PlannerAgendaType.MONTHLY.value,
                index=0
            )
            cls.create_planner_agenda(db, monthly_agenda_create, user_id)

        return base_query.filter(
            (PlannerAgenda.agenda_type == PlannerAgendaType.BACKLOG.value) |
            ((PlannerAgenda.agenda_type == PlannerAgendaType.MONTHLY.value) & (PlannerAgenda.name == monthly_name))
        ).order_by(PlannerAgenda.index).all()

    @classmethod
    def create_planner_agenda(cls, db: Session, agenda_item: PlannerAgendaCreate, user_id: int) -> PlannerAgenda:
        if agenda_item.index is None:
            agenda_item.index = cls.get_new_agenda_index(db, user_id)

        db_agenda = PlannerAgenda(**agenda_item.model_dump(), user_id=user_id)
        db.add(db_agenda)
        db.commit()

        db.refresh(db_agenda)
        return db_agenda

    @classmethod
    def update_planner_agenda(
        cls, db: Session, agenda_id: int, agenda_item: PlannerAgendaUpdate, user_id: int
    ) -> PlannerAgenda | None:
        db_agenda = cls.get_planner_agenda(db, agenda_id, user_id)
        if not db_agenda:
            return None

        update_data = agenda_item.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_agenda, field, value)
        db.commit()

        db.refresh(db_agenda)
        return db_agenda

    @classmethod
    def archive_planner_agenda(cls, db: Session, agenda_id: int, user_id: int) -> bool:
        db_agenda = cls.get_planner_agenda(db, agenda_id, user_id)
        if not db_agenda:
            return False

        # Archive all items in this agenda
        db.query(PlannerAgendaItem).filter(
            PlannerAgendaItem.is_archived.is_(False),
            PlannerAgendaItem.agenda_id == agenda_id
        ).update({
            'is_archived': True,
            'archived_dt': datetime.now()
        })
        db_agenda.archive()
        db.commit()

        return True

    @classmethod
    def reorder_agendas(cls, db: Session, ordered_agenda_ids: list[int], user_id: int) -> bool:
        new_index = 0

        try:
            with atomic_transaction(db):
                for agenda_id in ordered_agenda_ids:
                    db_agenda = cls.get_planner_agenda(db, agenda_id, user_id)
                    if db_agenda:
                        db_agenda.index = new_index
                    new_index += 1
        except TransactionRollback as e:
            logger.warning(f'reorder_agendas: {str(e)}')
            return False

        return True
