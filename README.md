# MFA-Service

Micro-Service for accepting multiple inputs of data for mult-factor authentication

## Getting Started

These instructions will get you a copy of the project up and running on your local machine for development and testing purposes.

### Prerequisites

What things you need to install the software and how to install them

* [ModWSGI](http://modwsgi.readthedocs.io/en/develop/) - The apache service used - apt-get install libapache2-mod-wsgi
* [Memcache](https://memcached.org) - Used to store key-values - apt-get install libmemcached-dev

You will need mod_wsgi set up first so that the server can be set reached.

The following is an example of the apache conf for the mod_wsgi

```
<VirtualHost *:80>
    ServerName mfa.com
     WSGIDaemonProcess mfa user=www-data group=www-data processes=1 threads=5
     WSGIScriptAlias / /var/www/mfa/mobile.wsgi

     <Directory /var/www/mfa>
         WSGIProcessGroup mfa
         WSGIApplicationGroup %{GLOBAL}
         Require all granted
     </Directory>
     ServerAdmin webmaster@mfa.com
     ErrorLog ${APACHE_LOG_DIR}/error.log
     CustomLog $_APACHE_LOG_DIR/access.log combined
</VirtualHost>
```

These python modules will also need to be installed

* [Bottle](https://bottlepy.org/docs/dev/) - Routing and endpoint - apt-get install python-bottle
* [PyMemCache](https://pymemcache.readthedocs.io/en/latest/) - python wrapper for memcached - pip install pymemcache
* [eventlet] pip install eventlet
* [imapclient] pip install imapclient
* [setuptools] pip install setuptools
* [libffi-dev] apt-get install libffi-dev
* [libffi6] apt-get install libffi6
* [cryptography] pip install cryptography
* [configparser] pip install configparser

Then enable the SWGI module and restart Apache.

```
a2enmod wsgi
service apache restart
```


## Running the tests

To run the tests you will first need to set up the json file, which is currently called "configuration.json"

This is a test stucture for the json

```
{
    "email": [
        {
            "site": "test1",
            "client": "1234",
            "username": "test1@test.com",
            "password": "password"
        },
        {
            "site": "test2",
            "client": "1235",
            "username": "test2@test.com",
            "password": "password"
        },
    ],
    "phone": [
        {
            "site": "test3",
            "client": "1236",
            "number": "7271231234"
        }
    ],
    "sites-regExp": {
        "test1": "test1Regexp",
        "test2": "test2Regexp",
        "test3": "test2Regexp"
    },
    "config": {
        "host": "imap.gmail.com",
        "ssl": "True",
        "folder": "INBOX",
        "download": "download/location",
        "waitTimeout": 15
    }
}
```

You can start the email monitor by simply starting the email_mon.py

The mobile MFA is operated via enpoints and shouldn't need much monitoring once graylog is set up to replace manual log

### Break down into end to end tests

The email monitor loops through all emails and and checks for new/unread emails, marks them as read and then saves them into memory using the clientID as the key

The mobile monitor just accepts the input and sets up the key based off of that

## Authors

* **Cody Fidler** - *Initial work* - [Cody](https://github.com/Ginger0913)
