import datagouv

import tempfile
import requests
import os
import logging

DATAGOUV_API = datagouv.DATAGOUV_API
TRANSPORT_ORGANIZATION_ID = datagouv.TRANSPORT_ORGANIZATION_ID
DATAGOUV_API_KEY = datagouv.DATAGOUV_API_KEY
ORIGINAL_URL_KEY = datagouv.ORIGINAL_URL_KEY


def _format_title_as_datagouv(title):
    return title.replace("_", "-").lower()


def find_community_resources(dataset_id, new_file, resource_url, resource_format):
    """
    Checks if the a community resource already exists
    """
    data = datagouv.get_transport_community_resources(dataset_id)
    file_name = os.path.basename(new_file)
    resource_format = (
        resource_format.lower()
    )  # datagouv lower case the format, we should do the same

    if data is not None:
        # Note: datagouv lowercase the file names, so we do the same
        filtered = [
            r
            for r in data
            if r.get("extras", {}).get(ORIGINAL_URL_KEY) == resource_url
            and resource_format == r.get("format")
        ]
        logging.debug(
            "title = %s, url = %s, format = %s",
            _format_title_as_datagouv(file_name),
            resource_url,
            resource_format,
        )
        logging.debug(
            "community resources: %s",
            [
                (r["title"], r.get("extras", {}).get(ORIGINAL_URL_KEY), r.get("format"))
                for r in data
            ],
        )
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


def find_or_create_community_resource(dataset_id, new_file, url):
    """
    When publishing a file, either the community resource already existed,
    then we only update the file.

    Otherwise we create a new resource
    """
    community_resource = find_community_resources(
        dataset_id, new_file, url, resource_format
    )
    if community_resource is not None:
        upload_resource(community_resource["id"], new_file)
        return community_resource
    return datagouv.create_community_resource(dataset_id, new_file)


def update_resource_metadata(dataset_id, resource, additional_metadata, url):
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
    resource["extras"] = {ORIGINAL_URL_KEY: url}

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


def publish_to_datagouv(dataset_id, new_file, additional_metadata, url):
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
        community_resource = find_or_create_community_resource(
            dataset_id, new_file, url, resource_format=additional_metadata["format"]
        )
        update_resource_metadata(
            dataset_id, community_resource, additional_metadata, url
        )
        logging.info("Added %s to the dataset %s", new_file, dataset_id)
    except requests.HTTPError as err:
        logging.warning(
            "Unable to add %s to the dataset %s. Http Error %s",
            new_file,
            dataset_id,
            err,
        )
    except Exception as err:
        logging.exception("Unable to add %s to the dataset %s", new_file, dataset_id)
