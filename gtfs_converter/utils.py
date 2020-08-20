import subprocess
import urllib
import logging
import re
import tempfile


def run_command(command):
    process = subprocess.Popen(
        command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    while True:
        output = process.stdout.readline().decode()
        output_err = process.stderr.readline().decode()
        if output:
            logging.info(output.strip())
        if output_err:
            logging.error(output_err.strip())
        if process.poll() is not None:
            break
    rc = process.poll()
    return rc


def run_command_get_stdout(command):
    return subprocess.check_output(command)


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
