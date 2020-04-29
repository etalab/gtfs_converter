import tempfile
import requests
import os
import logging

DATAGOUV_API = os.environ['DATAGOUV_API']
TRANSPORT_ORGANIZATION_ID = os.environ['TRANSPORT_ORGANIZATION_ID']
DATAGOUV_API_KEY = os.environ['DATAGOUV_API_KEY']

def find_community_resources(dataset_id, netex_file):
    """
    Checks if the a community resource already exists
    """
    logging.debug("Searching community ressource %s in dataset %s", netex_file, dataset_id)
    url = f"{DATAGOUV_API}/datasets/community_resources/"
    params = {
        'dataset': dataset_id,
        'organization': TRANSPORT_ORGANIZATION_ID
    }
    ret = requests.get(url, params=params)
    ret.raise_for_status()

    data = ret.json()['data']

    if data is not None:
        filtered = [r for r in data if r['title'] == netex_file]
        if len(filtered) == 0:
            logging.debug("Found the dataset %s, but no existing ressource", dataset_id)
            return None

        if len(filtered) > 1:
            logging.warning("More that one community resource %s in dataset %s",
                           netex_file, dataset_id)
        logging.debug("Found dataset %s and matching community resource, with id %s",
                     dataset_id, filtered[0]['id'])
        return filtered[0]
    raise Exception(f"Searched community ressources of dataset {dataset_id}, could not understand response")


def create_community_resource(dataset_id, netex_file):
    """
    Creates a community resource and uploads the file

    This call will not link the resource. It requires and extra call
    """
    logging.debug('Creating a community resource on dataset %s', dataset_id)
    headers = {'X-API-KEY': DATAGOUV_API_KEY}
    files = {'file': open(netex_file, 'rb')}
    url = f"{DATAGOUV_API}/datasets/{dataset_id}/upload/community/"

    ret = requests.post(url, headers=headers, files=files)
    ret.raise_for_status()
    json = ret.json()

    logging.debug("Created a new community resource %s on dataset %s", json['id'], dataset_id)

    return json


def find_or_create_community_resource(dataset_id, netex_file):
    """
    When publishing a file, either the community resource already existed,
    then we only update the file.

    Otherwise we create a new resource
    """
    community_resource = find_community_resources(dataset_id, netex_file)
    if community_resource is not None:
        upload_resource(community_resource['id'], netex_file)
        return community_resource
    return create_community_resource(dataset_id, netex_file)


def update_resource_metadata(dataset_id, resource):
    """
    Updates metadata of the resources.

    This call is opportant to link the resource to a dataset.

    It also sets the organisation, format and description.

    Does not return
    """
    logging.debug("Updating metadata of resource %s", resource['id'])
    resource['dataset'] = dataset_id
    resource['organization'] = TRANSPORT_ORGANIZATION_ID
    resource['description'] = """Converstion du fichier automatique du fichier GTFS au format NeTEx (profil France)

La conversion est effecutée par transport.data.gouv.fr en utilisant l’outil https://github.com/CanalTP/transit_model
    """
    resource['format'] = 'NeTEx'

    url = f"{DATAGOUV_API}/datasets/community_resources/{resource['id']}/"
    headers = {'X-API-KEY': DATAGOUV_API_KEY}

    ret = requests.put(url, headers=headers, json=resource)
    ret.raise_for_status()
    logging.debug("Updating of resource %s done", resource['id'])


def upload_resource(resource_id, filename):
    """
    Replaces the file of an existing resource.

    After the call, and update to that resource is needed
    """
    logging.debug("Uploading an new file %s on resource %s", filename, resource_id)
    url = f"{DATAGOUV_API}/datasets/community_resources/{resource_id}/upload/"
    headers = {'X-API-KEY': DATAGOUV_API_KEY}
    ret = requests.post(url, headers=headers, files={'file': open(filename, 'rb')})
    ret.raise_for_status()
    logging.debug("Uploading an new file %s on resource %s done", filename, resource_id)


def publish_to_datagouv(dataset_id, netex_file):
    """
    This will publish the netex file as a community resource of the dataset.

    If the community resource already existed, it will be updated
    """
    try:
        logging.info("Going to add the file %s as community ressource to the dataset %s",
                    netex_file, dataset_id)
        community_resource = find_or_create_community_resource(dataset_id, netex_file)
        update_resource_metadata(dataset_id, community_resource)
        logging.info("Added %s to the dataset %s", netex_file, dataset_id)
    except requests.HTTPError as err:
        logging.warning("Unable to add %s to the dataset %s. Http Error %s",
                       netex_file, dataset_id, err)
    except Exception as err:
        logging.warning("Unable to add %s to the dataset %s. Generic Error %s",
                       netex_file, dataset_id, err)