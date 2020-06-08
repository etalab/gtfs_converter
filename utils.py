import subprocess
import urllib
import logging
import re


def run_command(command):
    process = subprocess.Popen(
        command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    while True:
        output = process.stdout.readline().decode()
        if process.poll() is not None:
            break
        if output:
            logging.info(output.strip())
    rc = process.poll()
    return rc


def download_gtfs(url):
    """
    Downloads the requested GTFS and saves it as local file.
    Returns the path to that file
    """
    logging.debug(f"Start downloading {url}")
    local_filename, headers = urllib.request.urlretrieve(url)
    fname = ""
    if "Content-Disposition" in headers.keys():
        fname = re.findall(
            'filename="?([^"]+)"?', headers["Content-Disposition"])[0]
    else:
        fname = url.split("/")[-1]

    logging.debug(f"Downloading done at {local_filename} {fname}")

    return local_filename, fname
