#!/usr/bin/env python3

import udi_interface
import sys
import time
import subprocess
import http.client
import urllib
import requests

LOGGER = udi_interface.LOGGER
          
ACTION = ['-',
	  'On',
	  'Off',
	  'Light on',
	  'Light off',
	  'Open',
	  'Closed',
	  'Locked',
	  'Unlocked',
	  'Lock jammed',
	  'Motion detected',
	  'Water leak',
	  'Rang',
	  'At home',
	  'Away',
	  'Offline',
	  'Low battery',
	  'Armed',
	  'Disarmed',
	  'Triggered',
	  'Don''t forget!',
	  'WARNING',
	  'EMERGENCY',
	  'Heat warning',
	  'Cold warning',
	  'Reset'
         ] 

class Controller(udi_interface.Node):
    def __init__(self, polyglot, primary, address, name):
        super(Controller, self).__init__(polyglot, primary, address, name)
        self.poly = polyglot
        self.name = name
        self.api_key = 'none'
        self.user_key = 'none'
        self.d_read = False

        polyglot.subscribe(polyglot.START, self.start, address)
        polyglot.subscribe(polyglot.CUSTOMPARAMS, self.parameterHandler)

        polyglot.ready()
        polyglot.addNode(self, conn_status = "ST")
        
    def start(self):
        LOGGER.info('Started Push Node Server')
        self.poly.updateProfile()
        self.poly.setCustomParamsDoc()
        
    def query(self):
        self.reportDrivers()

    def delete(self):
        LOGGER.info('Deleting the Push Node Server.')

    def stop(self):
        LOGGER.debug('Node Server stopped.')

    def parameterHandler(self, params):
        valid = True

        if 'api_key' in params and params['api_key'] != '':
            self.api_key = params['api_key']               
        else:
            self.poly.Notices['api'] = 'Please enter your Pushover API token'
            valid = False

        if 'user_key' in params and params['user_key'] != '':
            self.user_key = params['user_key']               
        else:
            self.poly.Notices['user'] = 'Please enter your Pushover user key'
            valid = False

        if 'disclaimer_read' in params and params['disclaimer_read'] != '':
            self.d_read = params['disclaimer_read']
        
        for key in params:
            _key = key.lower()
            if _key == 'api_key' or _key == 'user_key' or _key == 'disclaimer_read': # should parse out the keys, all others will be node
                continue
            else:
                _val = params[key].lower()
                _cleanaddress = _val.replace(' ','')
                _address = (_cleanaddress[:12] + _cleanaddress[-2:])
                _key = key
                if not self.poly.getNode(_address):
                    self.poly.addNode(thingnode(self.poly, self.address, _address, _key))
		
        if not self.d_read:
            self.poly.Notices['dis'] = 'Please read the Disclaimer <a target="_blank" href="https://github.com/UniversalDevicesInc-PG3/udi-push-poly/blob/master/Disclaimer.md">here</a> to remove this notice.'


    id = 'controller'
    commands = {
    }

    drivers = [{'driver': 'ST', 'value': 0, 'uom': 25}]


    
class thingnode(udi_interface.Node):

    def __init__(self, polyglot, primary, address, name):
        super(thingnode, self).__init__(polyglot, primary, address, name)
        self.title = str(name)
        self.poly = polyglot
        self.parent = polyglot.getNode(primary)
        
    def send_pushover(self, command = None):
        _message = int(command.get('value'))
        try:
            LOGGER.info("Sending Pushover message %s %s", self.title, ACTION[_message])
            conn = http.client.HTTPSConnection("api.pushover.net:443")
            conn.request("POST", "/1/messages.json",
                    urllib.parse.urlencode({
                        "token": self.parent.api_key,
                        "user": self.parent.user_key,
                        "title": self.title,
                        "message": ACTION[_message],
                    }), { "Content-type": "application/x-www-form-urlencoded" })
            conn.getresponse()
            conn.close()
        except Exception as inst:
            LOGGER.error("Error sending to pushover: " + str(inst))

    id = 'thingnodetype'

    commands = {
                'ACTIONS': send_pushover
                }
 
    
if __name__ == "__main__":
    try:
        polyglot = udi_interface.Interface([])
        polyglot.start('2.0.1')
        Controller(polyglot, 'controller', 'controller', 'Push')
        polyglot.runForever()
    except (KeyboardInterrupt, SystemExit):
        sys.exit(0)
