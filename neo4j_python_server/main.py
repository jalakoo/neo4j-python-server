from fastapi import FastAPI, Request, Response, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from pydantic import BaseModel
from typing import Optional
from neo4j_python_server.database import query_db, can_connect
from neo4j_python_server.models import Neo4jCredentials
from neo4j_python_server.export import ExportFormat, export_schema, export_composite
from neo4j_python_server.logger import logger
import json
import os
import logging
from neo4j import exceptions
from .routers import nodes as nodes_router
from .routers import relationships as relationships_router

logger.setLevel(logging.DEBUG)

origins = [
    os.getenv("FRONTEND_URL"),
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

app.include_router(nodes_router.router)
app.include_router(relationships_router.router)


@app.post("/validate")
async def check_database_connection(
    creds: Optional[Neo4jCredentials] = Neo4jCredentials(),
):

    success, msg = can_connect(creds)
    if success:
        return {"message": "Connection successful"}, 200
    else:
        return {"message": "Connection failed", "error": msg}, 400


@app.post("/schema/")
def get_schema(
    creds: Optional[Neo4jCredentials] = Neo4jCredentials(),
    export_format: Optional[ExportFormat] = ExportFormat.DEFAULT,
):
    """Return a data model for a specified Neo4j instance."""

    logger.info(
        f"Getting data model for Neo4j instance at {creds.uri}, {creds.username}, {creds.password}"
    )

    query = """
        call db.schema.visualization
    """
    records, _, _ = query_db(creds, query)

    logger.debug(f"get data model records: {records}")

    converted_records = export_schema(records, export_format)

    return converted_records
