#!/usr/bin/env python
from __future__ import print_function
import wsma
from wsma_config import host, user, password

with wsma.HTTP(host, user, password) as w:
    w.execCLI("show run")
    print(w.output)

