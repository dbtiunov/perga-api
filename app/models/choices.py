from enum import Enum


class PlannerItemState(Enum):
    TODO = "todo"
    COMPLETED = "completed"
    SNOOZED = "snoozed"
    DROPPED = "dropped"


class PlannerAgendaType(Enum):
    MONTHLY = "monthly"
    CUSTOM = "custom"


class WeekStartDay(Enum):
    MONDAY = "monday"
    SUNDAY = "sunday"
