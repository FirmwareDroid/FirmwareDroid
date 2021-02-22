import json
import logging
from bson import ObjectId
from mongoengine.base import LazyReference


class DefaultJsonEncoder(json.JSONEncoder):
    """
    JSON Encoder for mongoDB objectID.
    """
    def default(self, obj):
        if isinstance(obj, ObjectId):
            return str(obj)
        if isinstance(obj, set):
            return list(obj)
        if isinstance(obj, LazyReference):
            return str(obj.pk)
        logging.info(f"type: {type(obj)}")
        return json.JSONEncoder.default(self, obj)
