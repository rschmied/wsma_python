#!/usr/bin/env python
from __future__ import print_function
from wsma.WSMA import WSMA
from wsma_config import WSMA_IP, WSMA_USER, WSMA_PASSWORD

# use HTTP as the protocol on the given port 
wsma = WSMA(WSMA_IP, WSMA_USER, WSMA_PASSWORD, port=2204, tls=False)
result = wsma.wsma_exec_text("show run")
print(result)
