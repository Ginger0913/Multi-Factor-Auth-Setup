import json
from pymemcache.client.base import Client


class clientRuler:
    def json_serializer(self, key, value):
        if type(value) == str:
            return value, 1
        return json.dumps(value), 2

    def json_deserializer(self, key, value, flags):
            if flags == 1:
                return value
            if flags == 2:
                return json.loads(value)
            raise Exception(key)

    def __init__(self, log_):
        try:
            self.log = log_
            self.client = Client(('localhost', 11211), serializer=self.json_serializer,
                deserializer=self.json_deserializer)
        except Exception as e:
            log_.error('{0}'.format(e.message))

    def setKey(self, set_key, set_value):
        try:
            self.client.delete(set_key)
            self.client.set(set_key, set_value, 900)
        except Exception as e:
            self.log.error('{0}'.format(e.message))
        
    def getKey(self, get_key):
        try:
            result = self.client.get(get_key)
            return result
        except Exception as e:
            self.log.error('{0}'.format(e.message))
            
    def deleteKey(self, delete_key):
        try:
            self.client.delete(delete_key)
        except Exception as e:
            self.log.error('{0}'.format(e.message))
