import pytest
from datetime import date, timedelta

from sqlalchemy.orm import Session

from app.models.choices import PlannerItemState
from app.models.planner import PlannerDayItem
from app.schemas.planner_day import PlannerDayItemCreate, PlannerDayItemUpdate
from app.services.planner_day_service import PlannerDayItemService


class TestPlannerDayItemService:
    """Tests for the PlannerDayItemService class"""

    @pytest.fixture
    def test_day(self):
        """Return a test date for the tests"""
        return date.today()

    def test_get_new_item_index(self, test_db: Session, test_user, test_day):
        """Test that get_new_item_index returns the correct index"""
        # When there are no items, index should be 0
        index = PlannerDayItemService.get_new_item_index(test_db, test_day, test_user.id)
        assert index == 0

        # Create an item with index 0
        item = PlannerDayItem(
            text="Test Item",
            index=0,
            state=PlannerItemState.TODO.value,
            user_id=test_user.id,
            day=test_day
        )
        test_db.add(item)
        test_db.commit()

        # Now index should be 1
        index = PlannerDayItemService.get_new_item_index(test_db, test_day, test_user.id)
        assert index == 1

    def test_get_day_item(self, test_db: Session, test_user, test_day):
        """Test that get_day_item returns the correct item"""
        # Create an item
        item = PlannerDayItem(
            text="Test Item",
            index=0,
            state=PlannerItemState.TODO.value,
            user_id=test_user.id,
            day=test_day
        )
        test_db.add(item)
        test_db.commit()
        test_db.refresh(item)

        # Get the item
        db_item = PlannerDayItemService.get_day_item(test_db, item.id, test_user.id)
        assert db_item is not None
        assert db_item.id == item.id
        assert db_item.text == "Test Item"
        assert db_item.state == PlannerItemState.TODO.value
        assert db_item.day == test_day

        # Try to get a non-existent item
        db_item = PlannerDayItemService.get_day_item(test_db, 999, test_user.id)
        assert db_item is None

        # Try to get an item with a different user_id
        db_item = PlannerDayItemService.get_day_item(test_db, item.id, 999)
        assert db_item is None

    def test_get_items_by_day(self, test_db: Session, test_user, test_day):
        """Test that get_items_by_day returns the correct items"""
        # Create some items for today
        item1 = PlannerDayItem(
            text="Item 1",
            index=0,
            state=PlannerItemState.TODO.value,
            user_id=test_user.id,
            day=test_day
        )
        item2 = PlannerDayItem(
            text="Item 2",
            index=1,
            state=PlannerItemState.TODO.value,
            user_id=test_user.id,
            day=test_day
        )
        test_db.add_all([item1, item2])
        test_db.commit()

        # Create an item for tomorrow
        tomorrow = test_day + timedelta(days=1)
        item3 = PlannerDayItem(
            text="Item 3",
            index=0,
            state=PlannerItemState.TODO.value,
            user_id=test_user.id,
            day=tomorrow
        )
        test_db.add(item3)
        test_db.commit()

        # Get items for today
        items = PlannerDayItemService.get_items_by_day(test_db, test_day, test_user.id)
        assert len(items) == 2
        assert items[0].text == "Item 1"
        assert items[1].text == "Item 2"

        # Get items for tomorrow
        items = PlannerDayItemService.get_items_by_day(test_db, tomorrow, test_user.id)
        assert len(items) == 1
        assert items[0].text == "Item 3"

    def test_create_day_item(self, test_db: Session, test_user, test_day):
        """Test that create_day_item creates an item correctly"""
        # Create an item
        item_create = PlannerDayItemCreate(
            text="Test Item",
            state=PlannerItemState.TODO.value,
            day=test_day
        )
        db_item = PlannerDayItemService.create_day_item(test_db, item_create, test_user.id)
        
        # Check that the item was created correctly
        assert db_item.id is not None
        assert db_item.text == "Test Item"
        assert db_item.state == PlannerItemState.TODO.value
        assert db_item.day == test_day
        assert db_item.index == 0  # Should be the first item
        assert db_item.user_id == test_user.id

    def test_update_day_item(self, test_db: Session, test_user, test_day):
        """Test that update_day_item updates an item correctly"""
        # Create an item
        item = PlannerDayItem(
            text="Test Item",
            index=0,
            state=PlannerItemState.TODO.value,
            user_id=test_user.id,
            day=test_day
        )
        test_db.add(item)
        test_db.commit()
        test_db.refresh(item)
        
        # Update the item
        tomorrow = test_day + timedelta(days=1)
        item_update = PlannerDayItemUpdate(
            text="Updated Item",
            state=PlannerItemState.COMPLETED.value,
            day=tomorrow
        )
        db_item = PlannerDayItemService.update_day_item(test_db, item.id, item_update, test_user.id)
        
        # Check that the item was updated correctly
        assert db_item.id == item.id
        assert db_item.text == "Updated Item"
        assert db_item.state == PlannerItemState.COMPLETED.value
        assert db_item.day == tomorrow
        assert db_item.index == 0  # Unchanged
        
        # Try to update a non-existent item
        db_item = PlannerDayItemService.update_day_item(test_db, 999, item_update, test_user.id)
        assert db_item is None
        
        # Try to update an item with a different user_id
        db_item = PlannerDayItemService.update_day_item(test_db, item.id, item_update, 999)
        assert db_item is None

    def test_delete_day_item(self, test_db: Session, test_user, test_day):
        """Test that delete_day_item deletes an item correctly"""
        # Create an item
        item = PlannerDayItem(
            text="Test Item",
            index=0,
            state=PlannerItemState.TODO.value,
            user_id=test_user.id,
            day=test_day
        )
        test_db.add(item)
        test_db.commit()
        test_db.refresh(item)
        
        # Delete the item
        success = PlannerDayItemService.delete_day_item(test_db, item.id, test_user.id)
        assert success is True
        
        # Check that the item was marked as deleted
        db_item = test_db.query(PlannerDayItem).filter(PlannerDayItem.id == item.id).first()
        assert db_item.is_deleted is True
        assert db_item.deleted_dt is not None
        
        # Try to delete a non-existent item
        success = PlannerDayItemService.delete_day_item(test_db, 999, test_user.id)
        assert success is False
        
        # Try to delete an item with a different user_id
        success = PlannerDayItemService.delete_day_item(test_db, item.id, 999)
        assert success is False

    def test_reorder_day_items(self, test_db: Session, test_user, test_day):
        """Test that reorder_day_items reorders items correctly"""
        # Create some items
        item1 = PlannerDayItem(
            text="Item 1",
            index=0,
            state=PlannerItemState.TODO.value,
            user_id=test_user.id,
            day=test_day
        )
        item2 = PlannerDayItem(
            text="Item 2",
            index=1,
            state=PlannerItemState.TODO.value,
            user_id=test_user.id,
            day=test_day
        )
        item3 = PlannerDayItem(
            text="Item 3",
            index=2,
            state=PlannerItemState.TODO.value,
            user_id=test_user.id,
            day=test_day
        )
        test_db.add_all([item1, item2, item3])
        test_db.commit()
        test_db.refresh(item1)
        test_db.refresh(item2)
        test_db.refresh(item3)
        
        # Reorder the items (3, 1, 2)
        success = PlannerDayItemService.reorder_day_items(test_db, [item3.id, item1.id, item2.id], test_user.id)
        assert success is True
        
        # Check that the items were reordered correctly
        db_item1 = test_db.query(PlannerDayItem).filter(PlannerDayItem.id == item1.id).first()
        db_item2 = test_db.query(PlannerDayItem).filter(PlannerDayItem.id == item2.id).first()
        db_item3 = test_db.query(PlannerDayItem).filter(PlannerDayItem.id == item3.id).first()
        assert db_item3.index == 0
        assert db_item1.index == 1
        assert db_item2.index == 2

    def test_copy_day_item(self, test_db: Session, test_user, test_day):
        """Test that copy_day_item copies an item correctly"""
        # Create an item
        item = PlannerDayItem(
            text="Test Item",
            index=0,
            state=PlannerItemState.TODO.value,
            user_id=test_user.id,
            day=test_day
        )
        test_db.add(item)
        test_db.commit()
        test_db.refresh(item)
        
        # Copy the item to tomorrow
        tomorrow = test_day + timedelta(days=1)
        copied_item = PlannerDayItemService.copy_day_item(test_db, item.id, tomorrow, test_user.id)
        
        # Check that the item was copied correctly
        assert copied_item.id != item.id  # New item
        assert copied_item.text == item.text
        assert copied_item.day == tomorrow
        assert copied_item.index == 0  # First item on the new day
        assert copied_item.user_id == test_user.id
        
        # Check that the original item is unchanged
        db_item = test_db.query(PlannerDayItem).filter(PlannerDayItem.id == item.id).first()
        assert db_item.state == PlannerItemState.TODO.value
        assert db_item.day == test_day
        
        # Try to copy a non-existent item
        copied_item = PlannerDayItemService.copy_day_item(test_db, 999, tomorrow, test_user.id)
        assert copied_item is None
        
        # Try to copy an item with a different user_id
        copied_item = PlannerDayItemService.copy_day_item(test_db, item.id, tomorrow, 999)
        assert copied_item is None

    def test_snooze_day_item(self, test_db: Session, test_user, test_day):
        """Test that snooze_day_item snoozes an item correctly"""
        # Create an item
        item = PlannerDayItem(
            text="Test Item",
            index=0,
            state=PlannerItemState.TODO.value,
            user_id=test_user.id,
            day=test_day
        )
        test_db.add(item)
        test_db.commit()
        test_db.refresh(item)
        
        # Snooze the item to tomorrow
        tomorrow = test_day + timedelta(days=1)
        snoozed_item = PlannerDayItemService.snooze_day_item(test_db, item.id, tomorrow, test_user.id)
        
        # Check that the new item was created correctly
        assert snoozed_item.id != item.id  # New item
        assert snoozed_item.text == item.text
        assert snoozed_item.day == tomorrow
        assert snoozed_item.index == 0  # First item on the new day
        assert snoozed_item.user_id == test_user.id
        
        # Check that the original item is marked as snoozed
        db_item = test_db.query(PlannerDayItem).filter(PlannerDayItem.id == item.id).first()
        assert db_item.state == PlannerItemState.SNOOZED.value
        assert db_item.day == test_day
        
        # Try to snooze a non-existent item
        snoozed_item = PlannerDayItemService.snooze_day_item(test_db, 999, tomorrow, test_user.id)
        assert snoozed_item is None
        
        # Try to snooze an item with a different user_id
        snoozed_item = PlannerDayItemService.snooze_day_item(test_db, item.id, tomorrow, 999)
        assert snoozed_item is None
