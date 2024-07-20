from neo4j_python_server.database import query_db, can_connect
from neo4j_python_server.logger import logger
from neo4j_python_server.models import Neo4jCredentials, Node
from neo4j_python_server.ingest import ImportFormat, import_nodes_query
from neo4j_python_server.utils import dict_to_cypher
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from neo4j_python_server.export import (
    ExportFormat,
    export_schema,
    export_nodes,
    export_relationships,
)

router = APIRouter(
    prefix="/nodes",
    tags=["Nodes"],
    # dependencies=[Depends(get_token_header)],
    responses={404: {"description": "Not found"}},
)


@router.post("/labels/", tags=["Nodes"])
def get_node_labels(
    creds: Optional[Neo4jCredentials] = Neo4jCredentials(),
) -> list[str]:
    """Return a list of Node labels from a specified Neo4j instance.

    Args:
        creds (Neo4jCredential): Credentials object for Neo4j instance to get node labels from.

    Returns:
        list[str]: List of Node labels
    """
    result = []
    query = """
        call db.labels();
    """
    try:
        response, _, _ = query_db(creds, query)
    except Exception as e:
        msg = f"Error getting node labels: {e}"
        logger.error(msg)
        return msg, 400

    logger.debug(f"get node labels response: {response}")

    result = [r.data()["label"] for r in response]

    logger.info(f"Node labels found: {result}")
    return result


@router.post("/")
def get_nodes(
    labels: Optional[list[str]] = [],
    export_format: Optional[ExportFormat] = ExportFormat.DEFAULT,
    creds: Optional[Neo4jCredentials] = Neo4jCredentials(),
):

    if labels is not None and len(labels) > 0:
        query = """
    MATCH (n)
    WHERE any(label IN labels(n) WHERE label IN $labels)
    RETURN n
        """
        params = {"labels": labels}
    else:
        query = """
        MATCH (n)
        RETURN n
    """
        params = {}

    records, summary, key = query_db(creds, query, params)

    result = export_nodes(records, export_format)

    logger.debug(f"{len(result)} results found")
    if len(result) > 0:
        logger.debug(f"First result: {result[0]}")

    return result


@router.post("/add")
def create_nodes(
    records: list[dict],
    labels: list[str],
    key: Optional[str],
    import_format: Optional[ImportFormat] = ImportFormat.DEFAULT,
    creds: Optional[Neo4jCredentials] = Neo4jCredentials(),
):

    # TODO: Why is key coming in as None when present in payload
    print(f"key received: {key}")

    query, params = import_nodes_query(records, labels, key, import_format)

    records, summary, keys = query_db(creds, query, params)
    logger.info(f"Add nodes summary: {summary.__dict__}")

    return {"message": "New node created", "summary": summary}
