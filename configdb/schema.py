from rest_framework.schemas.openapi import SchemaGenerator

class ConfigDBSchemaGenerator(SchemaGenerator):
    def get_schema(self, *args, **kwargs):
        schema = super().get_schema(*args, **kwargs)
        schema['info']['title'] = 'Configuration Database'
        schema['info']['description'] = 'Observatory Configuration Database is a simple frontend to a relational ' \
                                        'database where we attempt to represent the physical state of a Telescope Network. It provides a RESTful API as well as HTML views of the data. ' \
                                        'This is used by other applications in the observatory control system to understand what components make up the observatory, ' \
                                        'and to allow for automated validation of component properties.' \
                                        'This API documentation outlines the RESTful access, creation and modification of the components of the Configuration Database.'

        # REST API schema version is decoupled from the Application version
        schema['info']['version'] = "2.1.1"
        return schema
