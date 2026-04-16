import datetime as dt
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.config import settings
from app.schemas.planner_day import PlannerDayItemCreateSchema
from app.services.planner_day_service import PlannerDayItemService

class TestPlannerDayAPI:
    def test_get_items_by_range(self, client: TestClient, test_db: Session, test_user, auth_headers):
        start_date = dt.date(2026, 2, 2)
        dates = [start_date + dt.timedelta(days=i) for i in range(5)]
        for date in dates:
            PlannerDayItemService.create_day_item(
                test_db,
                item=PlannerDayItemCreateSchema(day=date, text=f'Item for {date}'),
                user_id=test_user.id
            )
            
        response = client.get(
            f'{settings.API_V1_STR}/planner/days/items/range/',
            params={'start_date': '2026-02-02', 'days_count': 3},
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert len(data) == 3
        assert '2026-02-02' in data
        assert '2026-02-03' in data
        assert '2026-02-04' in data
        assert '2026-02-05' not in data
        
        assert len(data['2026-02-02']) == 1
        assert data['2026-02-02'][0]['text'] == 'Item for 2026-02-02'
