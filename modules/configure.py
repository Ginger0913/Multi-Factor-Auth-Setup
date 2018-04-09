from configparser import ConfigParser
import os.path as path
import json
import sys
import traceback
import modules.decoder as dec
import modules.caching as cache
from time import sleep
import eventlet
imapclient = eventlet.import_patched('imapclient')


class EmailConf:
    def __init__(self, log_, _config):
        # Retrieve IMAP host - halt script if section 'imap' or value missing
        try:
            self.host = _config['host']
        except ConfigParser.NoSectionError:
            log_.critical('no "imap" section in configuration file')
            quit()
        # Retrieve IMAP username - halt script if missing
        try:
            self.username = _config['username']
        except ConfigParser.NoOptionError:
            log_.critical('no IMAP username specified in configuration file')
            quit()
        # Retrieve IMAP password - halt script if missing
        try:
            self.password = _config['password']
        except ConfigParser.NoOptionError:
            log_.critical('no IMAP password specified in configuration file')
            quit()
        # Retrieve IMAP SSL setting - warn if missing, halt if not boolean
        try:
            self.ssl = _config['ssl']
        except ConfigParser.NoOptionError:
            # Default SSL setting to False if missing
            log_.warning('no IMAP SSL setting specified in configuration file')
            self.ssl = False
        except ValueError:
            log_.critical('IMAP SSL setting invalid - not boolean')
            quit()
        # Retrieve IMAP folder to monitor - warn if missing
        try:
            self.folder = _config['folder']
        except ConfigParser.NoOptionError:
            # Default folder to monitor to 'INBOX' if missing
            log_.warning('no IMAP folder specified in configuration file')
            self.folder = 'INBOX'
        # Retrieve path for downloads - halt if section of value missing
        try:
            self.download = _config['download']
        except ConfigParser.NoOptionError:
            # If value is None or specified path not existing, warn and default
            # to script path
            log_.warn('no download path specified in configuration')
            self.download = None
        finally:
            self.download = self.download if (
                self.download and path.exists(self.download)
            ) else path.abspath(__file__)
        log_.info('setting path for email downloads - {0}'.format(self.download))

    def process_email(self, mail_, log_):
        download = self.download
        reg_exp = ""
        client = ""
        body = ""
        if mail_.is_multipart():
            for part in mail_.walk():
                ctype = part.get_content_type()
                cdispo = str(part.get('Content-Disposition'))
                if ctype == 'text/plain' and 'attachment' not in cdispo:
                    body = part.get_payload(decode=True)
                    break
                _filename = part.get_filename()
                if _filename is not None:
                    att_path = (path.join(download, _filename))
                    if not path.isfile(att_path):
                        fp = open(att_path, 'wb')
                        fp.write(part.get_payload(decode=True))
                        fp.close()
        else:
            body = (mail_.get_payload(decode=True))  # Retrieve RegExp - halt script if missing
        try:
            with open('configuration.json') as data_file:
                data = json.load(data_file)
                receiving_email = mail_['to'].replace('<', '').replace('>', '')
                reg_exp = dec.matchJSON(data, 'username', 'email', receiving_email, 'regExp', log_)
                client = dec.matchJSON(data, 'username', 'email', receiving_email, 'client', log_)
        except Exception as e:
            log_.critical(e)
            quit()
        final_result = dec.decodeRegExp(reg_exp, body, log_)
        if final_result is None:
            log_.error('Could not find code in text')
            return '<span>Could not find code</span>'
        client_class = cache.clientRuler(log_)
        client_class.setKey(client, final_result)
        log_.info(body)
        log_.info('{0} has had a code generated for them containing {1}'.format(client, final_result))

    def connect(self, log_):
        host = self.host
        username = self.username
        password = self.password
        folder = self.folder
        ssl = self.ssl
        # Attempt connection to IMAP server
        log_.info('connecting to IMAP server - {0}'.format(host))
        try:
            imap = imapclient.IMAPClient(host, use_uid=True, ssl=ssl)
            self.imap = imap
        except Exception:
            # If connection attempt to IMAP server fails, retry
            etype, evalue = sys.exc_info()[:2]
            estr = traceback.format_exception_only(etype, evalue)
            logstr = 'failed to connect to IMAP server - '
            for each in estr:
                logstr += '{0}; '.format(each.strip('\n'))
            log_.error(logstr)
            sleep(10)
            pass
        log_.info('server connection established')
        # Attempt login to IMAP server
        log_.info('logging in to IMAP server - {0}'.format(username))
        try:
            result = imap.login(username, password)
            log_.info('login successful - {0}'.format(result))
        except Exception:
            # Stop script when login fails
            etype, evalue = sys.exc_info()[:2]
            estr = traceback.format_exception_only(etype, evalue)
            logstr = 'failed to login to IMAP server - '
            for each in estr:
                logstr += 'Username {0} -- {1}; '.format(username, each.strip('\n'))
            log_.critical(logstr)
            return False
        # Select IMAP folder to monitor
        log_.info('selecting IMAP folder - {0}'.format(folder))
        try:
            result = imap.select_folder(folder)
            log_.info('folder selected')
        except Exception:
            # Stop script when folder selection fails
            etype, evalue = sys.exc_info()[:2]
            estr = traceback.format_exception_only(etype, evalue)
            logstr = 'failed to select IMAP folder - '
            for each in estr:
                logstr += '{0}; '.format(each.strip('\n'))
            log_.critical(logstr)
            pass
        # Retrieve and process all unread messages. Should errors occur due
        # to loss of connection, attempt re-establishing connection
        try:
            result = imap.search('UNSEEN')
        except Exception:
            pass
        log_.info('{0} unread messages seen - {1}'.format(
            len(result), result
        ))
        return result

    def fetch(self, data):
        result = self.imap.fetch(data, ['RFC822'])
        return result
