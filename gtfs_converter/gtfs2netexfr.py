import os
import logging
import shutil
import utils

NETEX_CONVERTER = os.environ["NETEX_CONVERTER"]
PUBLISHER = os.environ.get("NETEX_PUBLISHER", "transport.data.gouv.fr")


def convert(gtfs_src, fname, netex_dir):
    """
    Converts a given gtfs file and returns the path to the generated netex zip file.
    The publisher is the name of the organization that published that dataset.
    """
    logging.info(f"Start converting {gtfs_src} to {netex_dir}")

    ret = utils.run_command(
        [
            NETEX_CONVERTER,
            "--input",
            gtfs_src,
            "--output",
            netex_dir,
            "--participant",
            PUBLISHER,
        ]
    )
    logging.debug(f"Conversion done with return code {ret}")
    if ret == 0:
        netex_zip = f"{fname}.netex"
        shutil.make_archive(netex_zip, "zip", netex_dir)
        return f"{netex_zip}.zip"

    raise Exception("Unable to convert file")
