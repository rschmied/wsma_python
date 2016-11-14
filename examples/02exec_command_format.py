#!/usr/bin/env python
from __future__ import print_function
import json
import wsma
from wsma_config import host, user, password, port

with wsma.HTTP(host, user, password) as w:
    w.execCLI('show ip interface brief', format_spec='built-in')
    print("\nReceived data:\n%s" % json.dumps(w.odmFormatResult, indent=2))

