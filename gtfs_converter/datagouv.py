import os
import requests
import logging

DATAGOUV_API = os.environ["DATAGOUV_API"]
TRANSPORT_ORGANIZATION_ID = os.environ["TRANSPORT_ORGANIZATION_ID"]
DATAGOUV_API_KEY = os.environ["DATAGOUV_API_KEY"]
ORIGINAL_URL_KEY = "transport:original_resource_url"


def delete_community_resources(dataset_id, resources_id):
    """
    delete the community resources
    """
    headers = {"X-API-KEY": DATAGOUV_API_KEY}
    url = f"{DATAGOUV_API}/datasets/community_resources/{resources_id}"

    logging.info(
        "deleting a community resource %s on dataset %s", resources_id, dataset_id
    )
    ret = requests.delete(url, params={"dataset": dataset_id}, headers=headers)
    ret.raise_for_status()


def get_dataset_detail(dataset_id):
    ret = requests.get(f"{DATAGOUV_API}/datasets/{dataset_id}/")
    ret.raise_for_status()
    return ret.json()


def get_transport_community_resources(dataset_id):
    """
    get all community resources for a dataset
    """
    url = f"{DATAGOUV_API}/datasets/community_resources/"
    ret = requests.get(
        url, params={"dataset": dataset_id, "organization": TRANSPORT_ORGANIZATION_ID}
    )
    ret.raise_for_status()

    data = ret.json()["data"]

    return data


def create_community_resource(dataset_id, cr_file):
    """
    Creates a community resource and uploads the file

    This call will not link the resource. It requires and extra call
    """
    logging.debug("Creating a community resource on dataset %s", dataset_id)
    headers = {"X-API-KEY": DATAGOUV_API_KEY}
    files = {"file": open(cr_file, "rb")}
    url = f"{DATAGOUV_API}/datasets/{dataset_id}/upload/community/"

    ret = requests.post(url, headers=headers, files=files)
    ret.raise_for_status()
    json = ret.json()

    logging.debug(
        "Created a new community resource %s on dataset %s", json["id"], dataset_id
    )

    return json


def update_resource(dataset_id, resource_id, new_file, metadata):
    """
    Update a new file to a data.gouv resource, and set its metadata
    """
    logging.debug("Updating a resource on dataset %s", dataset_id)
    url = f"{DATAGOUV_API}/datasets/{dataset_id}/resources/{resource_id}/upload/"
    headers = {"X-API-KEY": DATAGOUV_API_KEY}
    files = {"file": open(new_file, "rb")}
    ret = requests.post(url, headers=headers, files=files)
    ret.raise_for_status()
    updated_resource_json = ret.json()

    # after the upload, we set the resource metadata
    # new_resource = {
    #     **updated_resource_json,
    #     **metadata
    # }
    new_resource = {**metadata, "id": resource_id}
    logging.debug("Updating metadata of resource %s", resource_id)

    url = f"{DATAGOUV_API}/datasets/{dataset_id}/resources/{resource_id}/"
    ret = requests.put(url, headers=headers, json=new_resource)
    ret.raise_for_status()
    logging.debug("Updating of resource %s done", resource_id)
