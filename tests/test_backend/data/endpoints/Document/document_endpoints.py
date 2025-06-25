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
