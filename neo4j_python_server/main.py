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
