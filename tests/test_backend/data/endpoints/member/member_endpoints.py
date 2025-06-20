def get_space_members_endpoint(space_id: str):
    return {
        'path': '/GetSpaceMembers',
        'headers': {
            'Content-Type': 'application/json',
            'Current-Space-Id': space_id,
        },
    }
