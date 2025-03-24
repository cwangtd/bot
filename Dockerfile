ARG BUILDER_IMAGE RUNTIME_IMAGE


####################
# Base image #
####################
FROM ${BUILDER_IMAGE} AS base

# set environment variables
ENV PYTHONFAULTHANDLER=1 \
    PYTHONHASHSEED=random \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y \
    libssl-dev \
    libffi-dev \
    python3-dev \
    python3-pip \
    python-is-python3 \
    python3-venv


####################
# Builder image #
####################
FROM base AS builder

ENV PIP_DEFAULT_TIMEOUT=100 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1

RUN apt-get install --no-install-suggests --no-install-recommends --yes pipx

RUN pipx install poetry
RUN pipx inject poetry poetry-plugin-bundle

ENV PATH=/root/.local/bin:$PATH

ARG PYPACKAGESFILE RELEASE

COPY ./${PYPACKAGESFILE} ./

COPY README.md ./

RUN if "$RELEASE" == "true" ; then \
    poetry bundle venv --python=/usr/bin/python3 --only=main /venv; \
    else \
    poetry bundle venv --python=/usr/bin/python3 /venv; \
    fi


####################
# Development image #
####################
From ${RUNTIME_IMAGE} AS develop

# set environment variables
ENV PYTHONFAULTHANDLER=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONHASHSEED=random \
    PYTHONUNBUFFERED=1 \
    PATH=/venv/bin:$PATH \
    WORKSPACE=/opt \
    APP_PATH=/opt \
    ENV_PATH=/opt/.env

RUN apt-get update && apt-get install -y python3-dev
#################### Firefox and GeckoDriver ####################
WORKDIR /opt/browsers

COPY --from=builder /venv /venv

ENV PATH=/venv/bin:$PATH
RUN playwright install-deps && playwright install firefox
#ENV GOOGLE_APPLICATION_CREDENTIALS=/opt/configs/image-web-detector-dev-service-secret.json

WORKDIR /opt


#RUN groupadd -g 10001 appgroup && \
   #useradd -u 10000 -g appgroup appuser \
   #&& chown -R appuser:appgroup /opt /usr/bin/geckodriver /usr/bin/firefox

#USER appuser:appgroup


####################
# Release image #
####################
FROM ${RUNTIME_IMAGE} AS release

# set environment variables
ENV PYTHONFAULTHANDLER=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONHASHSEED=random \
    PYTHONUNBUFFERED=1 \
    PATH=/venv/bin:$PATH \
    WORKSPACE=/opt \
    APP_PATH=/opt \
    ENV_PATH=/opt/.env

RUN apt-get update && apt-get install -y python3-dev

WORKDIR /opt

COPY --from=builder /venv /venv

ENV PATH=/venv/bin:$PATH
RUN playwright install-deps && playwright install firefox

ARG STAGE PORT VERSION

ENV VERSION=${VERSION}
ENV WORKSPACE=/opt
ENV STAGE=${STAGE}
ENV PORT=${PORT}

EXPOSE ${PORT}

COPY src/app /opt/app
COPY src/envs/${STAGE}.env /opt/.env

CMD exec gunicorn app.main:app -w 2 -k uvicorn.workers.UvicornWorker --timeout 3600 --bind :${PORT} --limit-request-line 0 --limit-request-field_size 0 --log-level debug
