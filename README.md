# Neo4j Python Server

Experimental FastAPI Server for providing formatted data from/to a [Neo4j](https://neo4j.com/developer/) database.

## Usage

```
poetry install
poetry run uvicorn neo4j_python_server.main:app --reload --host 0.0.0.0
```

Interactive docs should now be located at:

```
http://localhost:8000/docs
```

## Data Schema

### Default

Matches schema used by the [neo4j-uploader]() package

Adding Nodes:

```
{
    "records": [
        {
            "name": "chicken"
        },
        {
            "name":"fish"
        }
    ],
    "labels": [
        "Animals"
    ]
}
```

Adding Relationships:

```
    {
        "type":"LOVES",
        "from_node": {
            "record_key":"_from_uid",
            "node_key":"uid",
            "node_label":"Person"
        },
        "to_node": {
            "record_key":"_to_gid",
            "node_key":"gid",
            "node_label": "Dog"
        },
        "exclude_keys":["_from_uid", "_to_gid"],
        "records":[
            {
                "_from_uid":"abc",
                "_to_gid":"abc"
            }
        ]
    }
```

### Cytoscape

### D3

### NetworkX
