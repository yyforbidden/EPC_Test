from twisted.internet import reactor, defer
from twisted.internet.protocol import Protocol, ClientFactory
import json
import struct


class ClientProtocol(Protocol):
      
    buffer = ''
      
    def dataReceived(self, data):
        for rsp in self._parse():
            self.response_received(rsp)
      
      
    def response_received(self, rsp):
        d, self.d = self.d, None
        if d:
            d.callback(rsp)
          
          
    def send_query(self, q):
        if q.handler:
            self.d = defer.Deferred()
            self.d.addCallback(q.handler)
        req_str = json.dumps(q.request)
        l = len(req_str)
        data = struct.pack('!I', l) + req_str
        self.transport.write(data)
      
      
    def _parse(self, data):
        self.buffer += data
        while True:
            if len(self.buffer) <= 4:
                break
            l = struct.unpack('!I', self.buffer[:4])
            if l > len(self.buffer)-4:
                break
            q, self.buffer = self.buffer[4:l], self.buffer[l:]
            q = json.loads(q)
            yield q
     
 
class ClientProtocolFactory(ClientFactory):
     
    protocol = ClientProtocol
    
