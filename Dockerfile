FROM python:3.5

ENV DOCKERFILE_VERSION 7
ENV PYTHONBUFFERED 1
ENV APPLICATION_ROOT /lco/configdb3/

RUN apt-get update
RUN apt-get install -y build-essential git
RUN apt-get install -y nginx supervisor

RUN mkdir -p $APPLICATION_ROOT
ADD . $APPLICATION_ROOT
WORKDIR $APPLICATION_ROOT

run echo "daemon off;" >> /etc/nginx/nginx.conf
run rm /etc/nginx/sites-enabled/default
run cp docker/nginx-app.conf /etc/nginx/sites-enabled/
run cp docker/supervisor-app.conf /etc/supervisor/conf.d/
run cp docker/local_settings.py $APPLICATION_ROOT/configdb3/

RUN pip install uwsgi
RUN pip install -r requirements.txt

RUN python3 manage.py collectstatic --noinput

expose 80
cmd ["supervisord", "-n"]



