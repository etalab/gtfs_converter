import requests
import logging
import os
import datagouv
from pylogctx import context as log_context


def _get_real_urls(dataset_id):
    """
    the resources has several urls, like the datagouv one and the real one 
    (`url` and `latest_url` in transport.data.gouv.fr)).
    So we need to query the datagouv api to be able to compare the urls
    """
    detail = datagouv.get_dataset_detail(dataset_id)
    return [r["url"] for r in detail.get("resources", [])]


def _cleanup_old_dataset_resources(dataset_id):
    resources_urls = frozenset(_get_real_urls(dataset_id))
    community_resources = datagouv.get_transport_community_resources(dataset_id)
    nb_cleaned = 0

    for cr in community_resources:
        original_resource_url = cr.get("extras", {}).get(datagouv.ORIGINAL_URL_KEY)
        key = (original_resource_url, cr["format"])
        if original_resource_url not in resources_urls:
            logging.info(
                f'for dataset {dataset_id}, resource {cr["title"]} | {cr["url"]} | original_url = {original_resource_url} is deprecated and will be deleted'
            )

            datagouv.delete_community_resources(dataset_id, cr["id"])
            logging.info(
                "deleted community resource %s (#%s) for the dataset %s",
                cr["url"],
                cr["id"],
                dataset_id,
            )
            nb_cleaned += 1
    return nb_cleaned


def cleanup_old_resources():
    """
    Delete the community resources when the main resource has been deleted
    """
    with log_context(task_id="cleanup"):
        logging.info("Cleaning up old resources")
        r = requests.get("https://transport.data.gouv.fr/api/datasets")
        r.raise_for_status()
        datasets = r.json()

        total_cleaned = 0

        for d in datasets:
            dataset_name = d["title"]
            if d["type"] != "public-transit":
                continue
            cleaned = _cleanup_old_dataset_resources(d["id"])
            total_cleaned += cleaned
        logging.info(f"{cleaned} resources cleaned")
