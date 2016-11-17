#!/usr/bin/env python
from __future__ import print_function
import wsma
from wsma_config import host, user, password, port

# use HTTP as the protocol on the given port 
with wsma.HTTP(host, user, password, port=port, tls=False) as w:
    w.execCLI("show run")
    print(w.output)

