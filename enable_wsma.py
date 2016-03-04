#!/usr/bin/env python
import sys
from Exscript import Account
from Exscript.protocols import SSH2
#logging.basicConfig(level=logging.DEBUG)

cmds="""ip http secure-server
ip http authentication local
wsma agent exec
 profile WSMA
wsma agent config
 profile WSMA
wsma profile listener WSMA
 transport https
end
"""

def main(argv):
    ip = argv[0]
    username = argv[1]
    password = argv[2]
    account = Account(name=username, password = password)
    #conn = SSH2(debug=5)
    conn = SSH2()
    # need this otherwise stupid aruba stuff gets in the way.
    conn.set_driver('ios')
    conn.connect(ip)
    conn.login(account)
    conn.execute('term len 0')
    conn.execute('show clock')
    print conn.response
    conn.execute('conf t')
    print conn.response.strip()

    for cmd in cmds.split("\n"):
        conn.execute(cmd)
        print conn.response

if __name__ == "__main__":
   main(sys.argv[1:])
