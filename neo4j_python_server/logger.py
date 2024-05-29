import logging

mname = "neo4j_python_server"
logger = logging.getLogger(mname)
sh = logging.StreamHandler()
formatter = logging.Formatter(
    f"{mname}:%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
sh.setFormatter(formatter)
logger.addHandler(sh)
