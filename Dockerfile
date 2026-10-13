# Reference build; deployment image digest MUST be pinned/approved separately.
ARG PYTHON_BASE_IMAGE
FROM ${PYTHON_BASE_IMAGE}
# CI/production MUST supply a reviewed image digest as build arg.
WORKDIR /opt/emr
COPY . /opt/emr
RUN python -m pip install --disable-pip-version-check --require-hashes --only-binary=:all: -r requirements/ci-py312-linux.lock && \
    python -m pip install --disable-pip-version-check --no-deps --no-build-isolation .
USER 65532:65532
CMD ["python", "-m", "emr.services.g6_service"]
