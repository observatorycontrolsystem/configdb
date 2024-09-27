from cerberus import Validator


class OCSValidator(Validator):
    """ Custom validator that allows label, show(in UI), and description fields in the schema """
    def _validate_description(self, constraint, field, value):
        pass

    def _validate_label(self, constraint, field, value):
        pass
    
    def _validate_show(self, constraint, field, value):
        pass