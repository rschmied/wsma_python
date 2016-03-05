# wsma_python
This python module shows some examples of interacting with the WSMA (Web Services Management Agent) protocol on Cisco device.

WSMA is supported on most Cisco enteprise devices (routers/switches), and first shipped in 2007.

## Installation

```

$ virtualenv env
$ source env/bin/activate
$ git clone https://github.com/aradford123/wsma_python
$ cd wmsa_python
$ python setup.py install

# update exmaples/wsma_config.py to point to your device, with appropriate credentials

$ ./update/00show_run.py

```

You can also use the script ```./enable_wsma.py <ip> <username> <password> ``` to configure WSMA if required on your device.

## exmaples 
contains a number of examples uses of the module

