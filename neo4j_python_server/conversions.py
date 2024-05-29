from pydantic import BaseModel
from enum import Enum
from neo4j_python_server.logger import logger


class ConversionFormat(str, Enum):
    CYTOSCAPE_JS = "cytoscape_js"
    DEFAULT = "default"


class ConversionConfig(BaseModel):
    response_format: ConversionFormat = ConversionFormat.DEFAULT


def convert_schema_default(records: list[any]) -> dict:
    # A list of lists will be returned. Only one element will be returned
    datamodel = records[0]

    # First indexed list are all Nodes information
    nodes = datamodel[0]

    # Second indexed list are all Relationships information
    relationships = datamodel[1]

    converted_nodes = [
        {
            "element_id": n.element_id,
            "labels": list(n.labels),
            "data": n._properties,
        }
        for n in nodes
    ]

    converted_rels = [
        {
            "source": {
                "element_id": r.start_node.element_id,
                "labels": list(r.start_node.labels),
                "data": r.start_node._properties,
            },
            "target": {
                "element_id": r.end_node.element_id,
                "labels": list(r.end_node.labels),
                "data": r.end_node._properties,
            },
            "element_id": r.element_id,
            "type": r.type,
            "data": r._properties,
        }
        for r in relationships
    ]

    converted_elements = converted_nodes + converted_rels
    logger.info(f"Returning schema result: {converted_elements}")
    return converted_elements


def convert_schema_cytoscape_js(records: list[any]) -> dict:

    # A list of lists will be returned. Only one element will be returned
    datamodel = records[0]

    # First indexed list are all Nodes information
    nodes = datamodel[0]

    # Second indexed list are all Relationships information
    relationships = datamodel[1]

    converted_nodes = [
        {
            "data": {
                "id": n.element_id,
                "label": list(n.labels)[0],
                "neo4j_data": n._properties,
            }
        }
        for n in nodes
    ]

    converted_rels = [
        {
            "data": {
                "source": r.start_node.element_id,
                "target": r.end_node.element_id,
                "id": f"{r.element_id}r",
                "label": r.type,
                "neo4j_data": r._properties,
            }
        }
        for r in relationships
    ]

    converted_elements = converted_nodes + converted_rels
    logger.info(f"Returning schema result: {converted_elements}")
    return converted_elements


def convert_schema(records: list[any], config: ConversionConfig) -> dict | list[dict]:
    if config.response_format == ConversionFormat.CYTOSCAPE_JS:
        return convert_schema_cytoscape_js(records)
    else:
        return convert_schema_default(records)
