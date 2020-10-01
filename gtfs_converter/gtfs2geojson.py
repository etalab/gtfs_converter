import subprocess
import os
import logging
import re
import shutil
import utils

GEOJSON_CONVERTER = os.environ["GEOJSON_CONVERTER"]


def convert(gtfs_src, fname, tmp_dir):
    """
    Converts a given gtfs file and returns the path to the generated geojson.
    """
    logging.info(f"Start converting {gtfs_src} to geojson {tmp_dir}")

    output = f"{tmp_dir}/{fname}.geojson"
    ret = utils.run_command(
        [GEOJSON_CONVERTER, "--input", gtfs_src, "--output", output]
    )
    logging.debug(f"Conversion done with return code {ret}")
    if ret == 0:
        return output

    raise Exception("Unable to convert file")


def convert_sync(gtfs_src):
    return utils.run_command_get_stdout([GEOJSON_CONVERTER, "--input", gtfs_src])
