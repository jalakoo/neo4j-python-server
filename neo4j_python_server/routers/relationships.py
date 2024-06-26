from fastapi import APIRouter, Request, Response, Body
from neo4j_python_server.database import query_db, can_connect
from neo4j_python_server.export import (
    ExportFormat,
    export_schema,
    export_nodes,
    export_relationships,
)
from neo4j_python_server.logger import logger
from neo4j_python_server.models import Neo4jCredentials
from typing import Optional

router = APIRouter(
    prefix="/relationships",
    tags=["Relationships"],
    # dependencies=[Depends(get_token_header)],
    responses={404: {"description": "Not found"}},
)


@router.post("/types/")
def get_relationship_types(
    creds: Optional[Neo4jCredentials] = Neo4jCredentials(),
) -> list[str]:
    """Return a list of Relationship types from a Neo4j instance.

    Args:
        creds (Neo4jCredential): Credentials object for Neo4j instance to get Relationship types from.

    Returns:
        list[str]: List of Relationship types
    """
    result = []
    query = """
        call db.relationshipTypes();
    """
    response, _, _ = query_db(creds, query)

    logger.debug(f"get relationships types response: {response}")

    result = [r.data()["relationshipType"] for r in response]

    logger.info("Relationships found: " + str(result))
    return result


@router.post("/")
def get_relationships(
    creds: Optional[Neo4jCredentials] = Neo4jCredentials(),
    nodes: Optional[list[str]] = None,
    relationships: Optional[list[str]] = None,
    export_format: Optional[str] = Body(...),
):
    """Return a list of Relationships from a Neo4j instance.

    Args:
        creds (Neo4jCredential): Credentials object for Neo4j instance to get Relationships from.

        nodes (list[str], optional): List of Node labels to filter by. Defaults to [].

        relationships (list[str], optional): List of Relationship types to filter by. Defaults to [].

        export_format (str, optional): Format to export data in. Options are "cytoscape" , "d3", and "default". Defaults to "default".

    Returns:
        list[Relationship]: List of Relationships formatted for Cytoscape
    """

    # Dynamically construct Cypher query dependent on optional Node Labels and Relationship Types.

    logger.info(f"Nodes recieved: {nodes}")
    logger.info(f"Format recieved: {export_format}")

    # String enums can't be passed to the Body decorator, so we'll convert them to strings here.
    if export_format is None:
        export_format = ExportFormat.DEFAULT

    query = f"""
    MATCH (n)-[r]->(n2)
    """
    params = {}

    # Add label filtering
    if nodes is not None and len(nodes) > 0:
        query += "\nWHERE any(label IN labels(n) WHERE label IN $labels) \nAND any(label IN labels(n2) WHERE label IN $labels)"
        params = {"labels": nodes}
        if relationships is not None and len(relationships) > 0:
            query += "\nAND type(r) in $relationships"
            params["relationships"] = relationships

    elif relationships is not None and len(relationships) > 0:
        query += "\nWHERE type(r) in $relationships"
        params["relationships"] = relationships

    query += "\nRETURN n, r, n2"

    # Query target db for data
    records, summary, keys = query_db(creds, query, params)

    result = export_relationships(records, export_format)

    logger.debug(f"result: {result}")

    # Debug return results
    # logger.debug(f"{len(result)} results found")
    # if len(result) > 0:
    #     logger.debug(f"First result: {result[0]}")

    return result


# @router.post("/new/")
# def create_relationship(creds: Neo4jCredentials, relationship_data: dict):
#     # Process the relationship data and create a new relationship

#     sid = relationship_data.source_id
#     tid = relationship_data.target_id
#     query = f"""
#     MATCH (n{{id:$sid}}), (n2:{{id:$tid}})
#     MERGE (n)-[r:{relationship_data.type}]->(n2)
#     RETURN r
#     """
#     params = {"sid": sid, "tid": tid}
#     records, summary, keys = query_db(creds, query, params)
#     logger.info(f"Add relationship summary: {summary}")
#     return {"message": "New relationship created", "summary": summary}
