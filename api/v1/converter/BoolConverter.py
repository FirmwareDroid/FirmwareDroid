from werkzeug.routing import BaseConverter


class BoolConverter(BaseConverter):
    """
    Converter class for "bool"
    """

    def to_python(self, value):
        return True if value == "true" or value == "True" else False
