#!/usr/bin/env python
from __future__ import print_function
import wsma
#from wsma_config import WSMA_IP, WSMA_USER, WSMA_PASSWORD
import json


# w = WSMA(WSMA_IP, WSMA_USER, WSMA_PASSWORD)
with wsma.HTTP('172.16.33.224', 'vagrant', 'vagrant', port=2224, tls=False) as w:
    w.execCLI('show ip interface brief', format_spec='built-in')
    print("\nReceived XML tree:\n%s" % json.dumps(w.odmFormatResult, indent=2))

