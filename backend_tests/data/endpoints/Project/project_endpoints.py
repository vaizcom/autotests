MAX_PROJECT_NAME_LENGTH = 25
MAX_PROJECT_SLUG_LENGTH = 8
MAX_PROJECT_DESCRIPTION_LENGTH = 1024

def create_project_endpoint(name: str, color: str, icon: str, description: str, slug: str, space_id: str):
    return {
        "path": "/CreateProject",
        "json": {
            "name": name,
            "color": color,
            "icon": icon,
            "description": description,
            "slug": slug,
            "spaceId": space_id
        },
        "headers": {
            "Content-Type": "application/json",
            "Current-Space-Id": space_id
        }
    }

def edit_project_endpoint(project_id: str, name: str, space_id: str):
    return {
        "path": "/EditProject",
        "json": {
            "projectId": project_id,
            "name": name
        },
        "headers": {
            "Content-Type": "application/json",
            "Current-Space-Id": space_id
        }
    }

def get_projects_endpoint(space_id: str):
    return {
        "path": "/GetProjects",
        "json": {},
        "headers": {
            "Content-Type": "application/json",
            "Current-Space-Id": space_id
        }
    }

def get_project_endpoint(project_id: str, space_id: str):
    return {
        "path": "/GetProject",
        "json": {
            "projectId": project_id
        },
        "headers": {
            "Content-Type": "application/json",
            "Current-Space-Id": space_id
        }
    }

def is_project_slug_unique_endpoint(slug: str, space_id: str):
    return {
        "path": "/IsProjectSlugUnique",
        "json": {
            "slug": slug,
            "spaceId": space_id
        },
        "headers": {
            "Content-Type": "application/json",
            "Current-Space-Id": space_id
        }
    }

def archive_project_endpoint(project_id: str, space_id: str):
    return {
        "path": "/ArchiveProject",
        "json": {
            "projectId": project_id
        },
        "headers": {
            "Content-Type": "application/json",
            "Current-Space-Id": space_id
        }
    }

def unarchive_project_endpoint(project_id: str, space_id: str):
    return {
        "path": "/UnarchiveProject",
        "json": {
            "projectId": project_id
        },
        "headers": {
            "Content-Type": "application/json",
            "Current-Space-Id": space_id
        }
    }
