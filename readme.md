# Goal

Those scripts are made designed to convert files on transport.data.gouv.fr into differents formats.

The converted files are published as community resources.

# Run

First build the docker image
`docker build . -t nap_converter`

Edit the docker_env file to set your credentials

Run the service

`docker run --rm --env-file docker_env -p8080:8080 nap_converter`


# Debuging

Some debuging tools are available in the `misc/cli_utils.py` file.

To run them you need `pip install -r requirements_dev.txt`.

Then you can run any function in the file like:
`python misc/cli_utils.py get_all_netex`
(don't forget to provide the environement variables).

The functions available are:
* `get_all_netex`: print all the datasets with their netex community resources
* `delete_all_netex`: delete the netex files created by transport.data.gouv.fr as community resource.
