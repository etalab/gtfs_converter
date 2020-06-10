import tempfile
import requests
import os
import logging

DATAGOUV_API = os.environ["DATAGOUV_API"]
TRANSPORT_ORGANIZATION_ID = os.environ["TRANSPORT_ORGANIZATION_ID"]
DATAGOUV_API_KEY = os.environ["DATAGOUV_API_KEY"]


def _format_title_as_datagouv(title):
    return title.replace("_", "-").lower()


def find_community_resources(dataset_id, new_file):
    """
    Checks if the a community resource already exists
    """
    logging.debug(
        "Searching community ressource %s in dataset %s", new_file, dataset_id
    )
    url = f"{DATAGOUV_API}/datasets/community_resources/"
    params = {"dataset": dataset_id, "organization": TRANSPORT_ORGANIZATION_ID}
    ret = requests.get(url, params=params)
    ret.raise_for_status()

    data = ret.json()["data"]
    file_name = os.path.basename(new_file)

    if data is not None:
        # Note: datagouv lowercase the file names, so we do the same
        filtered = [
            r
            for r in data
            if _format_title_as_datagouv(r["title"])
            == _format_title_as_datagouv(file_name)
        ]
        logging.debug("title = %s", _format_title_as_datagouv(file_name))
        logging.debug("community resources: %s", [r["title"] for r in data])
        if len(filtered) == 0:
            logging.debug("Found the dataset %s, but no existing ressource", dataset_id)
            return None

        if len(filtered) > 1:
            logging.warning(
                "More that one community resource %s in dataset %s",
                file_name,
                dataset_id,
            )
        logging.debug(
            "Found dataset %s and matching community resource, with id %s",
            dataset_id,
            filtered[0]["id"],
        )
        return filtered[0]
    raise Exception(
        f"Searched community ressources of dataset {dataset_id}, could not understand response"
    )


def create_community_resource(dataset_id, netex_file):
    """
    Creates a community resource and uploads the file

    This call will not link the resource. It requires and extra call
    """
    logging.debug("Creating a community resource on dataset %s", dataset_id)
    headers = {"X-API-KEY": DATAGOUV_API_KEY}
    files = {"file": open(netex_file, "rb")}
    url = f"{DATAGOUV_API}/datasets/{dataset_id}/upload/community/"

    ret = requests.post(url, headers=headers, files=files)
    ret.raise_for_status()
    json = ret.json()

    logging.debug(
        "Created a new community resource %s on dataset %s", json["id"], dataset_id
    )

    return json


def find_or_create_community_resource(dataset_id, new_file):
    """
    When publishing a file, either the community resource already existed,
    then we only update the file.

    Otherwise we create a new resource
    """
    community_resource = find_community_resources(dataset_id, new_file)
    if community_resource is not None:
        upload_resource(community_resource["id"], new_file)
        return community_resource
    return create_community_resource(dataset_id, new_file)


def update_resource_metadata(dataset_id, resource, additional_metadata):
    """
    Updates metadata of the resources.

    This call is opportant to link the resource to a dataset.

    It also sets the organisation, format and description.

    Does not return
    """
    logging.debug("Updating metadata of resource %s", resource["id"])
    resource.update(additional_metadata)
    resource["dataset"] = dataset_id
    resource["organization"] = TRANSPORT_ORGANIZATION_ID

    url = f"{DATAGOUV_API}/datasets/community_resources/{resource['id']}/"
    headers = {"X-API-KEY": DATAGOUV_API_KEY}

    ret = requests.put(url, headers=headers, json=resource)
    ret.raise_for_status()
    logging.debug("Updating of resource %s done", resource["id"])


def upload_resource(resource_id, filename):
    """
    Replaces the file of an existing resource.

    After the call, and update to that resource is needed
    """
    logging.debug("Uploading an new file %s on resource %s", filename, resource_id)
    url = f"{DATAGOUV_API}/datasets/community_resources/{resource_id}/upload/"
    headers = {"X-API-KEY": DATAGOUV_API_KEY}
    ret = requests.post(url, headers=headers, files={"file": open(filename, "rb")})
    ret.raise_for_status()
    logging.debug("Uploading done")


def publish_to_datagouv(dataset_id, new_file, additional_metadata):
    """
    This will publish the converted file as a community resource of the dataset.

    If the community resource already existed, it will be updated
    """
    try:
        logging.info(
            "Going to add the file %s as community ressource to the dataset %s",
            new_file,
            dataset_id,
        )
        community_resource = find_or_create_community_resource(dataset_id, new_file)
        update_resource_metadata(dataset_id, community_resource, additional_metadata)
        logging.info("Added %s to the dataset %s", new_file, dataset_id)
    except requests.HTTPError as err:
        logging.warning(
            "Unable to add %s to the dataset %s. Http Error %s",
            new_file,
            dataset_id,
            err,
        )
    except Exception as err:
        logging.warning(
            "Unable to add %s to the dataset %s. Generic Error %s",
            new_file,
            dataset_id,
            err,
        )
