import pytest

pytestmark = [pytest.mark.backend]


def create_project_endpoint(name: str, color: str, icon: str, description: str, slug: str, space_id: str):
    return {
        'path': '/CreateProject',
        'json': {
            'name': name,
            'color': color,
            'icon': icon,
            'description': description,
            'slug': slug,
            'spaceId': space_id,
        },
        'headers': {'Content-Type': 'application/json', 'Current-Space-Id': space_id},
    }


def create_board_endpoint(
    name: str,
    temp_project: str,
    space_id: str,
    groups: list = None,
    typesList: list = None,
    customFields: list = None,
    description: str = None,
):
    payload = {
        'name': name,
        'project': temp_project,
        'groups': groups,
        'typesList': typesList,
        'customFields': customFields,
    }
    if description is not None:
        payload['description'] = description

    return {
        'path': '/CreateBoard',
        'json': payload,
        'headers': {'Content-Type': 'application/json', 'Current-Space-Id': space_id},
    }


def edit_project_endpoint(
    project_id: str,
    name: str = None,
    color: str = None,
    description: str = None,
    icon: str = None,
    slug: str = None,
    space_id: str = None,
):
    payload = {'projectId': project_id}
    if name is not None:
        payload['name'] = name
    if color is not None:
        payload['color'] = color
    if description is not None:
        payload['description'] = description
    if icon is not None:
        payload['icon'] = icon
    if slug is not None:
        payload['slug'] = slug

    return {
        'path': '/EditProject',
        'json': payload,
        'headers': {'Content-Type': 'application/json', 'Current-Space-Id': space_id},
    }


def get_projects_endpoint(space_id: str):
    return {
        'path': '/GetProjects',
        'json': {},
        'headers': {'Content-Type': 'application/json', 'Current-Space-Id': space_id},
    }


def get_project_endpoint(project_id: str, space_id: str):
    return {
        'path': '/GetProject',
        'json': {'projectId': project_id},
        'headers': {'Content-Type': 'application/json', 'Current-Space-Id': space_id},
    }


def is_project_slug_unique_endpoint(slug: str, space_id: str):
    return {
        'path': '/IsProjectSlugUnique',
        'json': {'slug': slug, 'spaceId': space_id},
        'headers': {'Content-Type': 'application/json', 'Current-Space-Id': space_id},
    }


def archive_project_endpoint(project_id: str, space_id: str):
    return {
        'path': '/ArchiveProject',
        'json': {'projectId': project_id},
        'headers': {'Content-Type': 'application/json', 'Current-Space-Id': space_id},
    }


def unarchive_project_endpoint(project_id: str, space_id: str):
    return {
        'path': '/UnarchiveProject',
        'json': {'projectId': project_id},
        'headers': {'Content-Type': 'application/json', 'Current-Space-Id': space_id},
    }
