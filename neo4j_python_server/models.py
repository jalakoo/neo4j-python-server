from pydantic import BaseModel, field_validator
from typing import Optional
import os


class Neo4jCredentials(BaseModel):
    uri: str = os.environ.get("NEO4J_URI", "bolt://localhost:7687")
    password: str = os.environ.get("NEO4J_PASSWORD", None)
    username: str = os.environ.get("NEO4J_USERNAME", "neo4j")
    database: str = os.environ.get("NEO4J_DATABASE", "neo4j")


class Node(BaseModel):
    labels: Optional[list[str]] = []
    element_id: Optional[str] = None
    properties: dict = None


class Relationship(BaseModel):
    source_node: Node
    target_node: Node
    type: str
    element_id: Optional[str] = None
    properties: dict = None
