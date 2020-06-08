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

    ret = utils.run_command(
        [
            GEOJSON_CONVERTER,
            "--input",
            gtfs_src,
            ">", output
        ]
    )
    logging.debug(f"Conversion done with return code {ret}")
    if ret == 0:

        return f"{netex_zip}.zip"

    raise Exception("Unable to convert file")
