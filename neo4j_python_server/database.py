from neo4j import GraphDatabase, basic_auth, exceptions
from pydantic import BaseModel
from neo4j_python_server.logger import logger
from neo4j_python_server.models import Neo4jCredentials


# Using simpler query
# def can_connect(creds: Neo4jCredentials) -> (bool, str):
#     try:
#         # Create a driver instance
#         driver = GraphDatabase.driver(creds.uri, auth=(creds.username, creds.password))

#         # Verify connection by trying to obtain a session
#         with driver.session(database=creds.database) as session:
#             session.run("RETURN 1")

#         print("Connection successful!")
#         return True, None

#     except exceptions.AuthError as e:
#         print(f"Authentication failed: {e}")
#         return False, f"{e}"

#     except exceptions.ServiceUnavailable as e:
#         print(f"Service unavailable: {e}")
#         return False, f"{e}"

#     except Exception as e:
#         print(f"An error occurred: {e}")
#         return False, f"{e}"


# Using verify_connetivity() which try-except doesn't properly catch
def can_connect(creds: Neo4jCredentials) -> (bool, str):
    try:
        with GraphDatabase.driver(
            creds.uri, auth=(creds.username, creds.password)
        ) as driver:
            driver.verify_connectivity()
            return True, None
    except exceptions.AuthError as e:
        print(e)
        return False, f"{e}"
    except exceptions.ServiceUnavailable as e:
        print(e)
        return False, f"{e}"
    except Exception as e:
        print(e)
        return False, f"{e}"


def query_db(creds: Neo4jCredentials, query: str, params: dict = {}):
    try:
        with GraphDatabase.driver(
            creds.uri, auth=basic_auth(creds.username, creds.password)
        ) as driver:
            return driver.execute_query(query, params, database=creds.database)
    except Exception as e:
        logger.error(
            f"Problem running query: {query} with params: {params}. ERROR: {e}"
        )
        raise e
