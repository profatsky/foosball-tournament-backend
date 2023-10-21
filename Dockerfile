# syntax=docker/dockerfile:1.4

FROM python:3.10-slim-bullseye as builder

ENV PYTHONUNBUFFERED 1
ENV POETRY_HOME /opt/poetry
ENV VENV /opt/venv
ENV PATH $VENV/bin:$PATH
ENV PYTHONPATH /app
WORKDIR /app
SHELL [ "/bin/sh", "-eu", "-c" ]
RUN --mount=type=cache,mode=0755,target=/root/.cache \
    python -m venv $POETRY_HOME ; \
    $POETRY_HOME/bin/pip install poetry==1.4.2 wheel==0.38.4 ; \
    ln -s $POETRY_HOME/bin/poetry /usr/bin/poetry
COPY --link poetry.lock pyproject.toml /app/
RUN --mount=type=cache,mode=0755,target=/root/.cache \
    poetry config virtualenvs.create false ; \
    python -m venv $VENV ; \
    . $VENV/bin/activate ; \
    poetry install --no-interaction --no-ansi --no-root
SHELL [ "/bin/sh", "-c" ]


FROM python:3.10-slim-bullseye
ENV PYTHONUNBUFFERED 1
ENV VENV /opt/venv
ENV PATH $VENV/bin:$PATH
ENV PYTHONPATH /app
WORKDIR /app
COPY --link --from=builder $VENV $VENV
COPY --link --from=builder . .
