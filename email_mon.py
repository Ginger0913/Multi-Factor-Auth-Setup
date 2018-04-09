import sys
from datetime import datetime, time

import json
import email
import logging
from logging.handlers import RotatingFileHandler
from modules.configure import EmailConf


# Setup the log handlers to stdout and file.
log = logging.getLogger('imap_monitor')
log.setLevel(logging.DEBUG)
formatter = logging.Formatter(
    '%(asctime)s | %(name)s | %(levelname)s | %(message)s'
    )
handler_stdout = logging.StreamHandler(sys.stdout)
handler_stdout.setLevel(logging.DEBUG)
handler_stdout.setFormatter(formatter)
log.addHandler(handler_stdout)
handler_file = RotatingFileHandler(
    'imap_monitor.log',
    mode='a',
    maxBytes=1048576,
    backupCount=9,
    encoding='UTF-8',
    delay=True
    )
handler_file.setLevel(logging.DEBUG)
handler_file.setFormatter(formatter)
log.addHandler(handler_file)

def main():
    log.info('... script started')
    data = {}
    # Read config file - halt script on failure
    try:
        with open('configuration.json') as data_file:
            data = json.load(data_file)
    except:
        log.critical('{0}'.format(sys.exc_info()[0]()))
        quit()
    con = EmailConf(log, data["config"])
    # End of configuration section --->
    while True:
        result = con.connect(log)
        if result:
            for each in result:
                try:
                    new_result = con.fetch(each)
                except Exception as e:
                    log.error(e)
                    log.error('failed to fetch email - {0}'.format(each))
                    continue
                new_result = dict(new_result[each])
                mail = email.message_from_string(new_result.get('RFC822'))
                try:
                    con.process_email(mail, log)
                    log.info('processing email {0} - {1}'.format(
                        each, mail['subject']
                        ))
                except Exception:
                    log.error('failed to process email {0}'.format(each))
                    continue
        # End of IMAP server connection loop --->

if __name__ == '__main__':
    main()
