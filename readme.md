# Goal

Those scripts are made designed to convert files on transport.data.gouv.fr into differents formats.

The converted files are published as community resources.

# Run

First build the docker image
`docker build . -t nap_converter`

Edit the docker_env file to set your credentials

Run the service

`docker run --env-file docker_env -p8080:8080 nap_converter`
