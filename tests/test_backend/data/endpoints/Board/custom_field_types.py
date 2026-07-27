from enum import Enum


class CustomFieldType(Enum):
    TEXT = 'Text'
    NUMBER = 'Number'
    CHECKBOX = 'Checkbox'
    DATE = 'Date'
    MEMBER = 'Member'
    TASK_RELATIONS = 'TaskRelations'
    SELECT = 'Select'
    URL = 'Url'
    ESTIMATION = 'Estimation'

    @classmethod
    def list(cls):
        return [field.value for field in cls]
