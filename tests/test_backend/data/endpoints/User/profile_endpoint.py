def get_profile_endpoint(space_id: str):
    return {
        'path': '/getProfile',
        'headers': {
            'Current-Space-Id': space_id,
        },
    }