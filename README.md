# ConfigDB3

Configdb3 is a simple frontend to a relational database where we attempt to
represent the physical state of the LCO Telescope Network. It provides a
RESTful API as well as HTML views of the data. It also generates a
`camera_mappings` file for use by older applications.

Applications that need to know which cameras are where, what filters they have
available, on what telescope, etc. should query this API.

Configdb3 is currently being served at
[configdb.lco.gtn](http://configdb.lco.gtn)

## Getting Started

These instructions will get you a copy of this project up and running on your
local machine for development and testing purposes. See the Deployment section
for instructions on how to deploy the project on a production system.

### Prerequisites

* Python 3.6
* PostgreSQL server
* Familiarity with the [Django](https://www.djangoproject.com/) web development framework

### Development Environment

Configure your development environment credentials

    export SECRET_KEY="changeme"
    export DEBUG="true"
    export DB_HOST="$(hostname --fqdn)"
    export DB_NAME="configdb3"
    export DB_USER="configdb3"
    export DB_PASS="configdb3"

Configure a PostgreSQL database with a set of credentials for your development
environment

    docker run -d --name=postgres \
        -e POSTGRES_USER="$DB_USER" \
        -e POSTGRES_PASSWORD="$DB_PASS" \
        -e POSTGRES_DB="$DB_NAME" \
        -p 5432:5432 \
        postgres:10-alpine

Create a Python virtual environment

    python3.6 -m venv env

Activate the Python virtual environment

    source env/bin/activate

Install required Python dependencies into the virtual environment

    pip install -r requirements.txt

Run initial database setup

    python manage.py migrate

Start the development server on port 8000

    python manage.py runserver 8000

Now you can connect to your development environment at

    http://127.0.0.1:8000/

## Build

This project is built automatically by the [LCO Jenkins Server](http://jenkins.lco.gtn/).
Please see the [Jenkinsfile](Jenkinsfile) for details.

## Production Deployment

This project is deployed in the LCO Kubernetes Cluster. Please see the
[LCO Helm Charts Repository](https://github.com/LCOGT/helm-charts) for details
about the production deployment.

## Configuration

This project is configured using environment variables. This is done so that it
is very easy to use different configurations in different environments (such as
development vs. production environments).

- **`SECRET_KEY`** - Django secret key (no default is provided)
- **`DEBUG`** - Enable Django debugging features (default: `false`)
- **`DB_ENGINE`** - Database Engine (default: `django.db.backends.postgresql_psycopg2`)
- **`DB_HOST`** - Database hostname (default: `127.0.0.1`)
- **`DB_NAME`** - Database name (default: `configdb3`)
- **`DB_USER`** - Database username (default: `postgres`)
- **`DB_PASS`** - Database password (default: `postgres`)
- **`DB_PORT`** - Database port number (default: `5432`)
- **`OAUTH_CLIENT_ID`** - ???
- **`OAUTH_CLIENT_SECRET`** - ???
- **`OAUTH_TOKEN_URL`** - ???

## License

This project is licensed under the GNU GPL v3 License - see the
[LICENSE.txt](LICENSE.txt) file for details.
