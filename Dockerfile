FROM python:3.6-alpine

EXPOSE 80
ENTRYPOINT [ "/init" ]
WORKDIR /lco/configdb3/

COPY requirements.txt /lco/configdb3/
RUN apk --no-cache add bash postgresql-libs \
        && apk --no-cache add --virtual .build-deps gcc postgresql-dev musl-dev \
        && pip --no-cache-dir install -r /lco/configdb3/requirements.txt \
        && apk --no-cache del .build-deps

COPY docker/ /

COPY . /lco/configdb3/

