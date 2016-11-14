#!/usr/bin/env python
from __future__ import print_function
import json
import wsma
from wsma_config import host, user, password, port

"""
IOS device must be configured for config rollback:
archive
 log config
  record rc
 path flash:
"""

with wsma.HTTP(host, user, password) as w:
    # note that there is a typo ('ebd') which triggers a rollback
    w.config('ip access-list extended 101\n permit ip any any \nebd', action_on_fail='rollback')
    print("\nReceived data:\n%s" % json.dumps(w.data, indent=2))

