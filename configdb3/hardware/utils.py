import string


class NAFormatter(string.Formatter):
    '''
    This formatter is used by the dynamic camera camera_mappings
    file to print NA instead of None when we have missing
    values
    '''
    def __init__(self, missing='NA', bad_fmt='!!'):
        self.missing, self.bad_fmt = missing, bad_fmt

    def get_field(self, field_name, args, kwargs):
        try:
            return super().get_field(field_name, args, kwargs)
        except (KeyError, AttributeError):
            return None, field_name

    def format_field(self, value, spec):
        if value is None:
            return self.missing
        else:
            return super().format_field(value, spec)
