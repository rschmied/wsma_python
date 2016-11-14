#!/usr/bin/env python
from __future__ import print_function
import wsma
from wsma_config import WSMA_IP, WSMA_USER, WSMA_PASSWORD

# use HTTP as the protocol on the given port 
w = wsma.HTTP(WSMA_IP, WSMA_USER, WSMA_PASSWORD, port=2204, tls=False)
w.execCLI("show run")
print(w.output)

