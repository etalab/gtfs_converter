"""
This tool is meant to process GTFS files from transport.data.gouv.fr,
convert them to the NeTEx format,
and upload them as community resources to transport.data.gouv.fr
"""

import logging
import queue
import threading
from waitress import serve
from flask import Flask, request, make_response

from gtfs2netexfr import download_and_convert
from datagouv_publisher import publish_to_datagouv


logging.basicConfig(level=logging.DEBUG, format='%(asctime)s -- %(levelname)s -- %(message)s')


q = queue.SimpleQueue()

def worker():
    logging.info('Setting up a worker')
    while True:
        item = q.get()
        logging.info(f"Dequeing {item['url']} for datagouv_id {item['datagouv_id']}")
        if item is None:
            logging.warn('The queue recieved and empty item')
            break
        try:
            netex = download_and_convert(item['url'], 'transport.data.gouv.fr')
            logging.debug(f"Got a netex repooo {netex}")
            publish_to_datagouv(item['datagouv_id'], netex)

        except Exception as err:
            logging.error(f"Conversion for url {item['url']} failed: {err}")
        finally:
            q.task_done()


q = queue.Queue()
t = threading.Thread(target=worker)
t.start()

app = Flask(__name__)
@app.route('/gtfs2netexfr')
def gtfs2netex():
    datagouv_id = request.args.get('datagouv_id')
    url = request.args.get('url')
    if datagouv_id and url:
        q.put({'url': url, 'datagouv_id': datagouv_id})
        logging.info(f"Enquing {url} for datagouv_id {datagouv_id}")
        return 'The request was put in a queue'
    else:
        return make_response('url and datagouv_id parameters are required', 400)


@app.route('/')
def index():
    return 'Hello, have a look at /gtfs2netex. Nothing else here.'

serve(app, listen='*:8080')
