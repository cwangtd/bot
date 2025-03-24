# Base
VERSION := $(shell /bin/date "+%Y-%m-%d-%H-%M-%S")

# Service
SERVICE := c-facade
STAGE := dev

# Docker
############################ 
# python:3.12.3-alpine3.19 #
############################
#CONTAINER_TAG := python-alpine
#BUILDER_IMAGE := python:3.12.3-alpine3.19
#RUNTIME_IMAGE := python:3.12.3-alpine3.19
#DOCKERFILE := Containerfiles/${CONTAINER_TAG}/Dockerfile
#PYPACKAGESFILE := Containerfiles/${CONTAINER_TAG}/py-libs/pyproject.toml


###################### 
# Base: ubuntu:24.04 #
######################
#CONTAINER_TAG := ubuntu
#BUILDER_IMAGE := ubuntu:24.04
#RUNTIME_IMAGE := ubuntu:24.04
#DOCKERFILE := Containerfiles/${CONTAINER_TAG}/poetry.Dockerfile # pip.Dockerfile, poetry.Dockerfile
#PYPACKAGESFILE := Containerfiles/${CONTAINER_TAG}/py-libs/pyproject.toml


##########################
# Project Root Directory #
##########################
BUILDER_IMAGE := ubuntu:24.04
RUNTIME_IMAGE := ubuntu:24.04
DOCKERFILE := Dockerfile
PYPACKAGESFILE := pyproject.toml


SERVICE_IMAGE := ${SERVICE}
PLATFORM := linux/amd64
PORT := 8010
NO_CACHE := false
TARGET_TAG := develop
TARGET_TAGS := base builder develop # TARGET_TAGS in Dockerfile
SHELL := /bin/bash
RELEASE := false

# Cloud Run
REGION := us-east1
DOCKER_LOCATION := us-east1-docker.pkg.dev
PROJECT_ID := provenance-a100
REPOSITORY := element
CLOUD_RUN_SERVICE := ${SERVICE}-${STAGE}
IMAGE_URI := ${DOCKER_LOCATION}/${PROJECT_ID}/${REPOSITORY}/${SERVICE}:${STAGE}
INGRESS := all
## all
## internal
## internal-and-cloud-load-balancing
MIN_INSTANCES := 1
MEMORY := 8Gi
CPU := 8
TIMEOUT := 300s

# Service Resources
AWS_SECRETS := 


##@ Helpers
.PHONY: help


help: ## Display this help.
	@awk 'BEGIN {FS = ":.*##"; printf "\nUsage:\n  make \033[36m\033[0m\n"} /^[a-zA-Z_-]+:.*?##/ { printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2 } /^##@/ { printf "\n\033[1m%s\033[0m\n", substr($$0, 5) } ' $(MAKEFILE_LIST) && echo


##@ Operatrions


printenv: ## print default makefile variables
	@echo "SERVICE: ${SERVICE}"
	@echo "STAGE: ${STAGE}"


##@ Release


release-all: c-download release tag-release push-release deploy ## build, tag, push, deploy 

release: ## build docker image
	@if [ "${NO_CACHE}" = "false" ]; then \
		echo "Build image with cache"; \
		DOCKER_BUILDKIT=1 docker build . -f ${DOCKERFILE} \
			--build-arg BUILDER_IMAGE=${BUILDER_IMAGE} \
			--build-arg RUNTIME_IMAGE=${RUNTIME_IMAGE} \
			--build-arg PORT=${PORT} \
			--build-arg STAGE=${STAGE} \
			--build-arg PYPACKAGESFILE=${PYPACKAGESFILE} \
			--build-arg RELEASE=${RELEASE} \
			--build-arg VERSION=${VERSION} \
			--progress=plain \
			--platform ${PLATFORM} \
			--target release \
			-t ${SERVICE}:${STAGE}; \
	else \
		echo "Build image with --no-cache flag"; \
		DOCKER_BUILDKIT=1 docker build . -f ${DOCKERFILE} --no-cache \
			--build-arg BUILDER_IMAGE=${BUILDER_IMAGE} \
			--build-arg RUNTIME_IMAGE=${RUNTIME_IMAGE} \
			--build-arg PORT=${PORT} \
			--build-arg STAGE=${STAGE} \
			--build-arg PYPACKAGESFILE=${PYPACKAGESFILE} \
			--build-arg RELEASE=${RELEASE} \
			--build-arg VERSION=${VERSION} \
			--progress=plain \
			--platform ${PLATFORM} \
			--target release \
			-t ${SERVICE}:${STAGE}; \
	fi

tag-release: ## tag docker image for gcp artifact registry
	@docker tag ${SERVICE}:${STAGE} ${IMAGE_URI}

push-release: ## push docker image to gcp artifact registry
	@docker push ${IMAGE_URI}

deploy: ## deploy docker image to gcp cloud run
	@gcloud beta run deploy ${CLOUD_RUN_SERVICE} \
		--image ${IMAGE_URI} \
		--region ${REGION} \
		--port ${PORT}  \
		--project ${PROJECT_ID} \
		--ingress ${INGRESS} \
		--memory ${MEMORY} \
		--cpu ${CPU} \
		--timeout ${TIMEOUT} \
		--allow-unauthenticated \
		--platform managed \
		--no-use-http2 \
		--cpu-boost \
		--service-min-instances ${MIN_INSTANCES}


##@ Config


c-download: ## Get config files from gcp secrets
	@for SECRETS in ${AWS_SECRETS}; do \
		echo "Clean old config file: src/configs/$${SECRETS}.json"; \
		rm -rf src/configs/$${SECRETS}.json; \
		echo "Getting config file: src/configs/$${SECRETS}.json"; \
		gcloud secrets versions access latest --secret=$${SECRETS} --out-file=src/configs/$${SECRETS}.json; \
		echo "Config file: src/configs/$${SECRETS}.json, Done!!"; \
	done \

c-update: ## Upload config files to gcp secrets
	@for SECRETS in ${AWS_SECRETS}; do \
		echo "Uploading config file: src/configs/$${SECRETS}.json"; \
		gcloud secrets versions add $${SECRETS} --data-file=src/configs/$${SECRETS}.json; \
		echo "Config file: src/configs/$${SECRETS}.json, Done!!"; \
	done

c-clean: ## Clean config files
	@for SECRETS in ${AWS_SECRETS}; do \
		echo "Clean config file: src/configs/$${SECRETS}.json"; \
		rm -rf src/configs/$${SECRETS}.json; \
	done


##@ Builds: Service docker images

devs-preparing: c-download ## preparing for devs

devs: ## build docker image with targets: ${TARGET_TAGS}
	@for TAG in $(TARGET_TAGS); do \
		DOCKER_BUILDKIT=1 docker build . -f ${DOCKERFILE} \
		--build-arg BUILDER_IMAGE=${BUILDER_IMAGE} \
		--build-arg RUNTIME_IMAGE=${RUNTIME_IMAGE} \
		--build-arg PYPACKAGESFILE=${PYPACKAGESFILE} \
		--build-arg RELEASE=${RELEASE} \
		--build-arg VERSION=${VERSION} \
		--progress=plain \
		--build-arg STAGE=${STAGE} \
		--platform ${PLATFORM} \
		--target $$TAG -t ${SERVICE_IMAGE}:$$TAG; \
	done


##@ Container Shell


container-shell: ## run ${SHELL} in container with docker image and given target 
	@echo "Run ${SHELL} in container with TARGET_TAG: ${TARGET_TAG}. TARGET_TAG: base develop"
	@docker run \
		-w /opt/dev \
		-v ${PWD}:/opt/dev \
		--rm -it ${SERVICE_IMAGE}:${TARGET_TAG} \
		${SHELL}

container-release-shell: ## run ${SHELL} in container with release docker image and given target
	@echo "Run ${SHELL} in container with TARGET_TAG: ${TARGET_TAG}. TARGET_TAG: release"
	@docker run \
		--rm -it ${SERVICE_IMAGE}:${STAGE} \
		${SHELL}

container-shell-py-libs: ## run ${SHELL} in container with base docker image and given target tp manage py-libs
	@echo "Run ${SHELL} in container with develop"
	@docker run \
		-w /opt/dev/py-libs \
		-v ${PWD}/${PYPACKAGESFILE}:/opt/dev/py-libs/pyproject.toml \
		--rm -it ${SERVICE_IMAGE}:builder \
		${SHELL}

##@ Images

print-built-images: ## print built images
	@docker images | grep ${SERVICE}

clean-built-images: ## clean built images
	@docker images | grep ${SERVICE} | awk '{print $$3}' | xargs docker rmi -f


##@ Launches


run-service: ## launch service with docker-compose file
	@docker compose -f ./docker-compose-${STAGE}.yml up -d --build

logs-service: ## show service logs with docker-compose file
	@docker compose -f ./docker-compose-${STAGE}.yml logs

stop-service: ## stop service with docker-compose file
	@docker compose -f ./docker-compose-${STAGE}.yml down

restart-service: stop-service run-service ## restart service with docker-compose file

run-release-service: ## launch service with docker-compose file
	@docker compose -f ./docker-compose.yml up -d --build

logs-release-service: ## show service logs with docker-compose file
	@docker compose -f ./docker-compose.yml logs

stop-release-service: ## stop service with docker-compose file
	@docker compose -f ./docker-compose.yml down

restart-release-service: stop-release-service run-release-service ## restart service with docker-compose file

##@ Benchmark


run-benchmark: ## run benchmark with ${STAGE}
	@docker-compose -f ./docker-compose-${STAGE}.yml up -d --build
	@docker-compose -f ./docker-compose-${STAGE}.yml exec ${SERVICE}-${STAGE} \
		locust -f /opt/benchmark/locustfile.py -H http://localhost:8089;

stop-benchmark: ## stop benchmark with ${STAGE}
	@docker-compose -f ./docker-compose-${STAGE}.yml down

run-cloud-benchmark: ## run benchmark
	@docker run \
		-w /opt \
		-v ${PWD}/benchmark:/opt/benchmark \
		-p 8089:8089 \
		--rm -it ${SERVICE_IMAGE}:develop \
		locust -f /opt/benchmark/locustfile.py -H http://localhost:8089;


##@ Lint


lint: ## py-lint
	@docker run \
		-w /opt/dev \
		-v ${PWD}:/opt/dev \
		--rm -it ${SERVICE_IMAGE}:develop \
		pylint src scripts


##@ TEST


testing: unit-testing integration-testing end-to-end-testing ## run all tests: unit, integration, end-to-end (Use 'make testing -j' for parallel execution)

unit-testing: ## run unit testing
	@docker run \
		-w /opt \
		-v ${PWD}/src/envs/ci.env:/opt/.env \
		-v ${PWD}/src/configs:/opt/configs \
		-v ${PWD}/src/app:/opt/app \
		-v ${PWD}/src/tests:/opt/tests \
		--rm -i ${SERVICE_IMAGE}:develop \
		pytest -vv tests/unit

integration-testing: ## run integration testing
	@docker run \
		-w /opt \
		-v ${PWD}/src/envs/ci.env:/opt/.env \
		-v ${PWD}/src/configs:/opt/configs \
		-v ${PWD}/src/app:/opt/app \
		-v ${PWD}/src/tests:/opt/tests \
		--rm -i ${SERVICE_IMAGE}:develop \
		pytest -vv tests/integration

end-to-end-testing: ## run end-to-end testing
	@docker run \
		-w /opt \
		-v ${HOME}/.config:/root/.config \
		-v ${PWD}/src/envs/ci.env:/opt/.env \
		-v ${PWD}/src/configs:/opt/configs \
		-v ${PWD}/src/app:/opt/app \
		-v ${PWD}/src/tests:/opt/tests \
        -v ${PWD}/logs:/opt/logs \
		--rm -i ${SERVICE_IMAGE}:develop \
		pytest -vv tests/end-to-end

test-cov: ## run test coverage
	@docker run \
		-w /opt \
		-v ${HOME}/.config:/root/.config \
		-v ${PWD}/src/app:/opt/app \
		-v ${PWD}/src/envs/ci.env:/opt/.env \
		-v ${PWD}/src/configs:/opt/configs \
		-v ${PWD}/src/tests:/opt/tests \
		-v ${PWD}/logs:/opt/logs \
		--rm -i ${SERVICE_IMAGE}:develop \
		pytest -vv --cov=app tests

test-env-shell: # (Not show on make -h) run shell in test container
	@docker run \
		-w /opt \
		-v ${HOME}/.config:/root/.config \
		-v ${PWD}/src/app:/opt/app \
		-v ${PWD}/src/envs/ci.env:/opt/.env \
		-v ${PWD}/src/configs:/opt/configs \
		-v ${PWD}/src/tests:/opt/tests \
		-v ${PWD}/logs:/opt/logs \
		--rm -it ${SERVICE_IMAGE}:develop \
		/bin/bash




###@ Profiling
#ITERATION := 1
#DEVELOP_IMAGE := ${SERVICE}:develop


#profiling: ## run profiling
	#@docker run \
		#-w /opt \
		#-v ${HOME}/.config:/root/.config \
		#-v ${PWD}/src/app:/opt/app \
		#-v ${PWD}/scripts:/opt/scripts \
		#--rm -it ${DEVELOP_IMAGE} \
		#python3 scripts/profile/profiler.py --iteration ${ITERATION}

run-service-without-docker: ## launch service without docker
	@uvicorn app.main:app --port ${PORT} --reload

run-with-gunicorn:
	@gunicorn app.main:app -w 2 -k uvicorn.workers.UvicornWorker --timeout 3600 --bind :${PORT} --limit-request-line 0 --limit-request-field_size 0 --log-level debug