import unittest
from EPCTest.dispatcher import Dispatcher
import socket
import struct
import json
import threading
import time
import Queue


class TestDispatcher(unittest.TestCase):


    def setUp(self):
        print '-'*10 + 'START ' + self._testMethodName + '-'*10
        self.name_map = {('t1',): 'tool1',
                         ('t2',): 'tool2',
                         ('t3',): 'tool3',}


    def tearDown(self):
        print '-'*10 + 'END' + '-'*10


    def start_up_tools(self, tool3=False):
        self.q = Queue.Queue()
        
        self.tool = DummyTool(10000, self.q)
        self.tool_instance = threading.Thread(target=self.tool.run_once)
        self.tool_instance.daemon = True
        self.tool_instance.start()

        self.tool2 = DummyTool(20000, self.q)
        self.tool2_instance = threading.Thread(target=self.tool2.run_once)
        self.tool2_instance.daemon = True
        self.tool2_instance.start()
        
        if tool3:
            self.tool3 = DummyTool(30000, self.q)
            self.tool3_instance = threading.Thread(target=self.tool3.run_once)
            self.tool3_instance.daemon = True
            self.tool3_instance.start()

            
    def start_up_3_responder(self, rsp=True):
        self.q = Queue.Queue()
        
        self.tool = DummyTool(10000, self.q)
        self.tool_instance = threading.Thread(target=self.tool.response, args=('tool1', rsp))
        self.tool_instance.daemon = True
        self.tool_instance.start()

        self.tool2 = DummyTool(20000, self.q)
        self.tool2_instance = threading.Thread(target=self.tool2.response, args=('tool2', rsp))
        self.tool2_instance.daemon = True
        self.tool2_instance.start()
        
        self.tool3 = DummyTool(30000, self.q)
        self.tool3_instance = threading.Thread(target=self.tool3.response, args=('tool3', rsp))
        self.tool3_instance.daemon = True
        self.tool3_instance.start()
        

    def testConnectAndDisconnect(self):
        addresses = {'tool1': ('127.0.0.1', 10000),
                     'tool2': ('127.0.0.1', 20000)}
        self.d = Dispatcher([], '', addresses, self.name_map, 0)
        
        self.start_up_tools()

        self.d._connect_to_tools()
        for i in range(2):
            data = self.q.get()
            self.assertEqual(data, 'connected')

        self.d._close_connection()
        for i in range(2):
            data = self.q.get()
            self.assertEqual(data, 'disconnected')
    
    
    def testSendScript(self):
        addresses = {'tool1': ('127.0.0.1', 10000),
                     'tool2': ('127.0.0.1', 20000)}
        
        scripts = [{'type': 'send script',
                    'office': 'tool1',
                    'script': [{'step': 'send'},
                               {'step': 'receive'}]},
                   {'type': 'send script',
                    'office': 'tool2',
                    'script': [{'step': 'send'},
                               {'step': 'receive'}]}]
        
        self.d = Dispatcher(scripts, '', addresses, self.name_map, 0)

        self.start_up_tools()        
        self.d._connect_to_tools()
        for i in range(2):
            data = self.q.get()
            self.assertEqual(data, 'connected')
        
        self.d._send_script()
        for i in range(2):
            data = self.q.get()
            self.assertEqual(data, scripts[i])
        
        self.d._close_connection()
        for i in range(2):
            data = self.q.get()
            self.assertEqual(data, 'disconnected')


    def testSendStart(self):
        addresses = {'tool1': ('127.0.0.1', 10000),
                     'tool2': ('127.0.0.1', 20000)}
        self.d = Dispatcher([], 'tool2', addresses, self.name_map, 10)

        self.start_up_tools()
        self.d._connect_to_tools()
        for i in range(2):
            data = self.q.get()
            self.assertEqual(data, 'connected')

        self.d._send_start()
        for i in range(2):
            data = self.q.get()
            self.assertEqual(data, {'type': 'start', 'office': 'tool%d'%(i+1), 'timer': 10})
        
        self.d._close_connection()
        for i in range(2):
            data = self.q.get()
            self.assertEqual(data, 'disconnected')
    
    
    def testSendEvent(self):
        addresses = {'tool1': ('127.0.0.1', 10000),
                     'tool2': ('127.0.0.1', 20000)}
        self.d = Dispatcher([], 'tool2', addresses, self.name_map, 10)
        
        self.start_up_tools()
        self.d._connect_to_tools()
        for i in range(2):
            data = self.q.get()
            self.assertEqual(data, 'connected')

        e = {'type': 'event', 'office': 'tool1', 'event': 'test'}
        self.d._send_event(e)
        data = self.q.get()
        self.assertEqual(data,
                         {'type': 'event',
                          'office': 'tool2',
                          'source': 'tool1',
                          'event': 'test'})
        
        self.d._close_connection()
        for i in range(2):
            data = self.q.get()
            self.assertEqual(data, 'disconnected')
            
    def testSendVar(self):
        addresses = {'tool1': ('127.0.0.1', 10000),
                     'tool2': ('127.0.0.1', 20000)}
        self.d = Dispatcher([], 'tool2', addresses, self.name_map, 10)
        self.start_up_tools()
        self.d._connect_to_tools()
        for i in range(2):
            data = self.q.get()
            self.assertEqual(data, 'connected')

        v = {'type': 'variable',
             'office': 'tool1',
             'variable': [{'name': 'var1', 'type': 1, 'value': '10'},
                          {'name': 'var2', 'type': 1, 'value': '20'}]}
        self.d._send_variable(v)
        data = self.q.get()
        v['office'] = 'tool2'
        self.assertEqual(data, v)
        
        self.d._close_connection()
        for i in range(2):
            data = self.q.get()
            self.assertEqual(data, 'disconnected')
        
        
    def testSendStop(self):
        addresses = {'tool1': ('127.0.0.1', 10000),
                     'tool2': ('127.0.0.1', 20000)}
        self.d = Dispatcher([], 'tool2', addresses, self.name_map, 10)
        
        self.start_up_tools()
        self.d._connect_to_tools()
        for i in range(2):
            data = self.q.get()
            self.assertEqual(data, 'connected')

        self.d._send_stop()
        data = self.q.get()
        self.assertEqual(data, {'type':'stop', 'office':'tool2'})
        
        data = self.q.get()
        self.assertEqual(data, {'type':'stop', 'office':'tool1'})
        
        self.d._close_connection()
        for i in range(2):
            data = self.q.get()
            self.assertEqual(data, 'disconnected')
        
        
    def testRecvScriptReceived(self):
        addresses = {'tool1': ('127.0.0.1', 10000),
                     'tool2': ('127.0.0.1', 20000)}
        self.d = Dispatcher([], 'tool1', addresses, self.name_map, 0)
        
        self.start_up_tools()
        self.d._connect_to_tools()
        for i in range(2):
            data = self.q.get()
            self.assertEqual(data, 'connected')
            
        self.d._state = 'wait_script_received'
        self.d._script_cnt = 2
        
        msgs = [{'type': 'script received', 'office': 'tool1'},
                {'type': 'script received', 'office': 'tool2'}]

        cmds = [{'type': 'start', 'office': 'tool2', 'timer': 0},
                {'type': 'start', 'office': 'tool1', 'timer': 0}]
        
        self.d._on_script_received(msgs[0])
        self.assertEqual(self.d._state, 'wait_script_received')
        
        self.d._on_script_received(msgs[1])
        self.assertEqual(self.d._state, 'wait_started')
        for i in range(2):
            data = self.q.get()
            self.assertEqual(data, cmds[i])
                
        self.d._close_connection()
        for i in range(2):
            data = self.q.get()
            self.assertEqual(data, 'disconnected')
    
    
    def testRecvStarted(self):
        addresses = {'tool1': ('127.0.0.1', 10000),
                     'tool2': ('127.0.0.1', 20000)}
        self.d = Dispatcher([], 'tooll1', addresses, self.name_map, 0)
        
        self.start_up_tools()
        self.d._connect_to_tools()
        for i in range(2):
            data = self.q.get()
            self.assertEqual(data, 'connected')
            
        self.d._state = 'wait_started'
        self.d._script_cnt = 2
        
        msgs = [{'type': 'started', 'office': 'tool1'},
                {'type': 'started', 'office': 'tool2'}]
        self.d._event_buffer = [{'type': 'event', 'office': 'tool1', 'event': 'test1'},
                                {'type': 'event', 'office': 'tool2', 'event': 'test2'},
                                {'type': 'event', 'office': 'tool3', 'event': 'test3'},]
        
        self.d._on_started(msgs[0])
        self.assertEqual(self.d._state, 'wait_started')
        
        self.d._on_started(msgs[1])
        for i in range(4):
            data = self.q.get()
            self.assertEqual(data['type'], 'event')
            self.assertNotEqual(data['office'], data['source'])
        self.assertEqual(self.d._state, 'started')
                
        self.d._close_connection()
        for i in range(2):
            data = self.q.get()
            self.assertEqual(data, 'disconnected')
    
    
    def testRecvEvent(self):
        addresses = {'tool1': ('127.0.0.1', 10000),
                     'tool2': ('127.0.0.1', 20000),
                     'tool3': ('127.0.0.1', 30000)}
        self.d = Dispatcher([], 'tool1', addresses, self.name_map, 0)
        
        self.start_up_tools(tool3=True)
        self.d._connect_to_tools()
        for i in range(3):
            data = self.q.get()
            self.assertEqual(data, 'connected')
            
        self.d._state = 'wait_started'
        self.d._script_cnt = 3
        self.d._script_start_cnt = 2

        
        msgs = [{'type': 'event', 'office': 'tool1', 'event': 'test1'},
               {'type': 'event', 'office': 'tool2', 'event': 'test2'},
               {'type': 'event', 'office': 'tool3', 'event': 'test3'},
               {'type': 'started', 'office': 'tool2'}]
        
        self.d._on_event(msgs[0])
        
        self.d._on_started(msgs[3])
        for i in range(2):
            data = self.q.get()
            self.assertEqual(data['type'], 'event')
            self.assertEqual(data['source'], 'tool1')
            self.assertEqual(data['event'], 'test1')
            
        self.d._on_event(msgs[1])
        for i in range(2):
            data = self.q.get()
            self.assertEqual(data['type'], 'event')
            self.assertEqual(data['source'], 'tool2')
            self.assertEqual(data['event'], 'test2')

        
        self.d._on_event(msgs[2])
        for i in range(2):
            data = self.q.get()
            self.assertEqual(data['type'], 'event')
            self.assertEqual(data['source'], 'tool3')
            self.assertEqual(data['event'], 'test3')
        
        self.assertEqual(self.d._state, 'started')
                
        self.d._close_connection()
        for i in range(3):
            data = self.q.get()
            self.assertEqual(data, 'disconnected')
    
    
    def testRecvVar(self):
        addresses = {'tool1': ('127.0.0.1', 10000),
                     'tool2': ('127.0.0.1', 20000),
                     'tool3': ('127.0.0.1', 30000),}
        self.d = Dispatcher([], 'tool1', addresses, self.name_map, 0)
        
        self.start_up_tools(tool3=True)
        self.d._connect_to_tools()
        for i in range(3):
            data = self.q.get()
            self.assertEqual(data, 'connected')
            
        self.d._state = 'wait_started'
        self.d._script_cnt = 3
        self.d._script_start_cnt = 2
        
        msgs = [{'type': 'variable',
                 'office': 'tool1',
                 'variable': [{'name': 'var1', 'type': 1, 'value': '10'},]},
                {'type': 'variable',
                 'office': 'tool2',
                 'variable': [{'name': 'var2', 'type': 1, 'value': '20'},]},
                {'type': 'variable',
                 'office': 'tool3',
                 'variable': [{'name': 'var3', 'type': 1, 'value': '30'},
                              {'name': 'var4', 'type': 1, 'value': '40'},
                              {'name': 'var1', 'type': 1, 'value': '50'},]},
                {'type': 'started', 'office': 'tool2'}]
        
        self.d._on_variable(msgs[0])

        self.d._on_started(msgs[3])
        
        d = msgs[0]
        d.pop('office')
        for i in range(2):
            data = self.q.get()
            data.pop('office')
            self.assertEqual(data, d)
        
        self.d._on_variable(msgs[1])

        d = msgs[1]
        d.pop('office')
        for i in range(2):
            data = self.q.get()
            data.pop('office')
            self.assertEqual(data, d)

        self.assertEqual(self.d.vars['var1'], '10')
        self.assertEqual(self.d.vars['var2'], '20')
        
        self.d._on_variable(msgs[2])
        
        d = msgs[2]
        d.pop('office')
        for i in range(2):
            data = self.q.get()
            data.pop('office')
            self.assertEqual(data, d)
            
        self.assertEqual(self.d.vars['var1'], '50')
        self.assertEqual(self.d.vars['var2'], '20')
        self.assertEqual(self.d.vars['var3'], '30')
        self.assertEqual(self.d.vars['var4'], '40')
        
        self.d._close_connection()
        for i in range(3):
            data = self.q.get()
            self.assertEqual(data, 'disconnected')
    
    
    def testRecvReportOnWaitStarted(self):
        addresses = {'tool1': ('127.0.0.1', 10000),
                     'tool2': ('127.0.0.1', 20000),
                     'tool3': ('127.0.0.1', 30000)}
        self.d = Dispatcher([], 'tool1', addresses, self.name_map, 0)
        
        self.start_up_tools(tool3=True)
        self.d._connect_to_tools()
        for i in range(3):
            data = self.q.get()
            self.assertEqual(data, 'connected')
            
        self.d._state = 'wait_started'
        self.d._script_cnt = 3
        self.d._script_started_cnt = 2
                
        msgs = [{'type': 'report',
                 'office': 'tool1',
                 'report': [{'name': 'var1', 'value': '10'},
                            {'name': 'var2', 'value': '20'},]},
                {'type': 'report',
                 'office': 'tool2',
                 'report': [{'name': 'var3', 'value': '30'},
                            {'name': 'var4', 'value': '40'},]},
                {'type': 'report',
                 'office': 'tool3',
                 'report': [{'name': 'var5', 'value': '50'},
                            {'name': 'var6', 'value': '60'},]},
                {'type': 'started',
                 'office': 'tool2'}]

        self.d._on_report(msgs[0])
        self.assertEqual(self.d.report['var1'], '10')
        self.assertEqual(self.d.report['var2'], '20')
        self.assertEqual(self.d._state, 'wait_report')
        
        data = self.q.get()
        self.assertEqual(data, {'type': 'stop', 'office': 'tool3'})
        data = self.q.get()
        self.assertEqual(data, {'type': 'stop', 'office': 'tool2'})
        
        self.d._on_report(msgs[2])
        self.assertEqual(self.d.report['var1'], '10')
        self.assertEqual(self.d.report['var2'], '20')
        self.assertEqual(self.d.report['var5'], '50')
        self.assertEqual(self.d.report['var6'], '60')

        self.d._on_started(msgs[3])

        self.d._on_report(msgs[1])
        self.assertEqual(self.d.report['var1'], '10')
        self.assertEqual(self.d.report['var2'], '20')
        self.assertEqual(self.d.report['var3'], '30')
        self.assertEqual(self.d.report['var4'], '40')
        self.assertEqual(self.d.report['var5'], '50')
        self.assertEqual(self.d.report['var6'], '60')
        
        self.assertEqual(self.d._state, 'finished')
                
        self.d._close_connection()
        for i in range(3):
            data = self.q.get()
            self.assertEqual(data, 'disconnected')
        

    def testRecvReportOnStarted(self):
        addresses = {'tool1': ('127.0.0.1', 10000),
                     'tool2': ('127.0.0.1', 20000),
                     'tool3': ('127.0.0.1', 30000),}
        self.d = Dispatcher([], 'tool1', addresses, self.name_map, 0)
        
        self.start_up_tools(tool3=True)
        self.d._connect_to_tools()
        for i in range(3):
            data = self.q.get()
            self.assertEqual(data, 'connected')
            
        self.d._state = 'started'
        self.d._script_cnt = 3
                
        msgs = [{'type': 'report',
                 'office': 'tool1',
                 'report': [{'name': 'var1', 'value': '10'},
                            {'name': 'var2', 'value': '20'},]},
                {'type': 'report',
                 'office': 'tool2',
                 'report': [{'name': 'var3', 'value': '30'},
                            {'name': 'var4', 'value': '40'},]},
                {'type': 'report',
                 'office': 'tool3',
                 'report': [{'name': 'var5', 'value': '50'},
                            {'name': 'var6', 'value': '60'},]}]

        self.d._on_report(msgs[0])
        for i in range(2):
            data = self.q.get()
            data.pop('office')
            self.assertEqual(data, {'type': 'stop'})
        self.assertEqual(self.d.report['var1'], '10')
        self.assertEqual(self.d.report['var2'], '20')

        self.d._on_report(msgs[1])
        self.assertEqual(self.d.report['var1'], '10')
        self.assertEqual(self.d.report['var2'], '20')
        self.assertEqual(self.d.report['var3'], '30')
        self.assertEqual(self.d.report['var4'], '40')
        
        self.d._on_report(msgs[2])
        self.assertEqual(self.d.report['var1'], '10')
        self.assertEqual(self.d.report['var2'], '20')
        self.assertEqual(self.d.report['var3'], '30')
        self.assertEqual(self.d.report['var4'], '40')
        self.assertEqual(self.d.report['var5'], '50')
        self.assertEqual(self.d.report['var6'], '60')
        
        self.assertEqual(self.d._state, 'finished')
                
        self.d._close_connection()
        for i in range(3):
            data = self.q.get()
            self.assertEqual(data, 'disconnected')
    
    
    def testRecvExceptionOnWaitScriptReceived(self):
        addresses = {'tool1': ('127.0.0.1', 10000),
                     'tool2': ('127.0.0.1', 20000),
                     'tool3': ('127.0.0.1', 30000)}
        self.d = Dispatcher([], 'tool1', addresses, self.name_map, 0)
        
        self.start_up_tools(tool3=True)
        self.d._connect_to_tools()
        for i in range(3):
            data = self.q.get()
            self.assertEqual(data, 'connected')
            
        self.d._state = 'wait_script_received'
        self.d._script_cnt = 3
        self.d._script_sent_cnt = 2
        
        msgs = [{'type': 'exception',
                 'office': 'tool1',
                 'code': 1,
                 'reason': 'test exception'},
                {'type': 'script_received',
                 'office': 'tool2'},
                {'type': 'report',
                 'office': 'tool2',
                 'report': []},
                {'type': 'report',
                 'office': 'tool3',
                 'report': []},]

        self.d._on_exception(msgs[0])
#         self.assertEqual(self.d._state, 'wait_report')
        data = self.q.get()
        self.assertEqual(data, {'type': 'stop', 'office': 'tool3'})
        data = self.q.get()
        self.assertEqual(data, {'type': 'stop', 'office': 'tool2'})

#         self.d._on_report(msgs[2])
#         self.d._on_report(msgs[3])

        self.assertEqual(self.d._state, 'finished')
                        
        self.d._close_connection()
        for i in range(3):
            data = self.q.get()
            self.assertEqual(data, 'disconnected')


    def testRecvExceptionOnWaitStarted(self):
        addresses = {'tool1': ('127.0.0.1', 10000),
                     'tool2': ('127.0.0.1', 20000),
                     'tool3': ('127.0.0.1', 30000)}
        self.d = Dispatcher([], 'tool1', addresses, self.name_map, 0)
        
        self.start_up_tools(tool3=True)
        self.d._connect_to_tools()
        for i in range(3):
            data = self.q.get()
            self.assertEqual(data, 'connected')
            
        self.d._state = 'wait_started'
        self.d._script_cnt = 3
        self.d._script_start_cnt = 2
        
        msgs = [{'type': 'exception',
                 'office': 'tool1',
                 'code': 1,
                 'reason': 'test exception'},
                {'type': 'started',
                 'office': 'tool2'},
                {'type': 'report',
                 'office': 'tool2',
                 'report': []},
                {'type': 'report',
                 'office': 'tool3',
                 'report': []},]

        self.d._on_exception(msgs[0])
#         self.assertEqual(self.d._state, 'wait_report')
        data = self.q.get()
        self.assertEqual(data, {'type': 'stop', 'office': 'tool3'})
        data = self.q.get()
        self.assertEqual(data, {'type': 'stop', 'office': 'tool2'})

#         self.d._on_started(msgs[1])
#         self.d._on_report(msgs[2])
#         self.d._on_report(msgs[3])

        self.assertEqual(self.d._state, 'finished')
                        
        self.d._close_connection()
        for i in range(3):
            data = self.q.get()
            self.assertEqual(data, 'disconnected')


    def testRecvExceptionOnStarted(self):
        addresses = {'tool1': ('127.0.0.1', 10000),
                     'tool2': ('127.0.0.1', 20000),
                     'tool3': ('127.0.0.1', 30000)}
        self.d = Dispatcher([], 'tool1', addresses, self.name_map, 0)
        
        self.start_up_tools(tool3=True)
        self.d._connect_to_tools()
        for i in range(3):
            data = self.q.get()
            self.assertEqual(data, 'connected')
            
        self.d._state = 'started'
        self.d._script_cnt = 3
        
        msgs = [{'type': 'exception',
                 'office': 'tool1',
                 'code': 1,
                 'reason': 'test exception'},
                {'type': 'report',
                 'office': 'tool2',
                 'report': []},
                {'type': 'report',
                 'office': 'tool3',
                 'report': []},]

        self.d._on_exception(msgs[0])
#         self.assertEqual(self.d._state, 'wait_report')
        
        data = self.q.get()
        self.assertEqual(data, {'type': 'stop', 'office': 'tool3'})
        data = self.q.get()
        self.assertEqual(data, {'type': 'stop', 'office': 'tool2'})
        
#         self.d._on_report(msgs[1])
#         self.d._on_report(msgs[2])
        self.assertEqual(self.d._state, 'finished')

        self.d._close_connection()
        for i in range(3):
            data = self.q.get()
            self.assertEqual(data, 'disconnected')
        
    
    def testRecvExceptionOnWaitReport(self):
        addresses = {'tool1': ('127.0.0.1', 10000),
                     'tool2': ('127.0.0.1', 20000),
                     'tool3': ('127.0.0.1', 30000)}
        self.d = Dispatcher([], 'tool1', addresses, self.name_map, 0)
        
        self.start_up_tools(tool3=True)
        self.d._connect_to_tools()
        for i in range(3):
            data = self.q.get()
            self.assertEqual(data, 'connected')
            
        self.d._state = 'wait_report'
        self.d._script_cnt = 3
        self.d._stopped_tools.add('tool2')
        
        msgs = [{'type': 'exception',
                 'office': 'tool1',
                 'code': 1,
                 'reason': 'test exception'},
                {'type': 'script_received',
                 'office': 'tool2'},
                {'type': 'report',
                 'office': 'tool2',
                 'report': []},
                {'type': 'report',
                 'office': 'tool3',
                 'report': []},]

        self.d._on_exception(msgs[0])
#         self.assertEqual(self.d._state, 'wait_report')

#         self.d._on_report(msgs[3])
        data = self.q.get()
        self.assertEqual(data, {'type': 'stop', 'office': 'tool3'})

        self.assertEqual(self.d._state, 'finished')
                        
        self.d._close_connection()
        for i in range(3):
            data = self.q.get()
            self.assertEqual(data, 'disconnected')    

    
    def testRunScript(self):
        addresses = {'tool1': ('127.0.0.1', 10000),
                     'tool2': ('127.0.0.1', 20000),
                     'tool3': ('127.0.0.1', 30000)}
        
        scripts = [{'type': 'send script',
                    'office': 'tool1',
                    'scripts': []},
                   {'type': 'send script',
                    'office': 'tool2',
                    'scripts': []},
                   {'type': 'send script',
                    'office': 'tool3',
                    'scripts': []}]
        
        self.start_up_3_responder()
        
        self.d = Dispatcher(scripts, 'tool1', addresses, self.name_map, 0)
        r, v, e = self.d.run_scripts()
        
        self.assertEqual(self.d.report['var1'], '1')
        self.assertEqual(self.d.report['var2'], '2')
        
        self.assertEqual(r['var1'], '1')
        self.assertEqual(r['var2'], '2')
        
        self.assertEqual(v, {})
        self.assertEqual(e, None)
    
        
    def testTimeout(self):
        addresses = {'tool1': ('127.0.0.1', 10000),
                     'tool2': ('127.0.0.1', 20000),
                     'tool3': ('127.0.0.1', 30000)}
        
        scripts = [{'type': 'send script',
                    'office': 'tool1',
                    'scripts': []},
                   {'type': 'send script',
                    'office': 'tool2',
                    'scripts': []},
                   {'type': 'send script',
                    'office': 'tool3',
                    'scripts': []}]
        
        self.start_up_3_responder(rsp=False)
        self.d = Dispatcher(scripts, 'tool1', addresses, self.name_map, 5)
        st_time = time.clock()
        r, v, e = self.d.run_scripts()
        ed_time = time.clock()
        
        self.assertEqual(e, 'execution time out')
        self.assertAlmostEqual(ed_time-st_time, 5, 1)

    
    def testLinkBroken(self):
        pass
    
    
    def testConnectionFailed(self):
        pass
    
    
    def testSendScriptNoResponse(self):
        pass
    
    
    def testStartNoResponse(self):
        pass
    
    
    def testStopNoResponse(self):
        pass
    
    
class DummyTool:
    def __init__(self, port, q):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.bind(('127.0.0.1', port))
        self.sock.listen(5)
        self.q = q
        
    def run_once(self):
        s, _ = self.sock.accept()
        self.q.put('connected')
        print '\n[Tools]: connected'
        buff = ''
        while True:
            data = s.recv(1024)
            if not data:
                self.q.put('disconnected')
                print '\n[Tools]: connection closed'
                break
            buff += data
            
            if len(buff) <= 4:
                print '\n[Tools]: data length < 4'
                continue
            l = struct.unpack('!I', buff[:4])[0]
            if len(buff)-4 < l:
                print '\n[Tools]: not enough data to unpack'
                continue
            
            json_str, buff = buff[4:l+4], buff[l+4:]
            json_obj = json.loads(json_str)
            self.q.put(json_obj)
            print '\n[Tools]: Received: %s' % str(json_obj)
        print '\n[Tools]: Finished'
            
            
    def response(self, office, rsp=True):
        s, _ = self.sock.accept()
        print '\n[Tools]: connected'
        buff = ''
        while True:
            data = s.recv(1024)
            if not data:
                print '\n[Tools]: connection closed'
                break
            buff += data
            
            if len(buff) <= 4:
                print '\n[Tools]: data length < 4'
                continue
            l = struct.unpack('!I', buff[:4])[0]
            if len(buff)-4 < l:
                print '\n[Tools]: not enough data to unpack'
                continue
            
            json_str, buff = buff[4:l+4], buff[l+4:]
            json_obj = json.loads(json_str)
            print '\n[Tools]: Received: %s' % str(json_obj)
            
            if json_obj['type'] == 'send script':
                print '\n[Tools]: receive send script'
                received = {'type': 'script received',
                            'office': office}
                recv_str = json.dumps(received)
                recv_len = struct.pack('!I', len(recv_str))
                print recv_str, len(recv_str)
                s.send(recv_len+recv_str)
                
            elif json_obj['type'] == 'start':
                print '\n[Tools]: receive start'
                if office == 'tool2':
                    event = {'type': 'event',
                             'office': office,
                             'event': 'evt1'}
                    evt_str = json.dumps(event)
                    evt_len = struct.pack('!I', len(evt_str))
                    s.send(evt_len+evt_str)

                started = {'type': 'started',
                           'office': office}
                start_str = json.dumps(started)
                start_len = struct.pack('!I', len(start_str))
                s.send(start_len+start_str)
                
                time.sleep(0.1)
                if office == 'tool1':
                    event = {'type': 'event',
                             'office': office,
                             'event': 'evt2'}
                    evt_str = json.dumps(event)
                    evt_len = struct.pack('!I', len(evt_str))
                    s.send(evt_len+evt_str)
                    
                if office == 'tool1' and rsp:
                    report = {'type': 'report',
                              'office': 'tool1',
                              'report': [{'name': 'var1', 'value': '1'},
                                         {'name': 'var2', 'value': '2'}]}
                    time.sleep(1)
                    rpt_str = json.dumps(report)
                    rpt_len = struct.pack('!I', len(rpt_str))
                    s.send(rpt_len + rpt_str)
                if office != 'tool1' and rsp:
                    time.sleep(1.5)
                    report = {'type': 'report',
                              'office': office,
                              'report': [{'name': 'var1', 'value': '1'},
                                         {'name': 'var2', 'value': '2'}]}
                    rpt_str = json.dumps(report)
                    rpt_len = struct.pack('!I', len(rpt_str))
                    s.send(rpt_len + rpt_str)

                    
            else:
                print '\n[Tools]: UNKNOWN MESSAGE'
                
        print '\n[Tools]: Finished'


if __name__ == "__main__":
#     import sys;sys.argv = ['', 'TestDispatcher.testRecvStarted']
    unittest.main()