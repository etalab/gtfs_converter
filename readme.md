# Goal

Those scripts are made designed to convert files on transport.data.gouv.fr into differents formats.

The converted files are published as community resources on data.gouv.fr.

# Use

The API provides several usefull routes:

* `/convert_to_netex_and_geojson`: Convert the GTFS into a GeoJson And a NeTEx and publish the new filse as community resource on data.gouv.fr
* `/gtfs2netexfr`: Convert the GTFS into a ziped NeTEx and publish the new file as community resource on data.gouv.fr
* `/gtfs2geojson`: Convert the GTFS into a GeoJson and publish the new file as community resource on data.gouv.fr

All Those routes need the same parameters:
* required param: `url`: URL of the GTFS
* required param: `datagouv_id`: Id or the datagouv dataset containing the GTFS. This is used to publish the generated file on this dataset

# Run

## Locally

### Prerequisite

If you use [direnv](https://direnv.net/), copy the `envrc.example` to `.envrc` and set the credential. Else export those variable.

You need to have:
* [gtfs2netexfr](https://github.com/CanalTP/transit_model/tree/master/gtfs2netexfr) and set the env var `NETEX_CONVERTER` to the path to this binary
* [gtfs-to-geojson](https://github.com/rust-transit/gtfs-to-geojson) and set the env var `GEOJSON_CONVERTER` to the path to this binary

Those binaries need to be build ([rust](https://www.rust-lang.org/) is needed).

### Running the app

In a python3 virtual env :

`pip install -r requirements_dev.txt`

`honcho start`

You can then query the API on http://localhost:8080/

## With docker

Edit the docker_env file to set your credentials

Build the images if you want (else it will use the one pushed on [docker hub](hub.docker.com/)):
`docker-compose up`

Run the service:

`docker-compose up`


# Debuging

Some debuging tools are available in the `misc/cli_utils.py` file.

To run them you need `pip install -r requirements_dev.txt`.

Then you can run any function in the file like:
`python misc/cli_utils.py get_all_netex`
(don't forget to provide the environement variables).

The functions available are:
* `get_all_netex`: print all the datasets with their netex community resources
* `delete_all_netex`: delete the netex files created by transport.data.gouv.fr as community resource.
* `get_netex_duplicates`: print all the datasets that have duplicated netex files (with same names)
* `delete_old_netex_duplicates`: delete the old netex duplicates (only keep the last one)
