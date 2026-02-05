from enum import Enum


PLANNER_MONTHLY_AGENDA_INDEX = 0
PLANNER_CUSTOM_AGENDA_INDEX_MIN = 1


class PlannerItemState(str, Enum):
    TODO = "todo"
    COMPLETED = "completed"
    SNOOZED = "snoozed"
    DROPPED = "dropped"


class PlannerAgendaType(str, Enum):
    MONTHLY = "monthly"
    CUSTOM = "custom"
    ARCHIVED = "archived"


class WeekStartDay(str, Enum):
    MONDAY = "monday"
    SUNDAY = "sunday"


class PlannerAgendaAction(str, Enum):
    DELETE_FINISHED_ITEMS = "delete_finished_items"
    SORT_ITEMS_BY_STATE = "sort_items_by_state"
