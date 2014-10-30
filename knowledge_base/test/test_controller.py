from twisted.trial import unittest
from twisted.test import proto_helpers
from twisted.python import log
from twisted.internet import defer
from twisted.internet.protocol import Protocol, ClientFactory
from twisted.test import proto_helpers
import json
import struct
import os
from knowledge_base.context import ContextManager
from knowledge_base.script import ScriptManager
from knowledge_base.controller import *


attach_msg = {'interface': 'Iu-PS-Control',
              'direction': 'RNC->SGSN',
              'layer3': {'protocol': 'NAS',
                         'message': 'Attach Request',
                         'parameters': {'imsi': '460001234567890'}}}
auth_msg = {'interface': 'Iu-PS-Control',
            'direction': 'RNC<-SGSN',
            'layer1': {'protocol': 'SCCP',
                       'message': 'DataIndication',
                       'parameters': {'sccp_id': '0'}},
            'layer2': {'protocol': 'RANAP',
                       'message': 'Data Transfer',
                       'parameters': {}},
            'layer3': {'protocol': 'NAS',
                       'message': 'Authentication Request',
                       'parameters': {'a': '1', 'b': '2'}}}
unknown_attach_msg = {'interface': 'Iu-PS-Control',
                      'direction': 'RNC->SGSN',
                      'layer3': {'protocol': 'NAS',
                                 'message': 'Attach Request fake',
                                 'parameters': {'imsi': '460001234567890'}}}

expected_attach_msg = {'interface': 'Iu-PS-Control',
                        'direction': 'RNC->SGSN',
                        'layer1': {'message': 'Connection Request',
                                   'protocol': 'SCCP',
                                   'parameters': {'sccp_id': '0'}},
                        'layer2': {'message': 'Initial UE',
                                   'protocol': 'RANAP',
                                   'parameters': {}},
                        'layer3': {'message': 'Attach Request',
                                   'protocol': 'NAS',
                                   'parameters': {'imsi': '460001234567890',
                                                  'ti': '0'}}}
expected_auth_rsp = [{'interface': 'Iu-PS-Control',
                         'layer2': {'message': 'Data Transfer',
                                    'protocol': 'RANAP',
                                    'parameters': {}},
                         'direction': 'RNC->SGSN',
                         'layer3': {'message': 'Authentication Response',
                                    'protocol': 'NAS',
                                    'parameters': {'imsi': '460001234567890', 'ti': '0'}},
                         'layer1': {'message': 'DataIndication',
                                    'protocol': 'SCCP',
                                    'parameters': {'sccp_id': '0'}}}]
error_msg = {'interface': 'ErrorInterface',
               'direction': 'Error-dir',
               'layer3': {'protocol': 'Error',
                          'message': 'Error Request',
                          'parameters': {'imsi': '460001234567890'}}}

cmd_start_test = {'command': 'StartTest', 'request_id': '1'}
cmd_stop_test = {'command': 'StopTest', 'request_id': '1'}

cmd_query_send = {'command': 'QuerySend', 'request_id': '1', 'message': attach_msg}
cmd_query_receive = {'command': 'QueryReceive', 'request_id': '1', 'message': auth_msg}
ans_query_send = {'command': 'AnswerSend', 'request_id': '1', 'message': expected_attach_msg}
ans_query_receive = {'command': 'AnswerReceive', 'request_id': '1', 'message': expected_auth_rsp}

cmd_query_send_unknown = {'command': 'QuerySend', 'request_id': '1', 'message': unknown_attach_msg}
cmd_query_receive_unknown = {'command': 'QueryReceive', 'request_id': '1', 'message': unknown_attach_msg}
ans_query_send_unknown = {'command': 'AnswerSend', 'request_id': '1', 'message': unknown_attach_msg}

cmd_query_send_run_error = {'command': 'QuerySend', 'request_id': '1', 'message': error_msg}
cmd_query_receive_run_error = {'command': 'QueryReceive', 'request_id': '1', 'message': error_msg}

unknown_cmd = {'command': 'unknown', 'request_id': '1'}

no_script_exception = {'command': 'Exception', 'request_id': '1', 'reason': 'Cannot find script'}
unknown_cmd_exception = {'command': 'Exception', 'request_id': '1', 'reason': 'unknown command: unknown'}

class TestQuery(unittest.TestCase):
    
    def setup(self):
        pass
    
    
    def test_on_start_test(self):
        q = Query(cmd_start_test, None, None, None)
        self.assertEqual(q.request, cmd_start_test)
        rsp = q.process()
        self.assertEqual(None, rsp)
    
    
    def test_on_stop_test(self):
        class C:
            clear_test_called = False
            @classmethod
            def clear_test(self):
                self.clear_test_called = True
            
        class T:
            lose_connection_called = False
            @classmethod
            def loseConnection(self):
                self.lose_connection_called = True
            
        class P:
            def __init__(self):
                self.transport = T()
                
        c = C()
        p = P()
        q = Query(cmd_stop_test, None, c, p)
        rsp = q.process()
        self.assertEqual(q.request, cmd_stop_test)
        self.assertTrue(C.clear_test_called)
        self.assertTrue(p.transport.lose_connection_called)
        self.assertEqual(None, rsp)
        
        
    def test_on_query_send(self):
        sm = ScriptManager(r'..\knowledge_base\test\scripts')
        cm = ContextManager(r'..\knowledge_base\test\contexts')
        q = Query(cmd_query_send, sm, cm, None)
        rsp = q.process()
        log.msg(rsp)
        log.msg(ans_query_send)
        self.assertEqual(q.request, cmd_query_send)
        self.assertEqual(rsp, ans_query_send)
    
    
    def test_on_query_receive(self):
        sm = ScriptManager(r'..\knowledge_base\test\scripts')
        cm = ContextManager(r'..\knowledge_base\test\contexts')
        q = Query(cmd_query_send, sm, cm, None)
        rsp = q.process()
        log.msg(rsp)
        q = Query(cmd_query_receive, sm, cm, None)
        rsp = q.process()
        log.msg(rsp)
        log.msg(ans_query_receive)
        self.assertEqual(rsp, ans_query_receive)
        self.assertEqual(q.request, cmd_query_receive)
        
        
    def test_send_script_cannot_be_found(self):
        sm = ScriptManager(r'..\knowledge_base\test\scripts')
        cm = ContextManager(r'..\knowledge_base\test\contexts')
        q = Query(cmd_query_send_unknown, sm, cm, None)
        rsp = q.process()
        log.msg(rsp)
        self.assertEqual(ans_query_send_unknown, rsp)
    
    
    def test_receive_script_cannot_be_found(self):
        sm = ScriptManager(r'..\knowledge_base\test\scripts')
        cm = ContextManager(r'..\knowledge_base\test\contexts')
        q = Query(cmd_query_receive_unknown, sm, cm, None)
        rsp = q.process()
        log.msg(rsp)
        self.assertEqual(no_script_exception, rsp)
    
    
    def test_send_script_execute_error(self):
        self.maxDiff = None
        sm = ScriptManager(r'..\knowledge_base\test\scripts')
        cm = ContextManager(r'..\knowledge_base\test\contexts')
        q = Query(cmd_query_send_run_error, sm, cm, None)
        rsp = q.process()
        log.msg(rsp)
        self.assertEqual('Exception', rsp['command'])
        self.assertEqual('1', rsp['request_id'])
        self.assertTrue('Error in script' in rsp['reason'])
    

    def test_receive_script_execute_error(self):
        self.maxDiff = None
        sm = ScriptManager(r'..\knowledge_base\test\scripts')
        cm = ContextManager(r'..\knowledge_base\test\contexts')
        q = Query(cmd_query_receive_run_error, sm, cm, None)
        rsp = q.process()
        log.msg(rsp)
        self.assertEqual('Exception', rsp['command'])
        self.assertEqual('1', rsp['request_id'])
        self.assertTrue('Error in script' in rsp['reason'])
    

    def test_unknown_command(self):
#         req = {'command': 'unknown',
#                'request_id': 1}
#         
#         expected_rsp = {'command': 'Exception',
#                         'request_id': 1,
#                         'reason': 'unknown command: unknown'}
#         
        q = Query(unknown_cmd, None, None, None)
        rsp = q.process()
        log.msg(rsp)
        self.assertEqual(rsp, unknown_cmd_exception)
        
        
class TestProtocol(unittest.TestCase):
    
    def setUp(self):
        sp = r'..\knowledge_base\test\scripts'
        cp = r'..\knowledge_base\test\contexts'
        self.f = KB_QueryFactory(sp, cp)
        self.p = self.f.buildProtocol(('127.0.0.1', 0))
        self.tr = proto_helpers.StringTransport()
        self.p.makeConnection(self.tr)
    
    
    def tearDown(self):
        pass
    
    
    def test_start_test(self):
        req_str = json.dumps(cmd_start_test)
        l = len(req_str)
        req_str = struct.pack('!I', l) + req_str
        self.p.dataReceived(req_str)


    def test_stop_test(self):
        req_str = json.dumps(cmd_stop_test)
        l = len(req_str)
        req_str = struct.pack('!I', l) + req_str
        self.p.dataReceived(req_str)
        
        
    def test_query_send(self):
        req_str = json.dumps(cmd_query_send)
        l = len(req_str)
        req_str = struct.pack('!I', l) + req_str
        self.p.dataReceived(req_str)
        data = self.tr.value()
        l = struct.unpack('!I', data[:4])[0]
        rsp = data[4:]
        self.assertEqual(json.loads(rsp), ans_query_send)
        self.assertEqual(l, len(rsp))
        
        
    def test_query_receive(self):
        attach_req_str = json.dumps(cmd_query_send)
        l = len(attach_req_str)
        attach_req_str = struct.pack('!I', l) + attach_req_str
        self.p.dataReceived(attach_req_str)
        self.tr.clear()
        
        req_str = json.dumps(cmd_query_receive)
        l = len(req_str)
        req_str = struct.pack('!I', l) + req_str
        self.p.dataReceived(req_str)
        
        data = self.tr.value()
        l = struct.unpack('!I', data[:4])[0]
        rsp = data[4:]
        self.assertEqual(json.loads(rsp), ans_query_receive)
        self.assertEqual(l, len(rsp))
        
        
    def test_query_send_no_script(self):
        req_str = json.dumps(cmd_query_send_unknown)
        l = len(req_str)
        req_str = struct.pack('!I', l) + req_str
        self.p.dataReceived(req_str)
        data = self.tr.value()
        l = struct.unpack('!I', data[:4])[0]
        rsp = data[4:]
        self.assertEqual(json.loads(rsp), ans_query_send_unknown)
        self.assertEqual(l, len(rsp))
        
    
    def test_query_receive_no_script(self):
        req_str = json.dumps(cmd_query_receive_unknown)
        l = len(req_str)
        req_str = struct.pack('!I', l) + req_str
        self.p.dataReceived(req_str)
        
        data = self.tr.value()
        l = struct.unpack('!I', data[:4])[0]
        rsp = data[4:]
        self.assertEqual(json.loads(rsp), no_script_exception)
        self.assertEqual(l, len(rsp))
    
    
    def test_query_send_execute_error(self):
        self.maxDiff = None
        req_str = json.dumps(cmd_query_send_run_error)
        l = len(req_str)
        req_str = struct.pack('!I', l) + req_str
        self.p.dataReceived(req_str)
        data = self.tr.value()
        l = struct.unpack('!I', data[:4])[0]
        rsp = json.loads(data[4:])
        self.assertEqual('Exception', rsp['command'])
        self.assertEqual('1', rsp['request_id'])
        self.assertTrue('Error in script' in rsp['reason'])
        self.assertEqual(l, len(data[4:]))
    
    
    def test_query_receive_execute_error(self):
        self.maxDiff = None
        req_str = json.dumps(cmd_query_receive_run_error)
        l = len(req_str)
        req_str = struct.pack('!I', l) + req_str
        self.p.dataReceived(req_str)
        data = self.tr.value()
        l = struct.unpack('!I', data[:4])[0]
        rsp = json.loads(data[4:])
        self.assertEqual('Exception', rsp['command'])
        self.assertEqual('1', rsp['request_id'])
        self.assertTrue('Error in script' in rsp['reason'])
        self.assertEqual(l, len(data[4:]))
        
        
    def test_unknown_command(self):
        req_str = json.dumps(unknown_cmd)
        l = len(req_str)
        req_str = struct.pack('!I', l) + req_str
        self.p.dataReceived(req_str)
        data = self.tr.value()
        l = struct.unpack('!I', data[:4])[0]
        rsp = data[4:]
        self.assertEqual(json.loads(rsp), unknown_cmd_exception)
        self.assertEqual(l, len(rsp))
        
        
class ClientProtocol(Protocol):
      
    buffer = ''
    
    
    def connectionMade(self):
        Protocol.connectionMade(self)
        self.result = {}
        
      
    def dataReceived(self, data):
        for rsp in self._parse(data):
            self.response_received(rsp)
      
      
    def response_received(self, rsp):
        request_id = rsp['request_id']
        d = self.result.pop(request_id)
        d.callback(rsp)
          
          
    def send_query(self, request):
        d = defer.Deferred()
        request_id = request['request_id']
        self.result[request_id] = d
        req_str = json.dumps(request)
        l = len(req_str)
        data = struct.pack('!I', l) + req_str
        self.transport.write(data)
        return d
      
      
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
     
    
class TestFromClient(unittest.TestCase):
    
    def setUp(self):
        sp = r'..\knowledge_base\test\scripts'
        cp = r'..\knowledge_base\test\contexts'
        f = KB_QueryFactory(sp, cp)
        from twisted.internet import reactor
        self.port = reactor.listenTCP(0, f, interface='127.0.0.1')
        self.client = None
        
    
    def tearDown(self):
        if self.client is not None:
            self.client.transport.loseConnection()
        return self.port.stopListening()
    
    
    def _create_client(self):
        from twisted.internet import protocol, reactor
        creator = protocol.ClientCreator(reactor, ClientProtocol)
        d = creator.connectTCP('127.0.0.1', self.port.getHost().port)
        return d
    
    
    def _send(self, client, req):
        self.client = client
        self.client.send_query(req)
        return client


    def _send_and_check(self, client, req, expected_rsp):
        self.client = client
        d = self.client.send_query(req)
        d.addCallback(self.assertEqual, expected_rsp)
        return client
    
    
    def _send_and_check_exception_head(self, client, req):
        def check_exc_head(rsp):
            self.assertEqual(rsp['command'], 'Exception')
            self.assertEqual(rsp['request_id'], req['request_id'])
            self.assertTrue('Error in script' in rsp['reason'])
        self.client = client
        d = self.client.send_query(req)
        d.addCallback(check_exc_head)
        return client
    
        
    def test_start_test(self):
        d = self._create_client()
        d.addCallback(self._send, cmd_start_test)
        return d
    
    
    def test_stop_test(self):
        d = self._create_client()
        d.addCallback(self._send, cmd_start_test)
        d.addCallback(self._send, cmd_stop_test)
        return d
    
    
    def test_query_send(self):
        d = self._create_client()
        d.addCallback(self._send, cmd_start_test)
        d.addCallback(self._send_and_check, cmd_query_send, ans_query_send)
        d.addCallback(self._send, cmd_stop_test)
        return d
    
    
    def test_query_receive(self):
        d = self._create_client()
        d.addCallback(self._send, cmd_start_test)
        d.addCallback(self._send, cmd_query_send)
        d.addCallback(self._send_and_check, cmd_query_receive, ans_query_receive)
        d.addCallback(self._send, cmd_stop_test)
        return d
    
    
    def test_query_send_no_script(self):
        d = self._create_client()
        d.addCallback(self._send, cmd_start_test)
        d.addCallback(self._send_and_check, cmd_query_send_unknown, ans_query_send_unknown)
        d.addCallback(self._send, cmd_stop_test)
        return d
    
    
    def test_query_receive_no_script(self):
        d = self._create_client()
        d.addCallback(self._send, cmd_start_test)
        d.addCallback(self._send_and_check, cmd_query_receive_unknown, no_script_exception)
        d.addCallback(self._send, cmd_stop_test)
        return d
    
    
    def test_query_send_execute_error(self):
        d = self._create_client()
        d.addCallback(self._send, cmd_start_test)
        d.addCallback(self._send_and_check_exception_head, cmd_query_send_run_error)
        d.addCallback(self._send, cmd_stop_test)
        return d
        
        
    def test_query_receive_execute_error(self):
        d = self._create_client()
        d.addCallback(self._send, cmd_start_test)
        d.addCallback(self._send_and_check_exception_head, cmd_query_receive_run_error)
        d.addCallback(self._send, cmd_stop_test)
        return d
        
        
    def test_unknown_command(self):
        d = self._create_client()
        d.addCallback(self._send, cmd_start_test)
        d.addCallback(self._send_and_check, unknown_cmd, unknown_cmd_exception)
        d.addCallback(self._send, cmd_stop_test)
        return d
        
