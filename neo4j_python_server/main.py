from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
from neo4j_python_server.database import query_db, can_connect
from neo4j_python_server.models import Neo4jCredentials
from neo4j_python_server.conversions import (
    ConversionConfig,
    ConversionFormat,
    convert_schema,
)
from neo4j_python_server.logger import logger
import json
import os
import logging
from neo4j.graph import Node, Relationship

logger.setLevel(logging.DEBUG)

app = FastAPI()

origins = [
    "http://127.0.0.1:8000",  # Alternative localhost address
    "http://localhost",
    "http://localhost:8000",
    "http://localhost:8080",  # Add other origins as needed
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

default_creds = Neo4jCredentials(
    uri=os.environ.get("NEO4J_URI", "bolt://localhost:7687"),
    password=os.environ.get("NEO4J_PASSWORD", None),
    username=os.environ.get("NEO4J_USERNAME", "neo4j"),
    database=os.environ.get("NEO4J_DATABASE", "neo4j"),
)


@app.post("/validate")
async def check_database_connection(creds: Optional[Neo4jCredentials] = None):

    if creds is None:
        creds = default_creds

    success, msg = can_connect(creds)
    if success:
        return {"message": "Connection successful"}, 200
    else:
        return {"message": "Connection failed", "error": msg}, 400


@app.post("/schema/")
def get_schema(
    creds: Optional[Neo4jCredentials] = default_creds,
    config: Optional[ConversionConfig] = ConversionConfig(),
):
    """Return a data model for a specified Neo4j instance."""

    query = """
        call db.schema.visualization
    """
    records, _, _ = query_db(creds, query)

    logger.debug(f"get data model records: {records}")

    converted_records = convert_schema(records, config)

    return converted_records


@app.post("/nodes/labels/")
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
    response, _, _ = query_db(creds, query)

    logger.debug(f"get node labels response: {response}")

    result = [r.data()["label"] for r in response]

    logger.info(f"Node labels found: {result}")
    return result


@app.post("/nodes/")
# NOTE: For some reason Pydantic is not parsing payload data correctly, so using older data parsing method with limited validation.
# async def get_nodes(
#     creds: Neo4jCredentials,
#     labels: Optional[list[str]] = None,
# ):
async def get_nodes(request: Request):

    try:
        # Attempt to parse the incoming JSON data
        parsed_data = await request.json()
    except json.JSONDecodeError as e:
        # Log the raw data when a JSON decode error occurs
        print(f"JSON decode error: {e}")
        return {"message": "JSON decode error", "error": str(e)}, 400

    labels = parsed_data["labels"] if "labels" in parsed_data else []
    creds = Neo4jCredentials(**parsed_data["creds"])

    # @app.post("/nodes/")
    # def get_nodes(creds: Neo4jCredentials, labels: list[str] = []):

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

    result = [
        {
            "data": {
                "id": r.values()[0]._element_id,
                "label": list(r.values()[0]._labels)[0],
                "neo4j_data": r.data()["n"],
            }
        }
        for r in records
    ]

    logger.debug(f"{len(result)} results found")
    if len(result) > 0:
        logger.debug(f"First result: {result[0]}")

    return result


# @app.post("/nodes/new")
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


@app.post("/relationships/types/")
def get_relationship_types(creds: Neo4jCredentials) -> list[str]:
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


@app.post("/relationships/")
# NOTE: For some reason this doesn't parse correctly
# async def get_relationships(
#     creds: Neo4jCredentials,
#     labels: Optional[list[str]] = None,
#     types: Optional[list[str]] = None,
# ):
async def get_relationships(request: Request):
    """Return a list of Relationships from a Neo4j instance.

    Args:
        creds (Neo4jCredential): Credentials object for Neo4j instance to get Relationships from.
        labels (list[str], optional): List of Node labels to filter by. Defaults to [].
        types (list[str], optional): List of Relationship types to filter by. Defaults to [].

    Returns:
        list[Relationship]: List of Relationships formatted for Cytoscape
    """

    # Using old school data parsing
    try:
        # Attempt to parse the incoming JSON data
        parsed_data = await request.json()
    except json.JSONDecodeError as e:
        # Log the raw data when a JSON decode error occurs
        print(f"JSON decode error: {e}")
        return {"message": "JSON decode error", "error": str(e)}, 400

    types = parsed_data["types"] if "types" in parsed_data else []
    labels = parsed_data["labels"] if "labels" in parsed_data else []
    creds = Neo4jCredentials(**parsed_data["creds"])

    # Dynamically construct Cypher query dependent on optional Node Labels and Relationship Types.

    # TODO: Do this is in a less confusing manner

    query = f"""
    MATCH (n)-[r]->(n2)
    """
    params = {}

    # Add label filtering
    if labels is not None and len(labels) > 0:
        query += "\nWHERE any(label IN labels(n) WHERE label IN $labels) \nAND any(label IN labels(n2) WHERE label IN $labels)"
        params = {"labels": labels}
        if types is not None and len(types) > 0:
            query += "\nAND type(r) in $types"
            params["types"] = types

    elif types is not None and len(types) > 0:
        query += "\nWHERE type(r) in $types"
        params["types"] = types

    query += "\nRETURN n, r, n2"

    # Query target db for data
    records, summary, keys = query_db(creds, query, params)

    # Reformat for Cytoscape
    result = []
    for r in records:
        source_id = r.values()[0]._element_id
        rid = r.values()[1]._element_id
        target_id = r.values()[2]._element_id
        r_label = r.data()["r"][1]

        result.append(
            {
                "data": {
                    "source": source_id,
                    "target": target_id,
                    "id": rid,
                    "label": r_label,
                    "neo4j_data": r.data(),
                }
            }
        )

    # Debug return results
    logger.debug(f"{len(result)} results found")
    if len(result) > 0:
        logger.debug(f"First result: {result[0]}")

    return result


# @app.post("/relationships/new/")
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
