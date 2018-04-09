import sys
import logging
from logging.handlers import RotatingFileHandler
from datetime import datetime, time
import os
import bottle
import json

os.chdir(os.path.dirname(__file__))
sys.path.append(os.path.dirname(__file__))
try:
	# Setup the log handlers to stdout and file.
	log = logging.getLogger('mobile_monitor')
	log.setLevel(logging.DEBUG)
	formatter = logging.Formatter(
		'%(asctime)s | %(name)s | %(levelname)s | %(message)s'
		)
	handler_stdout = logging.StreamHandler(sys.stdout)
	handler_stdout.setLevel(logging.DEBUG)
	handler_stdout.setFormatter(formatter)
	log.addHandler(handler_stdout)
	handler_file = RotatingFileHandler(
		'mobile_monitor.log',
		mode='a',
		maxBytes=1048576,
		backupCount=9,
		encoding='UTF-8',
		delay=True
		)
	handler_file.setLevel(logging.DEBUG)
	handler_file.setFormatter(formatter)
	log.addHandler(handler_file)
except Exception as e:
	bottle.redirect('/error/{0}'.format(e.message))


def RepresentsInt(s):
	try:
		int(s)
		phone_length = len(s)
		if (phone_length < 8):
			return False
		return True
	except ValueError:
		return False


from modules import decoder as dec
from modules import caching as cache
	

@bottle.route('/<phone_num>')
def index(phone_num):
	api_key = None
	mfa_code = None
	phone_number = None
	
	if 'api_key' in bottle.request.query:
		api_key = bottle.request.query.api_key
	if 'Body' in bottle.request.query:
		mfa_code = bottle.request.query.Body
	if 'From' in bottle.request.query:
		phone_number = bottle.request.query['From']
	ip_address = bottle.request.environ.get('HTTP_X_FORWARDED_FOR') or bottle.request.environ.get('REMOTE_ADDR')
	
	if not api_key or not mfa_code or not phone_num:
		log.error('No parameters passed - {0}. The following parameters were given: {1}'.format(ip_address,str(', '.join([str(x) for x in bottle.request.query]))))
		return ('<sms>You keep navigating to this page. I do not think it means what you think it means.</sms>')
	if api_key != 'a749881d-5205-4d22-8602-f879064f52ca':
		log.error('API key did not match - {0}'.format(ip_address))
		return bottle.template('<sms>My name is Indigo Montoya, you entered in the wrong api key... prepare to die.</sms><br><sms>Your IP:{{ip_address}}has been logged</sms>', ip_address=str(ip_address))
	if not RepresentsInt(phone_num):
		log.error('No valid phone number - {0}'.format(ip_address))
		return ('<sms>Please enter a valid number.</sms>')

	try:
		with open('configuration.json') as data_file:
			data = json.load(data_file)
	except Exception as e:
		log.critical('{0}'.format(e.message))
		return ('<sms>Can not read data: {0}</sms>'.format(e.message))
	regExp = dec.matchJSON(data, 'number','phone', phone_num, 'regExp', log)
	
	if regExp is None:
		log.error('No valid regexp for provided info')
		return ('<sms>There appears to be some missing data</sms>')
		
	client = dec.matchJSON(data, 'number', 'phone', phone_num, 'client', log)
	if client is None:
		log.error('Could not match to clientID {0}'.format(client))
		return bottle.template('<sms>Could not match client {{client}}</sms>', client = str(client))
		
	finalResult = dec.decodeRegExp(regExp, mfa_code, log)
	if finalResult is None:
		log.error('could not find code in {0} using {1}'.format(mfa_code, regExp))
		return bottle.template('<sms>could not find code in {{mfa}} using {{reg}}</sms>', mfa = str(mfa_code), reg=regExp)
		
	clientClass = cache.clientRuler(log)
	clientClass.setKey(client, finalResult)
	return bottle.template('<sms>Succesfully inserted code: {{mfa_code}} from {{phone_number}}. Thank you!</sms>', mfa_code=str(finalResult), phone_number=str(phone_num))
	
	
@bottle.route('/retrieve')
def retrieveCase():
	client_id = bottle.request.query.client_id
	passedMethod = bottle.request.query.method
	ip_address = bottle.request.environ.get('HTTP_X_FORWARDED_FOR') or bottle.request.environ.get('REMOTE_ADDR')
	if passedMethod not in ["phone", "email"]:
		log.error('No valid phone number - {0}'.format(ip_address))
		return ('<span>Please enter a valid method.</span>')
	clientClass = cache.clientRuler(log)
	keyRetrieved = clientClass.getKey(client_id)
	if keyRetrieved is None:
		log.error('No code found')
		return bottle.template('<span>There was an error retrieving your code for clientID {{client}}</span>',client=client_id)
	log.info('{0} is your mfa key'.format(keyRetrieved))
	return bottle.template('{{mfa}}',mfa=str(json.dumps({'mfa_code': keyRetrieved})))
	
	
@bottle.route('/delete')
def retrieveCase():
	client_id = bottle.request.query.client_id
	passedMethod = bottle.request.query.method
	ip_address = bottle.request.environ.get('HTTP_X_FORWARDED_FOR') or bottle.request.environ.get('REMOTE_ADDR')

	if passedMethod not in ["phone", "email"]:
		log.error('No valid phone number - {0}'.format(ip_address))
		return ('<span>Please enter a valid method.</span>')
	clientClass = cache.clientRuler(log)
	clientClass.deleteKey(client_id)
	log.info('{0} has been removed'.format(client_id))
	return bottle.template('<span id="mfa_code">{{client}} has been removed</span>',client=str(client_id))

	
@bottle.error(404)
def error404(error):
	return 'Inconceivable!'
	
	
@bottle.route('/error/<errorpassed>')
def generalError(errorpassed):
	return bottle.template('<span>{{error_made}}</span>',error_made=errorpassed)

application = bottle.default_app()
