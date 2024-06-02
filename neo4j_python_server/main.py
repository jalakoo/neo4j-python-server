from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware

from pydantic import BaseModel
from typing import Optional
from neo4j_python_server.config import default_creds
from neo4j_python_server.database import query_db, can_connect
from neo4j_python_server.models import Neo4jCredentials
from neo4j_python_server.export import (
    ExportConfig,
    ExportFormat,
    export_schema,
    export_nodes,
    export_relationships,
)
from neo4j_python_server.logger import logger
import json
import os
import logging
from neo4j import exceptions
from .routers import nodes, relationships

logger.setLevel(logging.DEBUG)

origins = [
    "http://127.0.0.1:8000",  # Alternative localhost address
    "http://localhost",
    "http://localhost:8000",
    "http://localhost:8080",  # Add other origins as needed
]


class Neo4jExceptionMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        try:
            response = await call_next(request)
            return response
        except exceptions.AuthError as e:
            msg = f"Neo4j Authentication Error: {e}"
            logger.error(msg)
            return Response(content=msg, status_code=400)
        except exceptions.ServiceUnavailable as e:
            msg = f"Neo4j Database Unavailable Error: {e}"
            logger.error(msg)
            return Response(content=msg, status_code=400)
        except Exception as e:
            logger.error(e)
            return Response(content=str(e), status_code=400)


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(Neo4jExceptionMiddleware)

app.include_router(nodes.router)
app.include_router(relationships.router)

# default_creds = Neo4jCredentials(
#     uri=os.environ.get("NEO4J_URI", "bolt://localhost:7687"),
#     password=os.environ.get("NEO4J_PASSWORD", None),
#     username=os.environ.get("NEO4J_USERNAME", "neo4j"),
#     database=os.environ.get("NEO4J_DATABASE", "neo4j"),
# )


@app.post("/validate")
async def check_database_connection(creds: Optional[Neo4jCredentials] = default_creds):

    success, msg = can_connect(creds)
    if success:
        return {"message": "Connection successful"}, 200
    else:
        return {"message": "Connection failed", "error": msg}, 400


@app.post("/schema/")
def get_schema(
    creds: Optional[Neo4jCredentials] = default_creds,
    config: Optional[ExportConfig] = ExportConfig(),
):
    """Return a data model for a specified Neo4j instance."""

    query = """
        call db.schema.visualization
    """
    records, _, _ = query_db(creds, query)

    logger.debug(f"get data model records: {records}")

    converted_records = export_schema(records, config)

    return converted_records


# @app.post("/nodes/labels/")
# def get_node_labels(creds: Optional[Neo4jCredentials] = default_creds) -> list[str]:
#     """Return a list of Node labels from a specified Neo4j instance.

#     Args:
#         creds (Neo4jCredential): Credentials object for Neo4j instance to get node labels from.

#     Returns:
#         list[str]: List of Node labels
#     """
#     result = []
#     query = """
#         call db.labels();
#     """
#     try:
#         response, _, _ = query_db(creds, query)
#     except Exception as e:
#         msg = f"Error getting node labels: {e}"
#         logger.error(msg)
#         return msg, 400

#     logger.debug(f"get node labels response: {response}")

#     result = [r.data()["label"] for r in response]

#     logger.info(f"Node labels found: {result}")
#     return result


# @app.post("/nodes/")
# def get_nodes(
#     creds: Optional[Neo4jCredentials] = default_creds,
#     labels: Optional[list[str]] = [],
#     config: Optional[ExportConfig] = ExportConfig(),
# ):

#     if labels is not None and len(labels) > 0:
#         query = """
#     MATCH (n)
#     WHERE any(label IN labels(n) WHERE label IN $labels)
#     RETURN n
#         """
#         params = {"labels": labels}
#     else:
#         query = """
#         MATCH (n)
#         RETURN n
#     """
#         params = {}

#     records, summary, key = query_db(creds, query, params)

#     result = export_nodes(records, config)

#     logger.debug(f"{len(result)} results found")
#     if len(result) > 0:
#         logger.debug(f"First result: {result[0]}")

#     return result


# # @app.post("/nodes/new")
# # def create_node(creds: Neo4jCredentials, node_data: dict):
# #     # Process the node data and create a new node
# #     label = node_data["label"]
# #     id = node_data["id"]
# #     query = f"""
# #     MERGE (n:`{label})
# #     SET n.id = $id
# #     RETURN n.id as id, label(n) as label
# #     """
# #     params = {
# #         "id": id,
# #     }
# #     records, summary, keys = query_db(creds, query, params)

# #     logger.info(f"Add nodes summary: {summary}")

# #     return {"message": "New node created", "summary": summary}


# @app.post("/relationships/types/")
# def get_relationship_types(creds: Neo4jCredentials) -> list[str]:
#     """Return a list of Relationship types from a Neo4j instance.

#     Args:
#         creds (Neo4jCredential): Credentials object for Neo4j instance to get Relationship types from.

#     Returns:
#         list[str]: List of Relationship types
#     """
#     result = []
#     query = """
#         call db.relationshipTypes();
#     """
#     response, _, _ = query_db(creds, query)

#     logger.debug(f"get relationships types response: {response}")

#     result = [r.data()["relationshipType"] for r in response]

#     logger.info("Relationships found: " + str(result))
#     return result


# @app.post("/relationships/")
# def get_relationships(
#     creds: Neo4jCredentials,
#     labels: Optional[list[str]] = None,
#     types: Optional[list[str]] = None,
#     config: ExportConfig = ExportConfig(),
# ):
#     """Return a list of Relationships from a Neo4j instance.

#     Args:
#         creds (Neo4jCredential): Credentials object for Neo4j instance to get Relationships from.
#         labels (list[str], optional): List of Node labels to filter by. Defaults to [].
#         types (list[str], optional): List of Relationship types to filter by. Defaults to [].

#     Returns:
#         list[Relationship]: List of Relationships formatted for Cytoscape
#     """

#     # Dynamically construct Cypher query dependent on optional Node Labels and Relationship Types.

#     # TODO: Do this is in a less confusing manner

#     query = f"""
#     MATCH (n)-[r]->(n2)
#     """
#     params = {}

#     # Add label filtering
#     if labels is not None and len(labels) > 0:
#         query += "\nWHERE any(label IN labels(n) WHERE label IN $labels) \nAND any(label IN labels(n2) WHERE label IN $labels)"
#         params = {"labels": labels}
#         if types is not None and len(types) > 0:
#             query += "\nAND type(r) in $types"
#             params["types"] = types

#     elif types is not None and len(types) > 0:
#         query += "\nWHERE type(r) in $types"
#         params["types"] = types

#     query += "\nRETURN n, r, n2"

#     # Query target db for data
#     records, summary, keys = query_db(creds, query, params)

#     result = export_relationships(records, config)

#     # Debug return results
#     logger.debug(f"{len(result)} results found")
#     if len(result) > 0:
#         logger.debug(f"First result: {result[0]}")

#     return result


# # @app.post("/relationships/new/")
# # def create_relationship(creds: Neo4jCredentials, relationship_data: dict):
# #     # Process the relationship data and create a new relationship

# #     sid = relationship_data.source_id
# #     tid = relationship_data.target_id
# #     query = f"""
# #     MATCH (n{{id:$sid}}), (n2:{{id:$tid}})
# #     MERGE (n)-[r:{relationship_data.type}]->(n2)
# #     RETURN r
# #     """
# #     params = {"sid": sid, "tid": tid}
# #     records, summary, keys = query_db(creds, query, params)
# #     logger.info(f"Add relationship summary: {summary}")
# #     return {"message": "New relationship created", "summary": summary}
