FROM debian:buster-slim AS build
RUN apt-get update && \
    apt-get install --no-install-suggests --no-install-recommends --yes python3-venv gcc libpython3-dev curl && \
    python3 -m venv /venv && \
    /venv/bin/pip install --upgrade pip


FROM build AS build-venv

ARG PYWHARF_PKG_REPO_NAME
ARG PYWHARF_PKG_REPO_TOKEN_NAME
ARG PYWHARF_SERVER_PORT

ADD dist /dist
RUN PIP_INDEX_URL="http://${PYWHARF_PKG_REPO_NAME}:$(curl http://localhost:9999/get/${PYWHARF_PKG_REPO_TOKEN_NAME})@localhost:${PYWHARF_SERVER_PORT}/simple" \
    /venv/bin/pip install --disable-pip-version-check $(realpath /dist/pywharf*.whl | head -n 1)


FROM gcr.io/distroless/python3-debian10
COPY --from=build-venv /venv /venv
ENV PATH /venv/bin:$PATH
ENTRYPOINT ["pywharf"]
