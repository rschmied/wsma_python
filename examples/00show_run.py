#!/usr/bin/env python
from __future__ import print_function
from wsma.WSMA import WSMA
from wsma_config import WSMA_IP, WSMA_USER, WSMA_PASSWORD
import json

wsma = WSMA(WSMA_IP, WSMA_USER, WSMA_PASSWORD)
result = wsma.wsma_exec_text("show run")
print(result)
