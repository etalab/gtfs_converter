import tempfile
import requests
import os
import logging
import fire
import collections


logging.basicConfig(
    level=logging.INFO, format="%(asctime)s -- %(levelname)s -- %(message)s"
)

DATAGOUV_API = os.environ["DATAGOUV_API"]
TRANSPORT_ORGANIZATION_ID = os.environ["TRANSPORT_ORGANIZATION_ID"]
DATAGOUV_API_KEY = os.environ["DATAGOUV_API_KEY"]


def _find_community_resources(dataset_id):
    """
    returns all netex created as $TRANSPORT_ORGANIZATION_ID as community resource
    """
    logging.debug("Searching community ressource in dataset %s", dataset_id)
    url = f"{DATAGOUV_API}/datasets/community_resources/"
    params = {"dataset": dataset_id, "organization": TRANSPORT_ORGANIZATION_ID}
    ret = requests.get(url, params=params)
    ret.raise_for_status()

    data = ret.json()["data"]

    if data is not None:
        # Note: datagouv lowercase the file names, so we do the same
        return [r for r in data if r["title"].lower().endswith("netex.zip")]
    raise Exception(
        f"Searched community ressources of dataset {dataset_id}, could not understand response"
    )


def _delete_community_resources(dataset_id, resources):
    """
    delete the community resources
    """
    logging.debug("deleting %s", resources)
    headers = {"X-API-KEY": DATAGOUV_API_KEY}

    for r in resources:
        url = f"{DATAGOUV_API}/datasets/community_resources/{r['id']}"

        logging.info(
            "deleting a community resource %s on dataset %s", r["title"], dataset_id
        )
        ret = requests.delete(url, params={"dataset": dataset_id}, headers=headers)
        ret.raise_for_status()


def _delete_dataset_netex(dataset_id):
    """
    This will delete the associated netex resources
    """
    try:
        logging.info("Going to delete the netex file of the dataset %s", dataset_id)
        community_resource = _find_community_resources(dataset_id)
        _delete_community_resources(dataset_id, community_resource)
        logging.info("deleted community resource for the dataset %s", dataset_id)
    except requests.HTTPError as err:
        logging.warning(
            "Unable to delete to the dataset %s. Http Error %s", dataset_id, err
        )
    except Exception as err:
        logging.warning(
            "Unable to delete to the dataset %s. Generic Error %s", dataset_id, err
        )


def delete_all_netex():
    logging.warning(
        "*** deleting all netex files created by transport.data.gouv.fr ***"
    )
    r = requests.get("https://transport.data.gouv.fr/api/datasets")
    r.raise_for_status()
    datasets = r.json()

    for d in datasets:
        dataset_name = d["title"]
        if d["type"] != "public-transit":
            continue
        _delete_dataset_netex(d["datagouv_id"])


def _get_duplicated_resources(community_resources):
    r_by_keys = collections.defaultdict(list)
    for r in community_resources:
        r_by_keys[r["title"]].append(r)

    return [(k, v) for (k, v) in r_by_keys.items() if len(v) > 1]


def get_netex_duplicates():
    r = requests.get("https://transport.data.gouv.fr/api/datasets")
    r.raise_for_status()
    datasets = r.json()

    for d in datasets:
        dataset_name = d["title"]
        if d["type"] != "public-transit":
            continue

        rs = _find_community_resources(d["datagouv_id"])
        if not rs:
            continue

        duplicated_resources = _get_duplicated_resources(rs)
        if duplicated_resources:
            logging.info(f"dup for dataset {d['id']}")
            for dup in duplicated_resources:
                logging.info(f"- {dup[0]}")
                for r in dup[1]:
                    logging.info(f" * {r['id']} ({r['last_modified']})")


def delete_old_netex_duplicates():
    logging.warn("DELETING OLD NETEX DUPLICATES!")
    r = requests.get("https://transport.data.gouv.fr/api/datasets")
    r.raise_for_status()
    datasets = r.json()

    for d in datasets:
        dataset_name = d["title"]
        if d["type"] != "public-transit":
            continue

        rs = _find_community_resources(d["datagouv_id"])
        if not rs:
            continue

        duplicated_resources = _get_duplicated_resources(rs)
        if duplicated_resources:
            logging.info(f"dup for dataset {d['id']}")
            for dr in duplicated_resources:
                logging.info(f"- {dr[0]}")
                duplicates = dr[1]
                duplicates.sort(key=lambda r: r["last_modified"])
                oldest = duplicates[:-1]

                logging.info(
                    f"  keeping {duplicates[-1]['id']} ({duplicates[-1]['last_modified']})"
                )
                for r in oldest:
                    logging.info(f"   * removing old {r['id']} ({r['last_modified']})")
                    _delete_community_resources(d["id"], [r])


if __name__ == "__main__":
    fire.Fire()
