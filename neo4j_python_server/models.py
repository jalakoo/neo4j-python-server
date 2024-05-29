from pydantic import BaseModel


class Neo4jCredentials(BaseModel):
    uri: str = "bolt://localhost:7687"
    password: str = "<password>"
    username: str = "neo4j"
    database: str = "neo4j"


class Node(BaseModel):
    id: str
    label: str
    properties: dict = None


class Relationship(BaseModel):
    source_id: str
    target_id: str
    type: str
    properties: dict = None
