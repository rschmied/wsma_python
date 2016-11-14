# -*- coding: utf-8 -*-

"""
WSMA

The Web Services Management Agent (WSMA) defines a mechanism through which a
network device can be managed, configuration data information can be
retrieved, and new configuration data can be uploaded and manipulated. WSMA
uses Extensible Markup Language (XML)-based data encoding, that is transported
by the Simple Object Access Protocol (SOAP), for the configuration data and
protocol messages.

References:

WSMA Configuration Guide, Cisco IOS Release 15.1M
http://www.cisco.com/c/en/us/td/docs/ios/netmgmt/configuration/guide/Convert/WSMA/nm_cfg_wsma.html

Cisco IOS Web Services Management Agent Command Reference
http://www.cisco.com/c/en/us/td/docs/ios-xml/ios/wsma/command/wsma-cr-book/wsma-cr-a1.html

WSMA SDK / PDF:
https://developer.cisco.com/fileMedia/download/3d65c079-122e-4702-a1ee-233cdf565cb1

Cisco IOS XML-PI Command Reference
http://www.cisco.com/c/en/us/td/docs/ios-xml/ios/xmlpi/command/xmlpi-cr-book/xmlpi-cr-p1.html

CISCO IOS XML RULE EDITOR USER GUIDE
https://developer.cisco.com/fileMedia/download/c3c98397-5204-4ae6-8678-782239d05ce8
"""

from .http import HTTP
from .ssh import SSH

__version__ = "0.4.1"
__author__ = 'Adam Radford'
__copyright__ = 'Copyright 2016 Cisco Systems Inc.'
__license__ = 'Apache 2.0'
__title__ = 'wsma_python'
