from typing import Optional, Dict, Any


def create_document_endpoint(
    kind: str,
    kind_id: str,
    space_id: str,
    parent_document_id: str = None,
    index: int = None,
    title: str = None,
):
    payload = {
        'kind': kind,
        'kindId': kind_id,
    }

    if parent_document_id is not None:
        payload['parentDocumentId'] = parent_document_id

    if index is not None:
        payload['index'] = index

    if title is not None:
        payload['title'] = title

    return {
        'path': '/CreateDocument',
        'json': payload,
        'headers': {
            'Content-Type': 'application/json',
            'Current-Space-Id': space_id,
        },
    }


def get_documents_endpoint(kind: str, kind_id: str, space_id: str):
    return {
        'path': '/GetDocuments',
        'json': {'kind': kind, 'kindId': kind_id},
        'headers': {'Content-Type': 'application/json', 'Current-Space-Id': space_id},
    }


def get_document_endpoint(document_id: str, space_id: str):
    return {
        'path': '/GetDocument',
        'json': {'documentId': document_id},
        'headers': {'Content-Type': 'application/json', 'Current-Space-Id': space_id},
    }


def get_document_siblings_endpoint(document_id: str, space_id: str):
    return {
        'path': '/GetDocumentSiblings',
        'json': {'documentId': document_id},
        'headers': {'Content-Type': 'application/json', 'Current-Space-Id': space_id},
    }


def get_ydocument_endpoint(document_id: str, space_id: str, till_commit_id: Optional[str] = None) -> Dict[str, Any]:
    payload: Dict[str, Any] = {'documentId': document_id}
    if till_commit_id is not None:
        payload['tillCommitId'] = till_commit_id

    return {
        'path': '/GetYDocument',
        'json': payload,
        'headers': {
            'Content-Type': 'application/json',
            'Current-Space-Id': space_id,
        },
    }


def edit_document_endpoint(document_id: str, title: str, icon: str, space_id: str) -> Dict[str, Any]:
    return {
        'path': '/EditDocument',
        'json': {
            'documentId': document_id,
            'title': title,
            'icon': icon,
        },
        'headers': {
            'Content-Type': 'application/json',
            'Current-Space-Id': space_id,
        },
    }


def duplicate_document_endpoint(document_id: str, space_id: str):
    return {
        'path': '/DuplicateDocument',
        'json': {'documentId': document_id},
        'headers': {
            'Content-Type': 'application/json',
            'Current-Space-Id': space_id,
        },
    }


def archive_document_endpoint(document_id: str, space_id: str):
    return {
        'path': '/ArchiveDocument',
        'json': {'documentId': document_id},
        'headers': {
            'Content-Type': 'application/json',
            'Current-Space-Id': space_id,
        },
    }
