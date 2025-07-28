# Observatory Configuration

![Build](https://github.com/observatorycontrolsystem/configdb/workflows/Build/badge.svg)
[![Coverage Status](https://coveralls.io/repos/github/observatorycontrolsystem/configdb/badge.svg)](https://coveralls.io/github/observatorycontrolsystem/configdb)
[![Codacy Badge](https://app.codacy.com/project/badge/Grade/dda63ab6370247a68aa78e0e186f819d)](https://www.codacy.com/gh/observatorycontrolsystem/configdb?utm_source=github.com&amp;utm_medium=referral&amp;utm_content=observatorycontrolsystem/configdb&amp;utm_campaign=Badge_Grade)

Observatory Configuration Database is a simple frontend to a relational database where we attempt to
represent the physical state of a Telescope Network. It provides a
RESTful API as well as HTML views of the data. This is used by other applications in the observatory control system to understand what components make up the observatory, and to allow for automated validation of component properties.

## Prerequisites
-   Python>=3.7
-   PostgreSQL >= 10

The application requires a PostgreSQL database backend because it uses JSONFields in the model.

## Configuration

This project is configured using environment variables.

| Variable              | Description                                                                        | Default                         |
| --------------------- | ---------------------------------------------------------------------------------- | ------------------------------- |
| `SECRET_KEY`          | Django Secret Key, this value must be set to run the app                           | `None`                          |
| `DEBUG`               | Enable Django debugging features, set to `True` for local development              | `False`                         |
| `DB_ENGINE`           | Database Engine, set to `django.db.backends.postgresql` to use PostgreSQL          | `django.db.backends.postgresql` |
| `DB_NAME`             | Database Name                                                                      | `configdb`                      |
| `DB_HOST`             | Database Hostname, set this when using PostgreSQL                                  | `127.0.0.1`                     |
| `DB_USER`             | Database Username, set this when using PostgreSQL                                  | `postgres`                      |
| `DB_PASS`             | Database Password, set this when using PostgreSQL                                  | `postgres`                      |
| `DB_PORT`             | Database Port, set this when using PostgreSQL                                      | `5432`                          |
| `OAUTH_CLIENT_ID`     | OAuth2 application client_id, set this to use OAuth2 authentication                | `""`                            |
| `OAUTH_CLIENT_SECRET` | OAuth2 application client_secret, set this to use OAuth2 authentication            | `""`                            |
| `OAUTH_TOKEN_URL`     | OAuth2 token URL, set this to use OAuth2 authentication                            | `""`                            |
| `OAUTH_PROFILE_URL`   | Observation portal profile endpoint, used to retrieve details on user accounts     | `""`                            |
| `OAUTH_SERVER_KEY`    | Observation portal server secret key to authenticate calls from the server         | `""`                            |
| `HEROIC_API_URL`    | HEROIC server api url, required for submitting your observatory updates to the HEROIC service         | `""`                            |
| `HEROIC_API_TOKEN`    | HEROIC server api token, required for submitting your observatory updates to the HEROIC service         | `""`                            |
| `HEROIC_OBSERVATORY`    | HEROIC server observatory code, required for submitting your observatory updates to the HEROIC service         | `""`                            |
| `HEROIC_EXCLUDE_SITES`    | Comma delimited list of site codes to ignore when sending updates to HEROIC         | `""`                            |
| `HEROIC_EXCLUDE_TELESCOPES`    | Comma delimited list of site.enclosure.telescope codes to ignore when sending updates to HEROIC      | `""`                            |

## Local Development

### **Poetry**

We use Poetry for package management. If you already have Poetry installed, you
can skip this section.

You can install Poetry using one of the many options listed at https://python-poetry.org/docs/#installation.
One simple option is using Pipx:

    python3 -m pip install --user pipx
    python3 -m pipx ensurepath
    pipx install poetry

### **Install**

Install the project and its Python dependencies:

    poetry install

This will install the project in a Poetry managed virtual environment. To run
commands in that environment either use `poetry run ...` or start a shell in
that environment with `poetry shell`


### **Set up the database**

This application requires the use of a PostgreSQL database (or another database that supports JSONField in Django). If using PostgreSQL, the following command uses the [PostgreSQL Docker image](https://hub.docker.com/_/postgres) to
create a test PostgreSQL database. Make sure that the options that you use to set up your database correspond with your configured database setting environment variables.

    docker run --name configdb-postgres -e POSTGRES_PASSWORD=postgres -e POSTGRES_DB=configdb -v/var/lib/postgresql/data -p5432:5432 -d postgres:11.1

After creating the database, migrations must be applied to set up the tables in the database.

    poetry run python manage.py migrate

### **Run the tests**

    poetry run python manage.py test

### **Run the configdb**

    poetry run python manage.py runserver

The configdb should now be accessible from <http://127.0.0.1:8000>!

### Authentication
The application connects to a running Observation Portal for OAuth2 authentication. Staff accounts should have
access to the admin interface. Remember to set the appropriate environment variables - the token url
will be the `/o/token/` endpoint of the Observation Portal you are connecting to.

If no Observation Portal is connected during development, creating a local superuser account should work to
access the admin interface as well:

    poetry run python manage.py createsuperuser

### Filling in Observatory Data
The admin interface is used to define the components of the Observatory. It is accessible by going to <http://127.0.0.1:8000/admin/>. The different components of the Observatory should be defined one-by-one, and will often reference each other when creating them. A sensible order to initially create the components of an Observatory is:

1. Site - The geographic location with one or more enclosures
2. Enclosure - A physical building containing one or more telescopes
3. Telescope - A single light collection system
4. Camera type - The generic properties of a single type of camera
5. Optical element - A single component within the optical path of a camera
6. Optical element group - A logical grouping of one or more optical elements of a single type that can be selected on a camera
7. Camera - A specific instance of a camera type with a set of optical element groups
8. Generic modes - A generic definition for a single mode, including an associated overhead and validation schema
9. Generic mode group - A grouping of one or more generic modes of a single type associated with a camera type. The type is user definable, but some examples used in the Observation Portal include `readout`, `acquisition`, `guiding`, `exposure`, and `rotator`
10. Instrument Category - Generic category of instruments. Usually used to differentiate `IMAGE` or `SPECTRA` in the OCS, but you are free to define additional categories and use them differently
11. Configuration Types - Generic types defining the configurations available on your telescope, i.e. `EXPOSE`, `BIAS`, `FLAT`, etc.
12. Instrument Type - The generic properties of a single type of instrument
13. Configuration Type Properties - Links a configuration type to an instrument type with additional settings specific to it
14. Instrument - A specific instance of an instrument type with a combination of one or more science cameras and a guide camera on a specific Telescope

-   Check out the updated step-by-step setup guide [here](https://observatorycontrolsystem.github.io/deployment/configdb_setup/)
-   It is recommended that all codes use lowercase characters by convention, except for type codes such as instrument type, camera type, and mode type which should use all upper case. While this convention isn't strictly required, it is useful to choose a convention and apply it consistently when defining your codes.


#### Notes on using the API to write
The API has recently been updated so all data structures should now be writable. Due to the heavily nested structure of the data, it is still highly recommended to write the data structures in the order defined above. There are a few api differencies when writing some structures, including:

1. Optical Element Groups - Can either link existing Optical Elements or create them itself. Set `optical_element_ids` to a list of existing Optical Element ids, or set the `optical_elements` field to a list of objects containing at least the optical elements `code` and `name` field, which will either match an existing optical element by `code` or create a new one. The `default` field should be populated with the code of an existing optical element. If the optical element doesn't exist yet, you must patch the group after creation to add the default.
2. Generic Mode Groups - Can either link existing Generic Modes or create them itself. Set `mode_ids` to a list of existing Generic Mode ids, or set the `modes` field to a list of objects containing at least the mode `code` and `name` field, which will either match an existing generic mode by `code` or create a new one. The `default` field should be populated with the code of an existing generic mode. If the generic mode doesn't exist yet, you must patch the group after creation to add the default.
3. Instrument Types - When setting or updating the configuration type properties associated with an Instrument Type, you must first have the Configuration Types created in advance. Then you can send `configuration_types` on creation that contain a list of objects with configuration type property settings and the `configuration_type` field which is the code of the configuration type you want to link. You can alternatively use the configuration type properties API to create those individually, referencing the corresponding configuration type code and instrument type id.


#### Generic Mode Validation Schema
GenericMode structures have a field called `validation_schema` which accepts a dictionary [Cerberus Validation Schema](https://docs.python-cerberus.org/en/stable/schemas.html). This validation schema will be used to provide automatic validation and setting of defaults within the [Observation Portal](https://github.com/observatorycontrolsystem/observation-portal). The validation schema will act on the structure in which the GenericMode is a part of. For example:

| Mode type   | What structure validation applies to |
| ----------- | ------------------------------------ |
| readout     | InstrumentConfig                     |
| exposure    | InstrumentConfig                     |
| rotator     | InstrumentConfig                     |
| acquisition | AcquisitionConfig                    |
| guiding     | GuidingConfig                        |

## Example queries
Every component has an endpoint to query, but to get the entire structure of the Observatory, it is common to query the sites endpoint and parse the data from within your client application.

Return all observatory configuration information

    GET /sites/

Return a specific camera's configuration

    GET /cameras/?code=my_camera_code

Return all instruments that are in the SCHEDULABLE state

    GET /instruments/?state=SCHEDULABLE

## Sending data to HEROIC

HEROIC is a service provided by Scimma through the NSF that accepts and stores observatory information, including instrument configuration and telescope status. By default, no data will be sent to the HEROIC service. If you want to send your observatory updates to HEROIC, you must set all the `HEROIC_*` environment variables. You must login to the HEROIC server, retrieve your API token, and request that an Observatory is created for you with your account as the admin for that observatory. Afterwards, by setting the appropriate environment variables your configuration database should automatically send updates to HEROIC when updates are made through the API or admin interface.
