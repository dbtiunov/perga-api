from sqlalchemy.orm import Session

from app.models.base import BaseModel
from app.services.base_service import BaseService


class TestModel(BaseModel):
    """A simple model for testing BaseService"""
    __tablename__ = "test_models"


class TestBaseService(BaseService[TestModel]):
    """A service class for testing BaseService"""
    model = TestModel


class TestBaseServiceFunctionality:
    """Tests for the BaseService class"""

    def test_get_base_query(self, test_db: Session):
        """Test that get_base_query returns a query filtered by is_archived=False"""
        # Create a test model instance
        test_model = TestModel()
        test_db.add(test_model)
        test_db.commit()
        
        # Create an archived test model instance
        archived_model = TestModel()
        archived_model.archive()
        test_db.add(archived_model)
        test_db.commit()
        
        # Get the base query
        query = TestBaseService.get_base_query(test_db)
        
        # Check that only non-archived models are returned
        results = query.all()
        assert len(results) == 1
        assert results[0].id == test_model.id
        assert not results[0].is_archived
