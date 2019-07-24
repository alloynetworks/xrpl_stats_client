#!/usr/bin/env python
# coding: utf-8

from websocket import create_connection
import json
import psutil
import os
import datetime
import time
import configparser
import sys
import requests
import secrets
import distro
from hashit import make_hash

#Provide full path, if you are using a systemd service 
conf_file = 'monitor.ini'

# DO NOT EDIT BELOW THIS LINE UNLESS YOU KNOW WHAT YOU ARE DOING :)


testmode = False

if len(sys.argv) == 2:
   if sys.argv[1] == 'gensecret':
      mysecret = secrets.token_hex(16)
      print('\n')
      print("Add this secret to your ini file [credentials] section.\n\nsecret = "+mysecret)
      print("\nSubmit this secret to the endpoint while registering")
      print("This key is not stored anywhere except the ini file")
      print('\n')
      sys.exit()

   if sys.argv[1] == 'testmode':
      testmode = True
   else:
      testmode = False



config = configparser.ConfigParser()
try:
   config.read(conf_file)
except:
   print("Error in ini file. Terminating.")
   sys.exit()

# Read key/values from the ini file
if 'default' in config.sections():
   if 'interval' in config['default']:
      interval = int(config['default']['interval'])
   else:
      interval = 60
   if 'endpoint' in config['default']:
      endpoint = config['default']['endpoint']
   else:
      print("Endpoint has to be defined and valid")
      sys.exit()
else:
   print("[default] section not present")
   sys.exit()



if 'rippled' in config.sections():
   if 'domain' in config['rippled']:
      domain = config['rippled']['domain']
   else:
      domain = "None"

   if 'ws_port' in config['rippled']:
      ws_port = config['rippled']['ws_port']
   else:
      ws_port = '6006'

else:
   domain = "None"
   ws_port = '6006'   


if 'credentials' in config.sections():
   if 'secret' in config['credentials']:
      mysecret = config['credentials']['secret']
      if len(mysecret) == 0:
         print("Invalid secret length")
         sys.exit()
   else:
      print("secret not present in ini file")
      sys.exit()
else:
   print("[credentials] section not present in ini file")
   sys.exit()



def fdata():
    
    try: 
       wsock = create_connection(
            'ws://localhost:' + ws_port)

    except:
       return False
    
    try:
       
       peerq = {"command" : "server_info"}
       wsock.send(json.dumps(peerq))
        

       resp = wsock.recv()
       return resp
       
    except:
       return False 

    finally:
        wsock.close()


def get_info():
   data = {'error' : False,
           'rippled' : [],
           'system' : []
          }

   jstr = fdata()

   if jstr == False:
      data['error'] = True
   else:
      jstr = json.loads(jstr)
      data['error'] = False     
      #Rippled info
      data['rippled'].append({'domain_stated': domain})

      server_state = jstr['result']['info']['server_state']

      data['rippled'].append({'state': server_state})
      data['rippled'].append({'version': jstr['result']['info']['build_version']})
      data['rippled'].append({'uptime': jstr['result']['info']['uptime']})
      data['rippled'].append({'complete_ledgers': jstr['result']['info']['complete_ledgers']})
      data['rippled'].append({'peers': jstr['result']['info']['peers']})
      data['rippled'].append({'io_latency_ms': jstr['result']['info']['io_latency_ms']})
      
      data['rippled'].append({'validation_quorum': jstr['result']['info']['validation_quorum']})
      data['rippled'].append({'validator_list_expiration': jstr['result']['info']['validator_list']['expiration'].split(" ")[0]})
      data['rippled'].append({'pubkey_validator': jstr['result']['info']['pubkey_validator']})

      #These two entries may not always be present
      try:
         data['rippled'].append({'validated_ledger_hash': jstr['result']['info']["validated_ledger"]["hash"]})
      except:
         data['rippled'].append({'validated_ledger_hash': "Not Found"})
      try:
         data['rippled'].append({'validated_ledger_age': jstr['result']['info']["validated_ledger"]["age"]})
      except:
         data['rippled'].append({'validated_ledger_age': "Unknown"})

      numproposers = jstr['result']['info']["last_close"]["proposers"]

      data['rippled'].append({'proposers': numproposers})

      if numproposers == 0 or server_state != 'proposing':
          data['error'] = True
          

   #System information   

   data['system'].append({'mem_free_gb' : round(psutil.virtual_memory().available/1024/1024/1024,2)})
        
   s_uptime = psutil.boot_time()
   ts = datetime.datetime.now().timestamp()

   data['system'].append({'uptime' : int(ts - s_uptime)})
   data['system'].append({'timestamp_epoch' : round(time.time(),0)})        
   data['system'].append({'swap_used_gb': round(psutil.swap_memory().used/1024/1024/1024,2)})
   data['system'].append({'iowait%' : psutil.cpu_times_percent().iowait})
   data['system'].append({'stats_interval' : interval})
   osinfo = distro.info()
   data['system'].append({'os_info': osinfo})
   
   return data


while True:   
     mydata = get_info() 
     myhash = make_hash(json.dumps(mydata),mysecret)
     headers = {'Content-type': 'application/json', 'Accept': 'text/plain', 'User-Agent': 'XRPL stats client','Content-Hash' : myhash}
     if testmode == False:
        try:
           r = requests.post(endpoint, data=json.dumps(mydata), headers=headers)
        except:
           continue
     else:     
        print(json.dumps(headers))
        print(json.dumps(mydata))
     time.sleep(interval)
