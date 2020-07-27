import utils
from jsonseq.encode import JSONSeqEncoder
import requests
import gzip
import logging
import tempfile
import os
import datagouv
from pylogctx import context as log_context

AGGREGATED_DATASET_ID = os.environ["AGGREGATED_DATASET_ID"]


def _get_all_transport_geojson_resources():
    r = requests.get("https://transport.data.gouv.fr/api/datasets")
    r.raise_for_status()
    datasets = r.json()
    resources = []
    for d in datasets:
        if d["type"] != "public-transit":
            continue
        for r in d["community_resources"]:
            url = r.get("url")
            if not url:
                continue
            if (
                r["community_resource_publisher"]
                != "Point d'Accès National transport.data.gouv.fr"
            ):
                continue
            if r["format"] != "geojson":
                continue
            if "geojson" not in r["title"]:
                continue

            resources.append(
                {
                    "resource_url": url,
                    "datagouv_dataset_id": d["id"],
                    "dataset_title": d["title"],
                }
            )
    logging.info(f"there are {len(resources)} geojson")
    return resources


def _get_features(resource):
    url = resource["resource_url"]
    r = requests.get(url)
    if r.status_code != requests.codes.ok:
        return []
    geojson = r.json()
    for f in geojson.get("features", []):
        # we add some metadata on each feature
        f.update(resource)
        yield f


def _create_merged_geojson_line(directory):
    """
    Merge all geojson on transport.data.gouv.fr to create an aggregated dataset with one geojson per line
    """
    logging.info("creating a big file for all french datasets")

    cpt = 0

    output_file_path = f"{directory}/public-transit.geojsonl"
    with open(output_file_path, "w") as outfile:
        for resource in _get_all_transport_geojson_resources():
            for chunk in JSONSeqEncoder().iterencode(_get_features(resource)):
                outfile.write(chunk)

            cpt += 1

    logging.info(f"{cpt} files read")
    return output_file_path


def _publish_to_datagouv(ziped_geojson, ziped_geojson_line, geopackage):
    resources_id = {
        r["title"]: r["id"]
        for r in datagouv.get_dataset_detail(AGGREGATED_DATASET_ID)["resources"]
    }

    logging.info("publishing to datagouv")
    datagouv.update_resource(
        AGGREGATED_DATASET_ID,
        resources_id["public-transit.geojsonl.zip"],
        ziped_geojson_line,
        metadata={
            "description": """Fichier contenant la position des arrêts ainsi que le tracès des lignes de france.
Chaque ligne correspond à un [GeoJSON](https://fr.wikipedia.org/wiki/GeoJSON), suivant le format [json-lines](http://jsonlines.org/).""",
            "format": "geojsonl",
            "mime": "application/zip",
        },
    )
    datagouv.update_resource(
        AGGREGATED_DATASET_ID,
        resources_id["public-transit.geojson.zip"],
        ziped_geojson,
        metadata={
            "description": """Fichier [GeoJSON](https://fr.wikipedia.org/wiki/GeoJSON) contenant la position des arrêts ainsi que le tracès des lignes de france.""",
            "format": "geojson",
            "mime": "application/zip",
        },
    )
    datagouv.update_resource(
        AGGREGATED_DATASET_ID,
        resources_id["public-transit.gpkg"],
        geopackage,
        metadata={
            "description": """Fichier [GeoPackage](https://www.geopackage.org/) contenant la position des arrêts ainsi que le tracès des lignes de france.""",
            "format": "geopackage",
            "mime": "application/geopackage+sqlite3",
        },
    )


def merge_geojson():
    """
    Merge all geojson on transport.data.gouv.fr to create 3 aggregated datasets:
    - 1 geojsonline
    - 1 geojson
    - geopackage

    and publish those resources on data.gouv
    """
    with log_context(task_id="merge_geojson"):
        with tempfile.TemporaryDirectory() as tmp_dir:
            geojson_line_file = _create_merged_geojson_line(tmp_dir)
            logging.info(f"geojson line created: {geojson_line_file}")

            geopackage_file = f"{tmp_dir}/public-transit.gpkg"
            geojson_file = f"{tmp_dir}/public-transit.geojson"
            utils.run_command(
                ["ogr2ogr", geopackage_file, f"GeoJSONSeq:{geojson_line_file}"]
            )

            ziped_geojson_file = f"{geojson_file}.zip"
            ziped_geojson_line_file = f"{geojson_line_file}.zip"
            utils.run_command(
                ["ogr2ogr", geojson_file, f"GeoJSONSeq:{geojson_line_file}"]
            )
            utils.run_command(["zip", "--junk-paths", f"{ziped_geojson_file}", geojson_file])
            utils.run_command(["zip", "--junk-paths", f"{ziped_geojson_line_file}", geojson_line_file])

            _publish_to_datagouv(
                ziped_geojson_file, ziped_geojson_line_file, geopackage_file
            )
            logging.info("all files published")
