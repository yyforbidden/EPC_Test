from twisted.internet.protocol import Protocol, ServerFactory
from twisted.internet import defer
import struct
import json
import traceback
from context import ContextManager
from script import ScriptManager


class Query:
    
    def __init__(self, request, test_id, transport):
        self.request = request
        self.test_id = test_id
        self.transport = transport
        
        
    def answer(self, rsp):
        s = json.dumps(rsp)
        l = len(s)
        s = struct.pack('!I', l) + s
        self.transport.write(s)
        

class KB_QueryProtocol(Protocol):
    
    buffer = ''
    test_id = -1
    
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
            query = Query(q, self.test_id, self.transport)
            yield query
            
            
    def stringRecieved(self, data):
        for query in self._parse(data):
            self.factory.message_received(query)
            
            
    def connectionLost(self):
        self.factory.connection_lost(self, Query(None, self.test_id, None))

            
class KB_QueryFactory(ServerFactory):
    
    protocol = KB_QueryProtocol
    current_test_id = -1
    
    def __init__(self):
        self.deferred = {'QuerySend': defer.Deferred(),
                         'QueryReceive': defer.Deferred(),
                         'StartTest': defer.Deferred(),
                         'StopTest': defer.Deferred()}
        
        
    def buildProtocol(self, addr):
        p = ServerFactory.buildProtocol(self, addr)
        p.test_id = self._test_id()
        return p
    
    
    @classmethod
    def _test_id(self):
        self.current_test_id = (self.current_test_id + 1) % 2**32
        return self.current_test_id
    
    
    def message_received(self, q):
        cmd = q.request['command']
        self.deferred[cmd].callback(q)
        
        
    def connection_lost(self, q):
        self.deferred['StopTest'].callback(q)
        

class Controller:
    
    def __init__(self, port, script_path, context_path):
        self.port = port
        self.script_manager = ScriptManager(script_path)
        self.context_path = context_path
        self.contexts = {}

        
    def run(self):
        processors = {'StartTest': self.on_start_test,
                      'StopTest': self.on_stop_test,
                      'QuerySend': self.on_query_send,
                      'QueryReceive': self.on_query_receive}
        
        kb_query_factory = KB_QueryFactory()
        for k, d in kb_query_factory.deferred.items():
            d.addCallback(processors[k])
            d.addErrback(self.on_error)

        from twisted.internet import reactor
        reactor.listenTCP(self.port, kb_query_factory)
        reactor.run()
        
        
    def on_start_test(self, q):
        self.contexts[q.test_id] = ContextManager(self.context_path)

        
    def on_stop_test(self, q):
        c = self.contexts.pop(q.test_id, None)
        if c:
            c.clear_test()
        
        
    def on_query_send(self, q):
        msg = q.request['message']
        c = self.contexts.get(q.test_id)
        s = self.script_manager.find_script(msg)
        rsp = msg
        if s:
            try:
                rsp_msg = s.run(msg, c)
            except Exception:
                rsp = {'command': 'Exception',
                       'message': traceback.format_exc()}
            else:
                rsp = {'command': 'AnswerSend',
                       'message': rsp_msg}
        q.answer(rsp)
    
    
    def on_query_receive(self, q):
        msg = q.request['message']
        c = self.contexts.get(q.test_id)
        s = self.script_manager.find_script(msg)
        if s:
            try:
                rsp_msg = s.run(msg, c)
            except Exception:
                rsp = {'command': 'Exception',
                       'message': traceback.format_exc()}
            else:
                rsp = {'command': 'AnswerSend',
                       'message': rsp_msg}
        else:
            rsp = {'command': 'Exception',
                   'message': 'Cannot find script'}
        q.answer(rsp)


