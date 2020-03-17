FROM python:3.8

RUN pip --no-cache-dir install -U pip \
    && pip --no-cache-dir install private-pypi==0.1.0a0

ENTRYPOINT ["private_pypi"]
