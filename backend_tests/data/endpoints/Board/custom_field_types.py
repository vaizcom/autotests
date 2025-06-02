from enum import Enum

class CustomFieldType(Enum):
    TEXT = "Text"
    NUMBER = "Number"
    CHECKBOX = "Boolean"
    DATE = "Date"
    MEMBER = "Member"
    TASK_RELATIONS = "TaskRelations"
    SELECT = "Select"

    @classmethod
    def list(cls):
        return [field.value for field in cls]
