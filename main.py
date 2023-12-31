import sys
from twisted.internet import reactor
from twisted.names import client, dns, server
from twisted.python import log
from twisted.internet import defer
from twisted.logger import Logger
from twisted.names import common, dns, error
import requests
import socket

import requests.packages.urllib3.util.connection as urllib3_cn
def allowed_gai_family4(): return socket.AF_INET  
urllib3_cn.allowed_gai_family = allowed_gai_family4

log = Logger()

def get_gip_addr():
    res = requests.get('https://ifconfig.me')
    return res.text

class SpoofResolver(common.ResolverBase):
    _ttl = 30
    def _should_resolve(self, name):
        return True

    def lookupAddress(self, name, timeout=None):
        #ここをさわると書き換えるドメイン名を指定できるよ
        if "mlpac.digitalartscloud.com" in name.decode("utf-8"):
            print("digitalartsを検知")
            addres = get_gip_addr().encode("utf-8")
        else:
            return defer.fail(error.DomainError(name))
        answer, authority, additional = common.EMPTY_RESULT
        if addres:
            answer = [
                dns.RRHeader(
                        name=name,
                        ttl=self._ttl,
                        payload=dns.Record_A(address=b'%s' % (addres,), ttl=self._ttl),
                        auth=True)
            ]

        return defer.succeed((answer, authority, additional))

        

    lookupAllRecords = lookupAddress

    def _lookup(self, name, cls, type, timeout):
        if self._should_resolve(name):
            return defer.succeed(common.EMPTY_RESULT)
        return defer.fail(error.DomainError(name))

def main():
    #log.startLogging(sys.stderr)

    factory = server.DNSServerFactory(
        clients=[
            SpoofResolver(),
            client.Resolver(servers=[('8.8.8.8', 53), ('8.8.4.4', 53)])
        ]
    )
    protocol = dns.DNSDatagramProtocol(factory)

    reactor.listenUDP(53, protocol)
    reactor.listenTCP(53, factory)

    reactor.run()

def webapp():
    def application(environ, start_response):
        
        start_response('200 OK', [('Content-type', 'text/plain')])

        return ["""function user_proxy(url, host) {return "DIRECT";}function FindProxyForURL(url, host) {return "DIRECT";}""".encode('utf-8')]
    from wsgiref import simple_server
    server = simple_server.make_server('', 80, application)
    server.serve_forever()

import threading



if __name__ == '__main__':
    threading.Thread(target=webapp).start()
    raise SystemExit(main())
