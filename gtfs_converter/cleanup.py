import requests
import logging
import os
import datagouv
from pylogctx import context as log_context

TRANSPORT_API_ENDPOINT = "https://transport.data.gouv.fr"


def _cleanup_old_dataset_resources(dataset):
    """
    for a dataset, we check that all community resource's original resource is still there.
    If not, we delete the deprecated community resource.
    """
    dataset_id = dataset["datagouv_id"]
    resources_url = {
        r["original_url"]: r["datagouv_id"] for r in dataset.get("resources", [])
    }

    nb_cleaned = 0

    for cr in dataset.get("community_resources", []):
        if (
            cr.get("community_resource_publisher")
            != "Point d'Accès National transport.data.gouv.fr"
        ):
            # we want to cleanup only community resources created by the PAN
            continue

        original_resource_url = cr["original_resource_url"]

        if original_resource_url in resources_url:
            # there is a main resource linked to this community ressource, we can keep it
            continue

        # we can cleanup the resource
        logging.info(
            f'for dataset {dataset_id}, resource {cr["title"]} | {cr["url"]} | original_url = {original_resource_url} is deprecated and will be deleted'
        )

        datagouv.delete_community_resources(dataset_id, cr["datagouv_id"])
        logging.info(
            "deleted community resource %s (#%s) for the dataset %s",
            cr["url"],
            cr["datagouv_id"],
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
        r = requests.get(f"{TRANSPORT_API_ENDPOINT}/api/datasets")
        r.raise_for_status()
        datasets = r.json()

        total_cleaned = 0

        for d in datasets:
            dataset_name = d["title"]
            if d["type"] != "public-transit":
                continue
            cleaned = _cleanup_old_dataset_resources(d)
            total_cleaned += cleaned
        logging.info(f"{total_cleaned} resources cleaned")
