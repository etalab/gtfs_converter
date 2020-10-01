import subprocess
import urllib
import logging
import re
import tempfile

import select
import fcntl
import os
import errno

# from: http://stackoverflow.com/questions/7729336/how-can-i-print-and-display-subprocess-stdout-and-stderr-output-without-distorti/7730201#7730201
def make_async(fd):
    fcntl.fcntl(fd, fcntl.F_SETFL, fcntl.fcntl(fd, fcntl.F_GETFL) | os.O_NONBLOCK)


# Helper function to read some data from a file descriptor, ignoring EAGAIN errors
# (those errors mean that there are no data available for the moment)
def read_async(fd):
    try:
        return fd.read()
    except IOError as e:
        if e.errno != errno.EAGAIN:
            raise e
        else:
            return ""


def run_command(command):

    proc = subprocess.Popen(
        command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, close_fds=True
    )
    try:
        make_async(proc.stderr)
        make_async(proc.stdout)
        while True:
            select.select([proc.stdout, proc.stderr], [], [])

            output = read_async(proc.stdout)
            if output:
                logging.info(output.strip())
            output_err = read_async(proc.stderr)
            if output_err:
                logging.error(output_err.strip())

            if proc.poll() is not None:
                break
    finally:
        proc.stdout.close()
        proc.stderr.close()

    return proc.returncode


def run_command_get_stdout(command):
    return subprocess.check_output(command)


def download_gtfs(url):
    """
    Downloads the requested GTFS and saves it as local file.
    Returns the path to that file
    """
    logging.debug(f"Start downloading {url}")
    local_filename, headers = urllib.request.urlretrieve(url)

    # we try to get the filename from the Content-Disposition header, else we get it from the url
    fname_in_header = re.findall(
        'filename="?([^"]+)"?', headers.get("Content-Disposition", "")
    )
    if fname_in_header:
        fname = fname_in_header[0]
    else:
        fname = url.split("/")[-1]

    logging.debug(f"Downloading done at {local_filename} {fname}")

    return local_filename, fname
