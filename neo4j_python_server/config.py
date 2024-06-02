from neo4j_python_server.models import Neo4jCredentials
import os

default_creds = Neo4jCredentials(
    uri=os.environ.get("NEO4J_URI", "bolt://localhost:7687"),
    password=os.environ.get("NEO4J_PASSWORD", None),
    username=os.environ.get("NEO4J_USERNAME", "neo4j"),
    database=os.environ.get("NEO4J_DATABASE", "neo4j"),
)
