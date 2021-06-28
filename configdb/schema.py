from rest_framework.schemas.openapi import SchemaGenerator
from setuptools_scm import get_version
from setuptools_scm.version import ScmVersion

def version_scheme(version: ScmVersion) -> str:
    """ Simply return the string representation of the version object tag, which is the latest git tag.
    setuptools_scm does not provide a simple semantic versioning format without trying to guess the next release, or adding some metadata to the version.
    """
    return str(version.tag)


class ConfigDBSchemaGenerator(SchemaGenerator):
    def get_schema(self, *args, **kwargs):
        schema = super().get_schema(*args, **kwargs)
        schema['info']['title'] = 'Configuration Database'
        schema['info']['description'] = 'An application with a database that stores observatory configuration'
        # Set the version to the latest git tag, and do not append any local information to the version number
        schema['info']['version'] = get_version(version_scheme=version_scheme, local_scheme='no-local-version')
        return schema
