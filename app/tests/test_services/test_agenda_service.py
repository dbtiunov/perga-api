from sqlalchemy.orm import Session

from app.const import PlannerAgendaType, PLANNER_CUSTOM_AGENDA_INDEX_MIN
from app.models.planner import PlannerAgenda
from app.schemas.planner_agenda import PlannerAgendaCreate, PlannerAgendaUpdate
from app.services.agenda_service import PlannerAgendaService


class TestPlannerAgendaService:
    """Tests for the PlannerAgendaService class"""

    def test_archive_and_unarchive_agenda(self, test_db: Session, test_user):
        """Archiving CUSTOM agenda to ARCHIVED and then unarchiving back to CUSTOM"""
        # Create a CUSTOM agenda
        agenda = PlannerAgenda(
            name="To Archive",
            index=PLANNER_CUSTOM_AGENDA_INDEX_MIN,
            agenda_type=PlannerAgendaType.CUSTOM,
            user_id=test_user.id
        )
        test_db.add(agenda)
        test_db.commit()
        test_db.refresh(agenda)

        # Archive it (CUSTOM -> ARCHIVED)
        update = PlannerAgendaUpdate(agenda_type=PlannerAgendaType.ARCHIVED)
        archived = PlannerAgendaService.update_planner_agenda(test_db, agenda.id, update, test_user.id)
        assert archived is not None
        assert archived.agenda_type == PlannerAgendaType.ARCHIVED
        # Unchanged fields
        assert archived.name == "To Archive"
        assert archived.index == PLANNER_CUSTOM_AGENDA_INDEX_MIN

        # Unarchive it back (ARCHIVED -> CUSTOM)
        update_back = PlannerAgendaUpdate(agenda_type=PlannerAgendaType.CUSTOM)
        unarchived = PlannerAgendaService.update_planner_agenda(test_db, agenda.id, update_back, test_user.id)
        assert unarchived is not None
        assert unarchived.agenda_type == PlannerAgendaType.CUSTOM
        # Unchanged fields
        assert unarchived.name == "To Archive"
        assert unarchived.index == PLANNER_CUSTOM_AGENDA_INDEX_MIN

    def test_get_new_agenda_index(self, test_db: Session, test_user):
        """Test that get_new_agenda_index returns the correct index"""
        # When there are no agendas, index should be 1
        index = PlannerAgendaService.get_new_agenda_index(test_db, test_user.id)
        assert index == PLANNER_CUSTOM_AGENDA_INDEX_MIN

        # Create an agenda with index 1
        agenda = PlannerAgenda(
            name="Test Agenda",
            index=index,
            agenda_type=PlannerAgendaType.CUSTOM,
            user_id=test_user.id
        )
        test_db.add(agenda)
        test_db.commit()

        # Now index should be 2
        index = PlannerAgendaService.get_new_agenda_index(test_db, test_user.id)
        assert index == 2

    def test_get_planner_agenda(self, test_db: Session, test_user):
        """Test that get_planner_agenda returns the correct agenda"""
        # Create an agenda
        agenda = PlannerAgenda(
            name="Test Agenda",
            index=PLANNER_CUSTOM_AGENDA_INDEX_MIN,
            agenda_type=PlannerAgendaType.CUSTOM,
            user_id=test_user.id
        )
        test_db.add(agenda)
        test_db.commit()
        test_db.refresh(agenda)

        # Get the agenda
        db_agenda = PlannerAgendaService.get_planner_agenda(test_db, agenda.id, test_user.id)
        assert db_agenda is not None
        assert db_agenda.id == agenda.id
        assert db_agenda.name == "Test Agenda"
        assert db_agenda.agenda_type == PlannerAgendaType.CUSTOM

        # Try to get a non-existent agenda
        db_agenda = PlannerAgendaService.get_planner_agenda(test_db, 999, test_user.id)
        assert db_agenda is None

        # Try to get an agenda with a different user_id
        db_agenda = PlannerAgendaService.get_planner_agenda(test_db, agenda.id, 999)
        assert db_agenda is None

    def test_create_planner_agenda(self, test_db: Session, test_user):
        """Test that create_planner_agenda creates an agenda correctly"""
        # Create an agenda
        agenda_create = PlannerAgendaCreate(
            name="Test Agenda",
            agenda_type=PlannerAgendaType.CUSTOM,
            index=None  # Should be set automatically
        )
        db_agenda = PlannerAgendaService.create_planner_agenda(test_db, agenda_create, test_user.id)
        
        # Check that the agenda was created correctly
        assert db_agenda.id is not None
        assert db_agenda.name == "Test Agenda"
        assert db_agenda.agenda_type == PlannerAgendaType.CUSTOM
        assert db_agenda.index == PLANNER_CUSTOM_AGENDA_INDEX_MIN
        assert db_agenda.user_id == test_user.id

    def test_update_planner_agenda(self, test_db: Session, test_user):
        """Test that update_planner_agenda updates an agenda correctly"""
        # Create an agenda
        agenda = PlannerAgenda(
            name="Test Agenda",
            index=PLANNER_CUSTOM_AGENDA_INDEX_MIN,
            agenda_type=PlannerAgendaType.CUSTOM,
            user_id=test_user.id
        )
        test_db.add(agenda)
        test_db.commit()
        test_db.refresh(agenda)
        
        # Update the agenda
        agenda_update = PlannerAgendaUpdate(
            name="Updated Agenda"
        )
        db_agenda = PlannerAgendaService.update_planner_agenda(test_db, agenda.id, agenda_update, test_user.id)
        
        # Check that the agenda was updated correctly
        assert db_agenda.id == agenda.id
        assert db_agenda.name == "Updated Agenda"
        assert db_agenda.agenda_type == PlannerAgendaType.CUSTOM  # Unchanged
        
        # Try to update a non-existent agenda
        db_agenda = PlannerAgendaService.update_planner_agenda(test_db, 999, agenda_update, test_user.id)
        assert db_agenda is None
        
        # Try to update an agenda with a different user_id
        db_agenda = PlannerAgendaService.update_planner_agenda(test_db, agenda.id, agenda_update, 999)
        assert db_agenda is None

    def test_delete_planner_agenda(self, test_db: Session, test_user):
        """Test that delete_planner_agenda deletes an agenda correctly"""
        # Create an agenda
        agenda = PlannerAgenda(
            name="Test Agenda",
            index=PLANNER_CUSTOM_AGENDA_INDEX_MIN,
            agenda_type=PlannerAgendaType.CUSTOM,
            user_id=test_user.id
        )
        test_db.add(agenda)
        test_db.commit()
        test_db.refresh(agenda)
        
        # Delete the agenda
        success = PlannerAgendaService.delete_planner_agenda(test_db, agenda.id, test_user.id)
        assert success is True
        
        # Check that the agenda was marked as deleted
        db_agenda = test_db.query(PlannerAgenda).filter(PlannerAgenda.id == agenda.id).first()
        assert db_agenda.is_deleted is True
        assert db_agenda.deleted_dt is not None
        
        # Try to delete a non-existent agenda
        success = PlannerAgendaService.delete_planner_agenda(test_db, 999, test_user.id)
        assert success is False
        
        # Try to delete an agenda with a different user_id
        success = PlannerAgendaService.delete_planner_agenda(test_db, agenda.id, 999)
        assert success is False

    def test_reorder_agendas(self, test_db: Session, test_user):
        """Test that reorder_agendas reorders agendas correctly"""
        # Create some agendas
        agenda1 = PlannerAgenda(
            name="Agenda 1",
            index=PLANNER_CUSTOM_AGENDA_INDEX_MIN,
            agenda_type=PlannerAgendaType.CUSTOM,
            user_id=test_user.id
        )
        agenda2 = PlannerAgenda(
            name="Agenda 2",
            index=PLANNER_CUSTOM_AGENDA_INDEX_MIN + 1,
            agenda_type=PlannerAgendaType.CUSTOM,
            user_id=test_user.id
        )
        agenda3 = PlannerAgenda(
            name="Agenda 3",
            index=PLANNER_CUSTOM_AGENDA_INDEX_MIN + 2,
            agenda_type=PlannerAgendaType.CUSTOM,
            user_id=test_user.id
        )
        test_db.add_all([agenda1, agenda2, agenda3])
        test_db.commit()
        test_db.refresh(agenda1)
        test_db.refresh(agenda2)
        test_db.refresh(agenda3)
        
        # Reorder the agendas (3, 1, 2)
        success = PlannerAgendaService.reorder_agendas(test_db, [agenda3.id, agenda1.id, agenda2.id], test_user.id)
        assert success is True
        
        # Check that the agendas were reordered correctly
        db_agenda1 = test_db.query(PlannerAgenda).filter(PlannerAgenda.id == agenda1.id).first()
        db_agenda2 = test_db.query(PlannerAgenda).filter(PlannerAgenda.id == agenda2.id).first()
        db_agenda3 = test_db.query(PlannerAgenda).filter(PlannerAgenda.id == agenda3.id).first()
        assert db_agenda3.index == 1
        assert db_agenda1.index == 2
        assert db_agenda2.index == 3
