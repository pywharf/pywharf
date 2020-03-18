FROM python:3.8

ADD dist /dist

RUN pip --no-cache-dir install -U pip \
    && pip --no-cache-dir install $(realpath /dist/private_pypi*.whl | head -n 1)

ENTRYPOINT ["private_pypi"]
