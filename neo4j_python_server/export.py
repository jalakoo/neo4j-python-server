from pydantic import BaseModel
from enum import Enum
from neo4j_python_server.logger import logger


class ExportFormat(str, Enum):
    CYTOSCAPE_JS = "cytoscape"
    DEFAULT = "default"


class ExportConfig(BaseModel):
    response_format: ExportFormat = ExportFormat.DEFAULT


def export_schema_default(records: list[any]) -> dict:
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
            "properties": n._properties,
        }
        for n in nodes
    ]

    try:
        converted_rels = [
            {
                "source": {
                    "element_id": r.start_node.element_id,
                    "labels": list(r.start_node.labels),
                    "properties": r.start_node._properties,
                },
                "target": {
                    "element_id": r.end_node.element_id,
                    "labels": list(r.end_node.labels),
                    "properties": r.end_node._properties,
                },
                "element_id": r.element_id,
                "type": r.type,
                "properties": r._properties,
            }
            for r in relationships
        ]
    except Exception as e:
        logger.error(
            f"Could not convert relationships schema to default format. First record for references: {records[0]}"
        )

    converted_elements = converted_nodes + converted_rels
    logger.info(f"Returning schema result: {converted_elements}")
    return converted_elements


def export_schema_cytoscape(records: list[any]) -> dict:

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
                "properties": n._properties,
            }
        }
        for n in nodes
    ]

    try:
        converted_rels = [
            {
                "data": {
                    "source": r.start_node.element_id,
                    "target": r.end_node.element_id,
                    "id": f"{r.element_id}r",
                    "label": r.type,
                    "properties": r._properties,
                }
            }
            for r in relationships
        ]
    except Exception as e:
        logger.error(
            f"Could not convert relationships schema to Cytoscape format. First record for references: {records[0]}"
        )
    converted_elements = converted_nodes + converted_rels
    logger.info(f"Returning schema result: {converted_elements}")
    return converted_elements


def export_schema(records: list[any], config: ExportConfig) -> dict | list[dict]:
    if config.response_format == ExportFormat.CYTOSCAPE_JS:
        return export_schema_cytoscape(records)
    else:
        return export_schema_default(records)


def export_nodes_default(records: list[any]) -> list[dict]:
    return [
        {
            "element_id": n.values()[0]._element_id,
            "labels": list(n.values()[0]._labels),
            "properties": n.values()[0]._properties,
        }
        for n in records
    ]


def export_nodes_cytoscape(records: list[any]) -> list[dict]:
    return [
        {
            "data": {
                "id": n.values()[0]._element_id,
                "label": list(n.values()[0]._labels)[0],
                "properties": n.values()[0]._properties,
            }
        }
        for n in records
    ]


def export_nodes(records: list[any], config: ExportConfig) -> dict | list[dict]:
    if config.response_format == ExportFormat.CYTOSCAPE_JS:
        return export_nodes_cytoscape(records)
    else:
        return export_nodes_default(records)


def export_relationships_default(records: list[any]) -> list[dict]:
    try:
        results = []
        for rec in records:
            r = rec.values()[1]
            source_eid = r._start_node._element_id
            source_labels = list(r._start_node._labels)
            source_props = r._start_node._properties
            # logger.debug(f"Source node: {source_eid} {source_labels} {source_props}")

            target_eid = r._end_node._element_id
            target_labels = list(r._end_node._labels)
            target_props = r._end_node._properties
            # logger.debug(f"Target node: {target_eid} {target_labels} {target_props}")

            rel_eid = r._element_id
            rel_type = rec.data()["r"][1]
            rel_props = r._properties
            # logger.debug(f"Relationship: {rel_eid} {rel_type} {rel_props}")

            results.append(
                {
                    "source": {
                        "element_id": source_eid,
                        "labels": source_labels,
                        "properties": source_props,
                    },
                    "target": {
                        "element_id": target_eid,
                        "labels": target_labels,
                        "properties": target_props,
                    },
                    "element_id": rel_eid,
                    "type": rel_type,
                    "properties": rel_props,
                }
            )
        return results
    except Exception as e:
        logger.error(
            f"Could not convert relationships to default schema. First record for references: {records[0]}"
        )
        logger.debug(f"__dict__: {records[0].__dict__}")
        logger.debug(f"values: {records[0].values()[1].__dict__}")
        logger.debug(f"data(): {records[0].data()['r']}")


def export_cytoscape_relationships(records: list[any]) -> list[dict]:
    try:
        return [
            {
                "data": {
                    "source": r.values()[0]._element_id,
                    "target": r.values()[2]._element_id,
                    "id": r.values()[1]._element_id,
                    "label": r.data()["r"][1],
                    "properties": r.data(),
                }
            }
            for r in records
        ]
    except Exception as e:
        logger.error(
            f"Could not convert relationships to Cytoscape format. First record for references: {records[0]}"
        )


def export_relationships(records: list[any], config: ExportConfig) -> dict | list[dict]:
    if config.response_format == ExportFormat.CYTOSCAPE_JS:
        return export_cytoscape_relationships(records)
    else:
        return export_relationships_default(records)
