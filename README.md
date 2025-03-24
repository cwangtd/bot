# Provenance-c-check-facade

## Descriptions

Facade service for the provenance-c-check service. This service is responsible for handling the requests from the client and forwarding them to the provenance-c-check service. It also handles the responses from the provenance-c-check service and returns them to the client.

In the following sections, I will show you how to build and run this service locally.

* [Descriptions](#descriptions)
* [Preparing](#preparing)
    * [Google Cloud SDK Configuration And Permissions](#google-cloud-sdk-configuration-and-permissions)
    * [Make Commands](#make-commands)
* [Prepare The Development Environment](#prepare-the-development-environment)
    * [Prepare The Development Environment](#prepare-the-development-environment)
    * [Build Service Development Docker Images](#build-service-development-docker-images)
    * [Launch / Stop Service With Development Docker Images Locally](#launch--stop-service-with-development-docker-images-locally*)
* [Build and Run the Release Service Locally](#build-and-run-the-release-service-locally)
    * [Prepare The Release Service Environment](#prepare-the-release-service-environment)
    * [Build Release Docker Images](#build-release-docker-images)
    * [Launch / Stop Release Service Locally](#launch--stop-release-service-locally)
* [Testing](#testing)
* [Python Dependencies Management](#python-dependencies-management)
* [Others](#others)
    * [Logs](#logs)
    * [Linting](#linting)

## Preparing

### Google Cloud SDK Configuration And Permissions

Firstly, make sure you have installed google-cloud-sdk - [installation](https://formulae.brew.sh/cask/google-cloud-sdk). 
And then, you can run the following command to login with your GCP account and set the default project:

    # Login with your GCP account to initiates the authentication process.
    $ gcloud auth login

    # Login with your GCP account to authorize your local application to access Google Cloud services using your user credentials.
    $ gcloud auth application-default login

    # Set the default project
    $ gcloud config set project <project_id>

    # Displays the current configuration settings for your gcloud command-line tool.
    $ gcloud config list

Please ensure that your GCP account in the 'provenance-a100' project has sufficient permissions to execute GCP monitoring and instance-related APIs.
If, when running this service, you encounter Google permission issues while making API calls, please request assistance from the DevOps team to grant the necessary permissions. 
The simplest approach would be to directly add 'editor' permissions for the developers.

### Make Commands

To build the service, this project provides a set of Makefile commands that you can use during development.
To view the available commands and their descriptions, you can run "make" or "make help" in your terminal.

    $ make
    or
    $ make help

In next sections, it will show you how to use these commands to build and run the service.

## Build and Run the Dev Service Locally

### Prepare The Development Environment

To build and run the service, you will need to prepare configuration files: secrets from GCP secret-manager.
This service has the following secret resource from GCP secret-manager:
Hint: This service does not have any secret resources from GCP secret-manager.

TBD: It would be better to create api secret resources in GCP secret-manager for the service to authenticate with the provenance-c-check service.

You can just run the following command to download these configuration files from GCP secret-manager:

    $ make preparing # It will download the configuration file from GCP secret-manager.

### Build Service Development Docker Images

After preparing the development environment, you can run the following command to build the Docker images for the service: 

    $ make devs

By running this command, you will initiate the build process for Docker images, specifically targeting the tags: `base` and `develop`.
- The `base` tag refer to the base image with essential dependencies.
- The `develop` tag include additional tools, 3rd-party python packages and configurations required for development.

### Launch / Stop Service With Development Docker Images Locally

To run the service, you can run the following command:

    $ make run-service

The servie will host on the port ``8010`` by default.

After running the previously mentioned commands and successfully deploying the service,
you can open a web browser and navigate to `http://localhost:8010/docs`. (The default SERVICE_STAGE is `dev`)
This URL will direct you to the Swagger UI of the service, you can find more details about the service and its APIs there.

If you want to stop the service, you can run the following command:

    $ make stop-service

Or you can just run the following command to restart the service:

    $ make restart-service

## Build and Run the Release Service Locally

This section will show you how to build and run the release service locally.
Almost the same as the development service, you need to prepare the development environment and build the Docker images for the release service.

### Prepare The Release Service Environment

Same as the development service, you can run the following command to download the configuration files from GCP secret-manager:

    $ make preparing # It will download the configuration file from GCP secret-manager.

### Build Release Docker Images

In this project, I package the service into a Docker image with tag: `release`. You can run the following command to build the release image:

    $ make release

This command will build a Docker image with the tag: `release`.

### Launch / Stop Release Service Locally

Once the release image is built, you can run the following command to start a container for the release service locally:

    $ make run-release-service

The service will host on the port `8010` by default.

After running the previously mentioned commands and successfully deploying the service, you can open a web browser and navigate to `http://localhost:8010/docs` to access the Swagger UI of the service.

If you want to stop the service, you can run the following command:

    $ make down-release-service

Or you can just run the following command to restart the service:

    $ make restart-release-service

## Testing

In this project, it uses the Python library pytest to build the test cases.
The test case files are stored in the `src/tests` directory. It includes the unit test cases and end-to-end test cases.
You can run the following command to execute the test cases:

    $ make testing             # Run all test cases including unit test cases and end-to-end test cases 
    $ make unit-testing        # Run the unit test cases
    $ make end-to-end-testing  # Run the end-to-end test cases

All test cases will be executed in the Docker container, it will ensure the test environment is consistent with the production environment.
And it can let developers run the test cases in the CI/CD pipeline.
Also, do not concern about the test environment. (e.g. python version, python dependencies)

## Python Dependencies Management

In this project, it use [poetry](https://python-poetry.org/) to manage python dependencies.
You can run the following steps to update or add python dependencies:

Fisrtly, we prepare a docker container for the poetry shell, you can run the following command to launch the container:

    $ make container-shell
    (container) $ poetry 

After launching the container, you can run the following commands to update or add python dependencies:

    # Add a new package
    (container) $ poetry add <package_name>
    # Update a package
    (container) $ poetry update <package_name>
    # Install all packages, it will also update the lock file: poetry.lock
    (container) $ poetry install

## Others

### Logs

You can view the logs of the service by running the following command:

    $ tail -f logs/app.log

### Linting

To check the code quality in the project using pylint, you can run the following command:

    $ make lint

## Not Ready

### Development

Once you have built the necessary Docker images for the project, you can run the following command to start a container specifically for:


### Benchmark

In this project, I use the Python library Locust to build the benchmark. You can initiate the benchmark by executing the following command:

    $ make benchmark

Once the benchmark is running, you can open a web browser and visit `http://localhost:8089/` to begin the benchmarking process.

## Reference
