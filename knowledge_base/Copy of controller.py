from twisted.internet.protocol import Protocol, ServerFactory
import struct
import json
import traceback
from context import ContextManager
from script import ScriptManager

class KB_QueryProtocol(Protocol):
    
    buffer = ''
    
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
            
            
    def _send(self, obj):
        s = json.dumps(obj)
        l = len(s)
        s = struct.pack('!I', l) + s
        self.transport.write(s)
        

    def stringRecieved(self, data):
        command_handlers = {'QuerySend': self.query_send,
                            'QueryReceive': self.query_receive,
                            'StartTest': self.start_test,
                            'StopTest': self.stop_test}
        for query in self._parse(data):
            cmd = query['command']
            msg = query['message']
            rsp = command_handlers[cmd](msg)
            self._send(rsp)
            
            
    def connectionLost(self):
        self.stop_test()

            
    def query_send(self, msg):
        s = self.factory.script_manager.find_script(msg)
        if not s:
            return msg
        else: 
            try:
                rsp_msg = s.run(msg, self.context_manager)
                rsp = {'command': 'AnswerSend',
                       'message': rsp_msg}
            except Exception:
                info = traceback.format_exc()
                rsp = self.report_error(info)
        return rsp
    
    
    def query_receive(self, msg):
        s = self.factory.script_manager.find_script(msg)
        if not s:
            rsp = self.report_error('No script for received message')
        else: 
            try:
                rsp_msg = s.run(msg, self.context_manager)
                rsp = {'command': 'AnswerRecv',
                       'message': rsp_msg}
            except Exception:
                info = traceback.format_exc()
                rsp = self.report_error(info)
        return rsp
        
        
    def start_test(self, msg):
        pass
        
        
    def stop_test(self, msg):
        self.context_manager.clear_test()
        self.context_manager = None
        self.transport.loseConnection()
        
        
    def report_error(self, reason):
        rsp = {'command': 'Exception',
               'reason': reason}
        return rsp
        
        
class KB_QueryFactory(ServerFactory):
    
    protocol = KB_QueryProtocol
    
    def __init__(self, sp, cp):
        self.script_manager = ScriptManager(sp)
        self.context_path = cp
        
        
    def buildProtocol(self, addr):
        p = ServerFactory.buildProtocol(self, addr)
        p.context_manager = ContextManager(self.context_path)
        return p
    

class Controller:
    
    def __init__(self, port, script_path, context_path):
        self.port = port
        self.script_path = script_path
        self.context_path = context_path
        
    def run(self):
        kb_query_factory = KB_QueryFactory(self.script_path,
                                           self.context_path)
        from twisted.internet import reactor
        reactor.listenTCP(self.port, kb_query_factory)
        reactor.run()