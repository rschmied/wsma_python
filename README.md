# wsma_python
This python module shows some examples of interacting with the WSMA (Web Services Management Agent) protocol on 
Cisco devices.

WSMA is supported on most Cisco enteprise devices (routers/switches), and first shipped in 2007.

## Installation

```
# a virtualenv installation
$ virtualenv env
$ source env/bin/activate

# now copy the code from github
$ git clone https://github.com/aradford123/wsma_python
$ cd wmsa_python

# install it in the virtual environement
$ python setup.py install

# update exmaples/wsma_config.py to point to your device, with appropriate credentials

$ ./update/00show_run.py

```

You can also use the script ```./enable_wsma.py <ip> <username> <password> ``` to configure WSMA if required on your device.  
This configures WSMA over https, you can also use HTTP or SSH as a transport.

You can also just paste in this config snippet.  This configures HTTPS transport (also supports SSH/HTTP) and local Authentication (can also support AAA)

```
ip http secure-server
ip http authentication local
wsma agent exec
 profile WSMA
wsma agent config
 profile WSMA
wsma profile listener WSMA
 transport https
end
```

## examples
contains a number of examples uses of the module.  

