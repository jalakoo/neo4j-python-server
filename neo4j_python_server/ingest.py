from enum import Enum
from typing import Optional


class ImportFormat(str, Enum):
    DEFAULT = "default"


def import_nodes_query(
    records: list[dict],
    labels: list[str],
    key: Optional[str] = None,
    format: Optional[ImportFormat] = ImportFormat.DEFAULT,
) -> tuple[str, dict]:

    if format != ImportFormat.DEFAULT:
        raise TypeError("Invalid import format")
    else:
        return import_nodes_query_default(records, labels, key)


def import_nodes_query_default(
    records: list[dict],
    labels: list[str],
    key: Optional[str] = None,
) -> tuple[str, dict]:
    """Creates a Cypher query and optional parameters for writing Nodes.

    Args:
        records (list[dict]): List of Node dictionaries to import.
        labels (list[str]): List of labels to apply to all Nodes.

    Returns:
        tuple[str, dict]: Cypher query and parameters to import Nodes.
    """

    # Create a string representation of properties to be used in the merge/create clause
    def properties_to_string(properties):
        return (
            "{" + ", ".join([f"{key}: node.{key}" for key in properties.keys()]) + "}"
        )

    # Join labels with colons
    label_string = ":".join(labels)

    query = "UNWIND $records AS node\n"

    if key is None:
        # Always create new
        # # Get the keys from the first record to determine the properties
        if records:
            properties_string = properties_to_string(records[0])
        else:
            properties_string = "{}"
        query += f"""
        CREATE (:{label_string} {properties_string})
        """
    else:
        # Create new only if matching Node does not exist.
        # Use the (unique property) key to determine which Node to update.
        # Merge command will create a new record if no matching Node is found.
        # Indetermine behavior if the key-values are not actually unique.
        query += f"""
        MERGE (n:{label_string} {{{key}: node.{key}}})
        SET n += node
        """
        print(f"merge query: {query}")

    return query, {"records": records}
