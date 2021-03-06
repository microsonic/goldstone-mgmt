# syntax=docker/dockerfile:experimental

ARG GS_MGMT_BUILDER_IMAGE=docker.io/microsonic/gs-mgmt-builder:latest
ARG GS_MGMT_BASE=docker.io/microsonic/gs-mgmt:latest

FROM $GS_MGMT_BUILDER_IMAGE as builder

ARG http_proxy
ARG https_proxy

FROM $GS_MGMT_BASE

RUN --mount=type=bind,source=sm/sonic-py-swsssdk,target=/src,rw pip install /src

RUN --mount=type=bind,source=src/south/sonic,target=/src,rw pip install /src

# vim:filetype=dockerfile
