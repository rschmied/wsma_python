#!/usr/bin/env python
from __future__ import print_function
import json
import wsma
from wsma_config import host, user, password

with wsma.HTTP(host, user, password) as w:
    w.config('snmp-server community fred-userxx RO')
    print("\nReceived data:\n%s" % json.dumps(w.data, indent=2))

