from neo4j_python_server.config import default_creds
from neo4j_python_server.database import query_db, can_connect
from neo4j_python_server.logger import logger
from neo4j_python_server.models import Neo4jCredentials
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from neo4j_python_server.export import (
    ExportConfig,
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
def get_node_labels(creds: Optional[Neo4jCredentials] = default_creds) -> list[str]:
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


@router.post("/nodes/", tags=["Nodes"])
def get_nodes(
    creds: Optional[Neo4jCredentials] = default_creds,
    labels: Optional[list[str]] = [],
    config: Optional[ExportConfig] = ExportConfig(),
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

    result = export_nodes(records, config)

    logger.debug(f"{len(result)} results found")
    if len(result) > 0:
        logger.debug(f"First result: {result[0]}")

    return result


# @router.post("/nodes/new",  tags=["Nodes"])
# def create_node(creds: Neo4jCredentials, node_data: dict):
#     # Process the node data and create a new node
#     label = node_data["label"]
#     id = node_data["id"]
#     query = f"""
#     MERGE (n:`{label})
#     SET n.id = $id
#     RETURN n.id as id, label(n) as label
#     """
#     params = {
#         "id": id,
#     }
#     records, summary, keys = query_db(creds, query, params)

#     logger.info(f"Add nodes summary: {summary}")

#     return {"message": "New node created", "summary": summary}
