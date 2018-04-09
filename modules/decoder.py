import re
import json
import sys
import os


def decodeRegExp(operation, content, log_):
    try:
        if re.search(operation, content, re.IGNORECASE):
            response = re.search(operation, str(content), re.IGNORECASE)
            return response.group(0)
        log_.info('Nope')
    except Exception as e:
        log_.error('{0}'.format(e))
        pass


def matchJSON(structure, matchKey, method, matching, return_val, log_):
    try:
        for i in range(len(structure[method])):
            if structure[method][i][matchKey] == matching:
                if return_val == 'regExp':
                    site = structure[method][i]['site']
                    return structure['sites-regExp'][site]
                return structure[method][i][return_val]
    except Exception as e:
        log_.error('{0}'.format(e))
        pass
