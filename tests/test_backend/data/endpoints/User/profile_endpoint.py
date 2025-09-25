def get_profile_endpoint(space_id: str):
    return {
        'path': '/getProfile',
        'headers': {
            'Content-Type': 'application/json',
            'Current-Space-Id': space_id,
        },
    }