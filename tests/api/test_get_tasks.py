import pytest
from requests import request
from settings import API_URL

@pytest.mark.skip
# отображает все таске на конкретной борде
def test_get_tasks_on_board():
    headers = {
        'Cookie': '_t=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpZCI6IjY2YWEzNWU0OWFiYzM0M2M1NjRiOTk5ZSIsImlhdCI6MTcyMj'
                  'QzMDk0OCwiZXhwIjozMzI1ODQzMDk0OH0.0D_DA_XsI7jukhsXwVvWoO97dm4_6yVA2fRrLOUGnK4',
        'CurrentSpaceId': '65c4bb9cdac495717995c039',
        # 'board': '662127aba13cc8fb663686f3',
        # 'project': '65c4bc77dac495717995c1e2'
    }
    payload = {'board': '662127aba13cc8fb663686f3'}
    response = request('GET', API_URL + 'getTasks', headers=headers, json=payload)
    assert response.status_code == 200
