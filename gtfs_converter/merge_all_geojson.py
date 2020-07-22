from jsonseq.encode import JSONSeqEncoder
import requests
import gzip
import logging


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


def merge_geojson():
    """
    Merge all geojson on transport.data.gouv.fr to create an aggregated dataset
    """
    logging.info("creating a big file for all french datasets")

    cpt = 0

    with gzip.open("/tmp/public-transit.geojsonl.gz", "wb") as outfile:
        for resource in _get_all_transport_geojson_resources():
            for chunk in JSONSeqEncoder().iterencode(_get_features(resource)):
                outfile.write(chunk.encode())

            cpt += 1

    logging.info(f"{cpt} files read")

