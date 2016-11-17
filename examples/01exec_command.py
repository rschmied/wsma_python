#!/usr/bin/env python
from __future__ import print_function
import json
import wsma
from wsma_config import host, user, password

with wsma.HTTP(host, user, password) as w:
    w.execCLI("show ip interface brief")
    print("\nReceived text:\n%s" % w.output)
    print("\nFull response:\n%s" % json.dumps(w.data, indent=2))
