FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /code

COPY pyproject.toml poetry.lock /code/

RUN pip install poetry
RUN poetry config virtualenvs.create false
RUN poetry install --no-dev

RUN apt-get update && \
    apt-get install -y postgresql-client && \
    rm -rf /var/lib/apt/lists/*

COPY . /code

COPY entrypoint.sh /code/entrypoint.sh
RUN chmod +x /code/entrypoint.sh
CMD ["/code/entrypoint.sh"]
