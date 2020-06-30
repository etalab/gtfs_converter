import logging
import os
import tempfile
from pylogctx import context as log_context  # type: ignore

import utils
import gtfs2netexfr
import gtfs2geojson
from datagouv_publisher import publish_to_datagouv


def convert(params):
    with log_context(task_id=params["datagouv_id"]):
        try:
            logging.info(
                f"Dequeing {params['url']} for datagouv_id {params['datagouv_id']} and {params['conversion_type']} conversions"
            )

            gtfs, fname = utils.download_gtfs(params["url"])

            for conversion in params["conversion_type"]:
                if conversion == "gtfs2netex":
                    _convert_to_netex(gtfs, fname, params["datagouv_id"], params["url"])
                if conversion == "gtfs2geojson":
                    _convert_to_geojson(
                        gtfs, fname, params["datagouv_id"], params["url"]
                    )

            logging.info("job finished")
        except:
            logging.exception("job failed")
            raise


def _convert_to_netex(gtfs, file_name, datagouv_id, url):
    with tempfile.TemporaryDirectory() as netex_dir:
        netex = gtfs2netexfr.convert(gtfs, file_name, netex_dir)
        logging.debug(f"Got a netex file: {netex}")
        metadata = {
            "description": """Conversion automatique du fichier GTFS au format NeTEx (profil France)

La conversion est effectuée par transport.data.gouv.fr en utilisant l’outil https://github.com/CanalTP/transit_model
    """,
            "format": "NeTEx",
            "mime": "application/zip",
        }
        publish_to_datagouv(datagouv_id, netex, metadata, url)


def _convert_to_geojson(gtfs, file_name, datagouv_id, url):
    with tempfile.TemporaryDirectory() as tmp_dir:
        geojson = gtfs2geojson.convert(gtfs, file_name, tmp_dir)
        logging.debug(f"Got a geojson file: {geojson}")
        metadata = {
            "description": """Création automatique d'un fichier geojson à partir du fichier GTFS.

Le fichier est généré par transport.data.gouv.fr en utilisant l'outil https://gitlab.com/CodeursEnLiberte/gtfs-to-geojson/
    """,
            "format": "geojson",
            "mime": "application/json",
        }
        publish_to_datagouv(datagouv_id, geojson, metadata, url)
