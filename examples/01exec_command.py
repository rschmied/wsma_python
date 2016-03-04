#!/usr/bin/env python
from wsma.WSMA import WSMA
from wsma_config import WSMA_IP, WSMA_USER, WSMA_PASSWORD
import json

wsma=WSMA(WSMA_IP, WSMA_USER, WSMA_PASSWORD)
result = wsma.wsma_exec("show ip int br")
print "Full response"
print json.dumps(result, indent=4)

print
print "just the recieved text"
print result['response']['execLog']['dialogueLog']['received']['text']