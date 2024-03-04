FROM python:3.9-slim

RUN mkdir /db-client
WORKDIR /db-client

RUN apt update && \
    apt install -y postgresql-client curl git \
    && rm -rf /var/lib/apt/lists/*

# Install pip and poetry
RUN pip install --no-cache --upgrade pip
RUN pip install --no-cache "poetry==1.3.2"

# Create layer for dependencies
# TODO: refine this as part of CI & test updates
COPY poetry.lock pyproject.toml ./
# Create a requirements file so we can install with minimal caching
# See: https://github.com/python-poetry/poetry-plugin-export
RUN poetry export --with dev \
    | grep -v '\--hash' \
    | grep -v '^torch' \
    | grep -v '^triton' \
    | grep -v '^nvidia' \
    | sed -e 's/ \\$//' \
    | sed -e 's/^[[:alpha:]]\+\[\([[:alpha:]]\+\[[[:alpha:]]\+\]\)\]/\1/' \
    > requirements.txt

# Install application requirements
RUN pip3 install --no-cache -r requirements.txt

# Copy files to image
COPY db_client/alembic.ini ./alembic.ini
COPY db_client/alembic ./alembic
COPY db_client ./db_client
COPY tests ./tests
COPY LICENSE .
COPY README.md .

# ENV
ENV PYTHONPATH=/db-client
CMD ["pytest", "--test-alembic", "-vvv", "--cov=db_client", "--cov-fail-under=80"]
