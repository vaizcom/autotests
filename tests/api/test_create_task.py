import time
from pprint import pprint

import pytest
from requests import request
from settings import API_URL

@pytest.mark.skip
def test_create_task_on_board():
    payload = {
        'assignees': [],
        'boardId': '662127aba13cc8fb663686f3',
        'completed': False,
        'dueEnd': None,
        'dueStart': None,
        # 'files': None,
        'group': "662a34883650db649385aaeb",
        'index': 3,
        'milestone': None,
        'parentTask': None,
        'name': 'autotest API ' + str(time.asctime()),
        'priority': 1,
        'types': [],
    }
    headers = {
        'Cookie': '_t=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpZCI6IjY2ZWQ1NDMzZDZiMWFhYzQxNjI1OWIyMCIsImlhdCI6MTcyNj'
                  'gyOTYxOSwiZXhwIjozMzI2MjgyOTYxOX0.gKnWN8TPnvpynqVUG6P4cHrzvqFqJqZD54tAA82nLh0',
        'CurrentSpaceId': '65c4bb9cdac495717995c039',
        'Content-Type': 'application/json',
    }
    response = request('POST', API_URL + 'CreateTask', headers=headers, json=payload)

    pprint(response.json())
    # assert response.status_code == 200
