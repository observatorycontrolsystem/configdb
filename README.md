ConfigDB3
=========

Configdb3 is a simple frontend to a relational database
where we attempt to represent the physical state of the
network. It provides a RESTful API as well as html
views of the data. It also generates a camera_mappings
file.

Applications that need to know which cameras are where,
what filters they have available, on what telescope, etc
should query this api.

Configdb3 is currently being served at
[configdb.lco.gtn](http://configdb.lco.gtn)

Development Server
------------------

`git clone ssh://git@git.lco.gtn:7999/ws/configdb3.git`
`cd configdb3 && docker-compose up`

This will start a django development server and a postgresql
database. However, the application uses sqlite3 by default.
If you want to use postgresql instead (recommended) override
the DATABASES setting using a `local_settings.py` file
in the `configdb3/` directory:


    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql_psycopg2',
            'NAME': 'configdb3',
            'USER': 'postgres',
            'PASSWORD': 'postgres',
            'HOST': 'db',
            'PORT': ''
        },
    }

Deployment
----------
To deploy configdb3, build the configdb3 docker image and push:

    docker build -f Dockerfile.prod -t docker.lcogt.net/configdb3:latest .
    docker push docker.lcogt.net/configdb3:latest

Then on the docker host:

    docker pull docker.lcogt.net/configdb3:latest
    cd configdb3-deploy
    docker-compose stop && docker-compose rm
    docker-compose up -d

Note building the image **will fail** if there is no local_settings.py file located at `configdb3-deploy/local_settings.py`. Use the one included in the current image as a guide.

