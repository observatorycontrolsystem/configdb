FROM python:3.10-alpine

# install system dependencies
RUN apk --no-cache add bash postgresql-libs libffi-dev make \
        && apk --no-cache add --virtual .build-deps gcc g++ postgresql-dev musl-dev git

# use bash
SHELL ["/bin/bash", "-c"]

# upgrade pip and install poetry
RUN pip install --upgrade pip && pip install poetry

WORKDIR /app

# copy bare minimum needed to install python dependecies with poetry
COPY ./README.md ./pyproject.toml ./poetry.lock ./

# install locked python dependecies using poetry to generate a requirements.txt
RUN pip install -r <(poetry export --without-hashes) # TODO: remove --without-hashes once not using git

# copy everything else
COPY ./ ./

# install our app
RUN pip install .

# free up some space
RUN apk --no-cache del .build-deps

# Docker friendly env vars for Python
ENV PYTHONUNBUFFERED=1 PYTHONFAULTHANDLER=1

CMD [ "gunicorn", "--bind=0.0.0.0:8080", "--worker-class=gevent", "--workers=4", "--access-logfile=-", "--error-logfile=-", "configdb.wsgi:application" ]

EXPOSE 8080/tcp
