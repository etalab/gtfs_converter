"""
This tool is meant to process GTFS files from transport.data.gouv.fr,
convert them to the NeTEx format,
and upload them as community resources to transport.data.gouv.fr
"""

import logging
import os
import utils
import queue
import threading
import datetime
from waitress import serve
from flask import Flask, request, make_response
from pylogctx import context as log_context
from logging import config
import tempfile

import gtfs2netexfr
import gtfs2geojson
from datagouv_publisher import publish_to_datagouv

logging.config.dictConfig(
    {
        "version": 1,
        "formatters": {
            "basic": {
                "()": "pythonjsonlogger.jsonlogger.JsonFormatter",
                "format": "%(asctime)s -- %(levelname)s [%(threadName)s] -- %(message)s'",
            }
        },
        "filters": {"context": {"()": "pylogctx.AddContextFilter"}},
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "filters": ["context"],
                "formatter": "basic",
            }
        },
        "root": {"level": "DEBUG", "handlers": ["console"]},
    }
)


def convert_to_netex(gtfs, file_name, datagouv_id, url):
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


def convert_to_geojson(gtfs, file_name, datagouv_id, url):
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
    pass


def worker():
    logging.info("Setting up a worker")
    while True:
        item = q.get()
        if item is None:
            logging.warn("The queue received an empty item")
            break

        with log_context(task_id=item["datagouv_id"]):
            logging.info(
                f"Dequeing {item['url']} for datagouv_id {item['datagouv_id']} and {item['conversion_type']} conversions"
            )

            try:
                gtfs, fname = utils.download_gtfs(item["url"])
            except Exception as err:
                logging.exception(f"dowload url {item['url']} failed")
                q.task_done()
                continue

            for conversion in item["conversion_type"]:
                try:
                    if conversion == "gtfs2netex":
                        convert_to_netex(gtfs, fname, item["datagouv_id"], item["url"])
                    if conversion == "gtfs2geojson":
                        convert_to_geojson(
                            gtfs, fname, item["datagouv_id"], item["url"]
                        )
                except Exception as err:
                    logging.exception(
                        f"Conversion {item['conversion_type']} for url {item['url']} failed"
                    )

            q.task_done()


q = queue.Queue()

threads = []
nb_threads = int(os.environ.get("NB_THREADS", 1))
for i in range(nb_threads):
    t = threading.Thread(target=worker, name=f"worker_{i}")
    threads.append(t)
    t.start()

app = Flask(__name__)


def _convert(conversion_type):
    datagouv_id = request.args.get("datagouv_id")
    url = request.args.get("url")
    if datagouv_id and url:
        q.put(
            {
                "url": url,
                "datagouv_id": datagouv_id,
                "task_date": datetime.datetime.today(),
                "conversion_type": conversion_type,
            }
        )
        logging.info(
            f"Enquing {url} for datagouv_id {datagouv_id}, for {conversion_type} conversion(s)"
        )
        return "The request was put in a queue"
    else:
        return make_response("url and datagouv_id parameters are required", 400)


@app.route("/gtfs2netexfr")
def convert_gtfs_to_netex():
    return _convert(["gtfs2netex"])


@app.route("/gtfs2geojson")
def convert_gtfs_to_geojson():
    return _convert(["gtfs2geojson"])


@app.route("/convert_to_netex_and_geojson")
def convert_gtfs_to_netex_and_geojson():
    return _convert(["gtfs2netex", "gtfs2geojson"])


@app.route("/stats")
def stats():
    return {"nb_queued_elements": q.qsize()}


@app.route("/queue")
def queue():
    elements = list(q.queue)
    return {"queue": elements}


@app.route("/")
def index():
    return "Hello, have a look at /gtfs2netexfr or /gtfs2geojson. Nothing else here."


serve(app, listen="*:8080")
