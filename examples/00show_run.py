#!/usr/bin/env python
from wsma.WSMA import WSMA
from wsma_config import WSMA_IP, WSMA_USER, WSMA_PASSWORD
import json

wsma=WSMA(WSMA_IP, WSMA_USER, WSMA_PASSWORD)
result = wsma.wsma_exec("show run")
print result['response']['execLog']['dialogueLog']['received']['text']