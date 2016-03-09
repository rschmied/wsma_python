#!/usr/bin/env python
from wsma.WSMA import WSMA
from wsma_config import WSMA_IP, WSMA_USER, WSMA_PASSWORD
import json
import logging

# comment this out to turn off debug
#logging.basicConfig(level=logging.DEBUG)


wsma=WSMA(WSMA_IP, WSMA_USER, WSMA_PASSWORD)

result = wsma.wsma_config("ip access-list extended 101\n permit ip any any \nfed", action_on_fail='rollback')
print json.dumps(result, indent=4)
