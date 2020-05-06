import subprocess
import urllib.request
import os
import logging
import re
import shutil

CONVERTER = os.environ["CONVERTER"]


def download_gtfs(url):
    """
    Downloads the requested GTFS and saves it as local file.
    Returns the path to that file
    """
    logging.debug(f"Start downloading {url}")
    local_filename, headers = urllib.request.urlretrieve(url)
    fname = ""
    if "Content-Disposition" in headers.keys():
        fname = re.findall('filename="?([^"]+)"?', headers["Content-Disposition"])[0]
    else:
        fname = url.split("/")[-1]

    logging.debug(f"Downloading done at {local_filename} {fname}")

    return local_filename, fname


def _run_command(command):
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    while True:
        output = process.stdout.readline().decode()
        if process.poll() is not None:
            break
        if output:
            logging.info(output.strip())
    rc = process.poll()
    return rc


def convert(gtfs_src, publisher, fname, netex_dir):
    """
    Converts a given gtfs file and returns the path to the generated netex zip file.
    The publisher is the name of the organization that published that dataset.
    """
    logging.info(f"Start converting {gtfs_src} to {netex_dir}")

    ret = _run_command(
        [
            CONVERTER,
            "--input",
            gtfs_src,
            "--output",
            netex_dir,
            "--participant",
            publisher,
        ]
    )
    logging.debug(f"Conversion done with return code {ret}")
    if ret == 0:
        netex_zip = f"{fname}.netex"
        shutil.make_archive(netex_zip, "zip", netex_dir)
        return f"{netex_zip}.zip"

    raise Exception("Unable to convert file")


def download_and_convert(url, publisher, netex_dir):
    gtfs, fname = download_gtfs(url)
    return convert(gtfs, publisher, fname, netex_dir)
