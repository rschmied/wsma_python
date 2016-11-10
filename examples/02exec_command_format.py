#!/usr/bin/env python
from __future__ import print_function
from wsma.WSMA import WSMA
from wsma_config import WSMA_IP, WSMA_USER, WSMA_PASSWORD
import json

wsma = WSMA(WSMA_IP, WSMA_USER, WSMA_PASSWORD)

result = wsma.wsma_exec("show ip int br", format_spec="built-in")
print(json.dumps(result, indent=4))

print("\njust the recieved XML tree"))
print(result['response']['execLog']['dialogueLog']['received']['tree'])
print(json.dumps(result['response']['execLog']['dialogueLog']['received']['tree'], indent=4))
