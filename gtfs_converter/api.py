"""
This tool is meant to process GTFS files from transport.data.gouv.fr,
convert them to the NeTEx format,
and upload them as community resources to transport.data.gouv.fr
"""

import logging
import os
import queue
import threading
import datetime
from waitress import serve
from flask import Flask, request, make_response
import tempfile
from redis import Redis
from rq import Queue  # type: ignore

import init_log
from jobs import convert


init_log.config_api_log()

q = Queue(connection=Redis())

app = Flask(__name__)


def _convert(conversion_type):
    datagouv_id = request.args.get("datagouv_id")
    url = request.args.get("url")
    if datagouv_id and url:
        q.enqueue(
            convert,
            {
                "url": url,
                "datagouv_id": datagouv_id,
                "task_date": datetime.datetime.today(),
                "conversion_type": conversion_type,
            },
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


@app.route("/")
def index():
    return "Hello, have a look at /gtfs2netexfr or /gtfs2geojson. Nothing else here."


serve(app, listen="*:8080")
