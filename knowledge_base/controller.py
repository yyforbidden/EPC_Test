from twisted.internet.protocol import Protocol, ServerFactory
from twisted.python import log
import struct
import json
import traceback
from context import ContextManager
from script import ScriptManager


class Query:
    
    def __init__(self, req, sm, cm, p):
        
        self.request = req
        self.script_manager = sm
        self.context_manager = cm
        self.protocol = p
        self.handlers = {'StartTest': self.on_start_test,
                         'StopTest': self.on_stop_test,
                         'QuerySend': self.on_query_send,
                         'QueryReceive': self.on_query_receive}
        cmd = req['command']
        self.handler = self.handlers.get(cmd, self.on_unknown_command)
        log.msg('<Query>: got %s' % cmd)
        
        
    def process(self):
        rsp = self.handler(self.request.get('message'))
        return rsp
        
        
    def on_start_test(self, msg):
        pass
    
    
    def on_stop_test(self, msg):
        self.context_manager.clear_test()
        self.protocol.transport.loseConnection()
    
        
    def on_query_send(self, msg):
        rsp = {'command': 'AnswerSend',
               'request_id': self.request['request_id'],
               'message': msg}
        try:
            s = self.script_manager.find_script(msg)
        except Exception:
            info = traceback.format_exc()
            log.msg('<Query>: find script error')
            log.msg('<Query>: %s' % info)
            log.msg('<Queyr>: sending back the original message')
            return rsp
        
        if not s:
            log.msg('<Query>: no script found for the message')
            log.msg('<Queyr>: sending back the original message')
            return rsp
        
        try:
            rsp_msg = s.run(msg, self.context_manager)
            rsp = {'command': 'AnswerSend',
                   'request_id': self.request['request_id'],
                   'message': rsp_msg}
        except Exception:
            info = traceback.format_exc()
            log.msg('<Query>: script execution error')
            log.msg('<Query>: %s' % info)
            log.msg('<Queyr>: sending exception')
            rsp = {'command': 'Exception',
                   'request_id': self.request['request_id'],
                   'reason': info}
        finally:
            return rsp
    
    
    def on_query_receive(self, msg):
        try:
            s = self.script_manager.find_script(msg)
        except Exception:
            info = traceback.format_exc()
            log.msg('<Query>: find script error')
            log.msg('<Query>: %s' % info)
            log.msg('<Queyr>: sending exception')
            rsp = {'command': 'Exception',
                   'request_id': self.request['request_id'],
                   'reason': info}
            return rsp
        
        if not s:
            log.msg('<Query>: no script found for the message')
            log.msg('<Queyr>: sending exception')
            rsp = {'command': 'Exception',
                   'request_id': self.request['request_id'],
                   'reason': 'Cannot find script'}
            return rsp
        
        try:
            rsp_msg = s.run(msg, self.context_manager)
            rsp = {'command': 'AnswerReceive',
                   'request_id': self.request['request_id'],
                   'message': rsp_msg}
        except Exception:
            info = traceback.format_exc()
            log.msg('<Query>: script execution error')
            log.msg('<Query>: %s' % info)
            log.msg('<Queyr>: sending exception')
            rsp = {'command': 'Exception',
                   'request_id': self.request['request_id'],
                   'reason': info}
        finally:
            return rsp
        
        
    def on_unknown_command(self, msg):
        rsp = {'command': 'Exception',
               'request_id': self.request.get('request_id', -1),
               'reason': 'unknown command: %s' % self.request['command']}
        
        return rsp


class KB_QueryProtocol(Protocol):
    
    buffer = ''
    
    def _parse(self, data):
        self.buffer += data
        while True:
            if len(self.buffer) <= 4:
                log.msg('<KB_Protocol>: not enough data to decode, length not received')
                break
            l = struct.unpack('!I', self.buffer[:4])[0]
            if l > (len(self.buffer)-4):
                log.msg('<KB_Protocol>: not enough data to decode, ' +
                        'length field=%d, ' % l +
                        'len(buffer)=%d' % (len(self.buffer)-4))
                break
            log.msg('<KB_Protocol>: found 1 query request')
            q, self.buffer = self.buffer[4:l+4], self.buffer[l+4:]
            try:
                q = json.loads(q)
            except ValueError:
                log.msg('<KB_Protocol>: cannot decode request')
                log.msg('<KB_Protocol>: msg=%s' % q)
                log.msg('<KB_Protocol>: err_info=%s' % traceback.format_exc())
            else:
                yield q
            
            
    def _send(self, rsp):
        s = json.dumps(rsp)
        l = len(s)
        s = struct.pack('!I', l) + s
        self.transport.write(s)
            
            
    def dataReceived(self, data):
        log.msg('<KB_Protocol>: received data: %s' % data)
        for req in self._parse(data):
            log.msg('<KB_Protocol>: got a request: %s' % req['command'])
            q = Query(req, self.script_manager, self.context_manager, self)
            rsp = q.process()
            if rsp:
                log.msg('<KB_Protocol>: resopnse: %s' % rsp['command'])
                self._send(rsp)
            
            
class KB_QueryFactory(ServerFactory):
    
    protocol = KB_QueryProtocol
    
    def __init__(self, sp, cp):
        self.script_manager = ScriptManager(sp)
        self.context_path = cp
        log.msg('<KB factory>: KB_QueryFactory created.')
        
    def buildProtocol(self, addr):
        log.msg('<KB factory>: Building protocol, address=%s...' % str(addr))
        p = ServerFactory.buildProtocol(self, addr)
        p.script_manager = self.script_manager
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
        log.msg('Starting Knowledge Base on port %d...' % self.port)
        from twisted.internet import reactor
        reactor.listenTCP(self.port, kb_query_factory)
        reactor.run()