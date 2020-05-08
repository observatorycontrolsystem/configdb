FROM python:3.6-alpine

WORKDIR /app

COPY requirements.txt .
RUN apk --no-cache add bash postgresql-libs libffi-dev make \
        && apk --no-cache add --virtual .build-deps gcc postgresql-dev musl-dev \
        && pip --no-cache-dir install -r requirements.txt \
        && apk --no-cache del .build-deps

COPY . .

CMD [ "gunicorn", "--bind=0.0.0.0:8080", "--worker-class=gevent", "--workers=4", "--access-logfile=-", "--error-logfile=-", "configdb3.wsgi:application" ]
