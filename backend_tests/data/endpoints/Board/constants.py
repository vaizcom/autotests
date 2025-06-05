import random
import string
# backend_tests/constants/board_limits.py

# Максимальная длина названия борды
MAX_BOARD_NAME_LENGTH = 50

# Максимальная длина заголовка для опций в кастомных селектах
BOARD_CUSTOM_SELECT_OPTION_MAX_TITLE_LENGTH = 25

# Максимальная длина заголовка кастомного поля
BOARD_CUSTOM_FIELD_MAX_TITLE_LENGTH = 50

# Максимальная длина описания типа борды
BOARD_TYPE_MAX_DESCRIPTION_LENGTH = 1024

# Максимальная длина описания группы борд
BOARD_GROUP_MAX_DESCRIPTION_LENGTH = 1024

# Максимальная длина описания кастомного поля
BOARD_CUSTOM_FIELD_MAX_DESCRIPTION_LENGTH = 1024

# Максимальная длина описания опции кастомного поля
BOARD_CUSTOM_FIELD_OPTION_MAX_DESCRIPTION_LENGTH = 1024

# Максимальное допустимое значение лимита в группе борд
BOARD_GROUP_LIMIT_MAX_VALUE = 999

DEFAULT_BOARD_GROUP_NAME = 'Empty group'

DEFAULT_BOARD_GROUPS = [
    {"name": "Backlog"},
    {"name": "Todo"},
    {"name": "In Progress"},
    {"name": "Done"}
]

typesList = [
      { "label": 'Green', "icon": 'Circle', "color": 'mint' },
      { "label": 'Blue', "icon": 'Square', "color": 'blue' },
      { "label": 'Cobalt', "icon": 'Hexagon', "color": 'violet' },
      { "label": 'Pink', "icon": 'Rhombus', "color": 'magenta' },
      { "label": 'Orange', "icon": 'Triangle', "color": 'orange' },
    ]