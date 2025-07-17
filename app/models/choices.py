from enum import Enum


class PlannerItemState(Enum):
    TODO = "todo"
    COMPLETED = "completed"
    SNOOZED = "snoozed"
    DROPPED = "dropped"


class PlannerAgendaType(Enum):
    BACKLOG = "backlog"
    MONTHLY = "monthly"
    CUSTOM = "custom"


class WeekStartDay(Enum):
    MONDAY = "monday"
    SUNDAY = "sunday"
