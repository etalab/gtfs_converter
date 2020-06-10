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


def convert_to_netex(gtfs, file_name, datagouv_id):
    with tempfile.TemporaryDirectory() as netex_dir:
        netex = gtfs2netexfr.convert(gtfs, file_name, netex_dir)
        logging.debug(f"Got a netex file: {netex}")
        metadata = {
            "description": """Conversion automatique du fichier GTFS au format NeTEx (profil France)

La conversion est effectuée par transport.data.gouv.fr en utilisant l’outil https://github.com/CanalTP/transit_model
    """,
            "format": "NeTEx",
        }
        publish_to_datagouv(datagouv_id, netex, metadata)


def convert_to_geojson(gtfs, file_name, datagouv_id):
    with tempfile.TemporaryDirectory() as tmp_dir:
        geojson = gtfs2geojson.convert(gtfs, file_name, tmp_dir)
        logging.debug(f"Got a geojson file: {geojson}")
        metadata = {
            "description": """Création automatique d'un fichier geojson à partir du fichier GTFS.

Le fichier est généré par transport.data.gouv.fr en utilisant l'outil https://gitlab.com/CodeursEnLiberte/gtfs-to-geojson/
    """,
            "format": "geojson",
        }
        publish_to_datagouv(datagouv_id, geojson, metadata)
    pass


def worker():
    logging.info("Setting up a worker")
    while True:
        item = q.get()
        if item is None:
            logging.warn("The queue recieved an empty item")
            break

        with log_context(task_id=item["datagouv_id"]):
            logging.info(
                f"Dequeing {item['url']} for datagouv_id {item['datagouv_id']}"
            )
            try:
                gtfs, fname = utils.download_gtfs(item["url"])

                # convert_to_netex(gtfs, fname, item["datagouv_id"])
                convert_to_geojson(gtfs, fname, item["datagouv_id"])

            except Exception as err:
                logging.error(
                    f"Conversion for url {item['url']} failed: {err}")
            finally:
                q.task_done()


q = queue.Queue()

threads = []
nb_threads = int(os.environ.get("NB_THREADS", 1))
for i in range(nb_threads):
    t = threading.Thread(target=worker, name=f"worker_{i}")
    threads.append(t)
    t.start()

app = Flask(__name__)


@app.route("/convert")
def convert():
    datagouv_id = request.args.get("datagouv_id")
    url = request.args.get("url")
    if datagouv_id and url:
        q.put(
            {
                "url": url,
                "datagouv_id": datagouv_id,
                "task_date": datetime.datetime.today(),
            }
        )
        logging.info(f"Enquing {url} for datagouv_id {datagouv_id}")
        return "The request was put in a queue"
    else:
        return make_response("url and datagouv_id parameters are required", 400)


@app.route("/gtfs2netexfr")
def gtfs2netex():
    # for retrocompatibility, we keep the old /gtfs2netexfr route
    return convert()


@app.route("/stats")
def stats():
    return {"nb_queued_elements": q.qsize()}


@app.route("/queue")
def queue():
    elements = list(q.queue)
    return {"queue": elements}


@app.route("/")
def index():
    return "Hello, have a look at /convert. Nothing else here."


serve(app, listen="*:8080")
