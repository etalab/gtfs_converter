"""
This tool is meant to process GTFS files from transport.data.gouv.fr,
convert them to the NeTEx format,
and upload them as community resources to transport.data.gouv.fr
"""

import logging
import os
import datetime
import tempfile
from waitress import serve
from flask import Flask, request, make_response
from redis import Redis
from rq import Queue  # type: ignore
from werkzeug.utils import secure_filename
from gtfs2geojson import convert_sync

import init_log


init_log.config_api_log()

q = Queue(connection=Redis.from_url(os.environ.get("REDIS_URL") or "redis://"))

app = Flask(__name__)


def _convert(conversion_type):
    datagouv_id = request.args.get("datagouv_id")
    url = request.args.get("url")
    if datagouv_id and url:
        q.enqueue(
            "jobs.convert",
            {
                "url": url,
                "datagouv_id": datagouv_id,
                "task_date": datetime.datetime.today(),
                "conversion_type": conversion_type,
            },
            job_timeout="20m",
            result_ttl=86400,
        )
        logging.info(
            f"Enquing {url} for datagouv_id {datagouv_id}, for {conversion_type} conversion(s)"
        )
        return "The request was put in a queue"
    else:
        return make_response("url and datagouv_id parameters are required", 400)


def _allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ['zip']


def _convert_to_geojson_sync():
    try:
        if 'file' not in request.files:
            return "no file"
        file = request.files['file']
        if file.filename == '':
            return "no filename"
        if file and _allowed_file(file.filename):
            filename = secure_filename(file.filename)
            with tempfile.TemporaryDirectory() as tmpdirname:
                file_path = os.path.join(tmpdirname, filename)
                file.save(file_path)
                return convert_sync(file_path)
    except:
        return "error in geojson conversion", 500


@app.route("/gtfs2netexfr")
def convert_gtfs_to_netex():
    return _convert(["gtfs2netex"])


@app.route("/gtfs2geojson")
def convert_gtfs_to_geojson():
    return _convert(["gtfs2geojson"])


@app.route("/gtfs2geojson_sync", methods=['POST'])
def convert_gtfs_to_geojson_sync():
    return _convert_to_geojson_sync()


@app.route("/convert_to_netex_and_geojson")
def convert_gtfs_to_netex_and_geojson():
    return _convert(["gtfs2geojson", "gtfs2netex"])


@app.route("/")
def index():
    return "Hello, have a look at /gtfs2netexfr or /gtfs2geojson. Nothing else here."


serve(app, listen="*:8080")
