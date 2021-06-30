from rest_framework.schemas.openapi import SchemaGenerator
from setuptools_scm import get_version
from setuptools_scm.version import ScmVersion

def version_scheme(version: ScmVersion) -> str:
    """Simply return the string representation of the version object tag, which is the latest git tag.

    setuptools_scm does not provide a simple semantic versioning format without trying to guess the next release, or adding some metadata to the version.
    """
    return str(version.tag)


class ConfigDBSchemaGenerator(SchemaGenerator):
    def get_schema(self, *args, **kwargs):
        schema = super().get_schema(*args, **kwargs)
        schema['info']['title'] = 'Configuration Database'
        schema['info']['description'] = 'Observatory Configuration Database is a simple frontend to a relational ' \
                                        'database where we attempt to represent the physical state of a Telescope Network. It provides a RESTful API as well as HTML views of the data. ' \
                                        'This is used by other applications in the observatory control system to understand what components make up the observatory, ' \
                                        'and to allow for automated validation of component properties.' \
                                        'This API documentation outlines the RESTful access, creation and modification of the components of the Configuration Database.'
        # Set the version to the latest git tag, and do not append any local information to the version number
        schema['info']['version'] = get_version(version_scheme=version_scheme, local_scheme='no-local-version')
        return schema
