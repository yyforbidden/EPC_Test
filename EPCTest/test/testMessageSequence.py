import unittest
import pprint
from EPCTest.topology import Topology
from EPCTest.msgseq import MessageSequence

class TestMessageSequence(unittest.TestCase):

    def setUp(self):
        t = Topology()
        self.msg_seq = MessageSequence(t)
        t.load_topology('topology.txt')
        t.assign('enb1', 'mme1', 'simu_enb1', '127.0.0.1:5000')
        t.assign('enb2', 'mme2', 'simu_enb2', '127.0.0.1:60000')
        

    def tearDown(self):
        pprint.pprint(self.msg_seq.msg_buff)        
    
    
    def testEmptyMessageBuffer(self):
        self.msg_seq._init_msg_buff()
        self.assertEqual(len(self.msg_seq.msg_buff), 2)
        enb1_buff = self.msg_seq.msg_buff[0]
        self.assertEqual(enb1_buff.ne_name, 'simu_enb1')
        self.assertEqual(enb1_buff.address, ('127.0.0.1', 5000))
        enb2_buff = self.msg_seq.msg_buff[1]
        self.assertEqual(enb2_buff.ne_name, 'simu_enb2')
        self.assertEqual(enb2_buff.address, ('127.0.0.1', 60000))


    def testSend(self):
        # 1.message from simulator to dut
        self.msg_seq.send('AttachReq', 'enb1', 'mme1',
                          paras='a: "1" ,b: 2 , c : @var1',
                          paras_to_save='a:@var2, c: @var3',
                          delay=10)
        # 2.message from dut to simulator
        self.msg_seq.send('AttachRsp', 'mme1', 'enb1')
        # 3.message from simulator to real_ne
        self.msg_seq.send('FooMsg', 'enb2', 'xgw2')
        # 4.message from real_ne to simulator
        self.msg_seq.send('BarMsg', 'xgw2', 'enb2')
        # 5.message from simulator to simulator
        self.msg_seq.send('XMsg', 'enb1', 'enb2')
        # 6.message from dut to real_ne
        self.msg_seq.send('CreateSessionReq', 'mme2', 'xgw2')
        # 7.message from real_ne to dut
        self.msg_seq.send('CreateSessionRsp', 'xgw2', 'mme2')
        # 8.message from dut to dut
        self.msg_seq.send('IDReq', 'mme1', 'mme2')
        # 9.message from real_ne to real_ne
        self.msg_seq.send('YMsg', 'xgw1', 'xgw2')
        # 10.message without parameter
        self.msg_seq.send('AttachReq', 'enb1', 'mme1')
        # 11.message on another simulator, message full name
        self.msg_seq.send('InitUE AttachReq', 'enb2', 'mme2')
        
        self.assertEqual(len(self.msg_seq.msg_buff), 2)
        for m in self.msg_seq.msg_buff:
            if 'enb1--mme1' in m.names:
                self.assertEqual(len(m), 2)
                self.assertEqual(m[0],
                                 {'step': 'Send Message',
                                  'message_alias': 'AttachReq',
                                  'paras': [{'name': 'a', 'value': '1'},
                                            {'name': 'b', 'value': 2}],
                                  'paras_to_retrieve': [{'name': 'c', 'var': 'var1'}],
                                  'paras_to_save': [{'name': 'a', 'var': 'var2'},
                                                    {'name': 'c', 'var': 'var3'}],
                                  'delay': 10})
                self.assertEqual(m[1],
                                 {'step': 'Send Message',
                                  'message_alias': 'AttachReq',
                                  'paras': [],
                                  'paras_to_retrieve': [],
                                  'paras_to_save': [],
                                  'delay': 0})
                found1 = True
            elif 'mme2--enb2' in m.names:
                self.assertEqual(len(m), 1)
                self.assertEqual(m[0],
                                 {'step': 'Send Message',
                                  'message_name': 'InitUE AttachReq',
                                  'paras': [],
                                  'paras_to_retrieve': [],
                                  'paras_to_save': [],
                                  'delay': 0})
                found2 = True
        self.assertEqual(self.msg_seq.trigger, 'simu_enb1')
        self.assertTrue(found1 and found2)
        
        
    def testOnRecieve(self):
        # 1.message from simulator to dut
        self.msg_seq.on_recieve('AttachReq', 'enb1', 'mme1')
        # 2.message from dut to simulator
        self.msg_seq.on_recieve('AttachRsp', 'mme1', 'enb1',
                                paras='a:"1", b:2, c:@var1',
                                index=4,
                                paras_to_save='a:@var2, c:@var3')
        # 3.message from simulator to real_ne
        self.msg_seq.on_recieve('FooMsg', 'enb2', 'xgw2')
        # 4.message from real_ne to simulator
        self.msg_seq.on_recieve('BarMsg', 'xgw2', 'enb2')
        # 5.message from simulator to simulator
        self.msg_seq.on_recieve('XMsg', 'enb1', 'enb2')
        # 6.message from dut to real_ne
        self.msg_seq.on_recieve('CreateSessionReq', 'mme2', 'xgw2')
        # 7.message from real_ne to dut
        self.msg_seq.on_recieve('CreateSessionRsp', 'xgw2', 'mme2')
        # 8.message from dut to dut
        self.msg_seq.on_recieve('IDReq', 'mme1', 'mme2')
        # 9.message from real_ne to real_ne
        self.msg_seq.on_recieve('YMsg', 'xgw1', 'xgw2')
        # 10.message without parameter
        self.msg_seq.on_recieve('AttachRsp', 'mme1', 'enb1')
        # 11.message on another simulator
        self.msg_seq.on_recieve('DT AttachRsp', 'mme2', 'enb2')
        
        self.assertEqual(len(self.msg_seq.msg_buff), 2)
        for m in self.msg_seq.msg_buff:
            if 'enb1--mme1' in m.names:
                self.assertEqual(len(m), 2)
                self.assertEqual(m[0],
                                 {'step': 'Receive Message',
                                  'message_alias': 'AttachRsp',
                                  'paras': [{'name': 'a', 'value': '1'},
                                            {'name': 'b', 'value': 2}],
                                  'index': 4,
                                  'paras_to_save': [{'name': 'a', 'var': 'var2'},
                                                    {'name': 'c', 'var': 'var3'}],
                                  'paras_to_retrieve': [{'name': 'c', 'var': 'var1'}]}) 
                self.assertEqual(m[1],
                                 {'step': 'Receive Message',
                                  'message_alias': 'AttachRsp',
                                  'paras': [],
                                  'index': 0,
                                  'paras_to_save': [],
                                  'paras_to_retrieve': []}) 
                found1 = True
            elif 'mme2--enb2' in m.names:
                self.assertEqual(len(m), 1)
                self.assertEqual(m[0],
                                 {'step': 'Receive Message',
                                  'message_name': 'DT AttachRsp',
                                  'paras': [],
                                  'index': 0,
                                  'paras_to_save': [],
                                  'paras_to_retrieve': []}) 
                found2 = True
        self.assertTrue(found1 and found2)

       
    def testFinish(self):
        self.msg_seq.finish('enb1--mme1')
        self.msg_seq.finish('mme1--mme2')
        self.msg_seq.finish('xgw1--enb1')
        self.msg_seq.finish('mme1--enb1')
        
        for m in self.msg_seq.msg_buff:
            if 'enb1--mme1' in m.names:
                self.assertEqual(len(m), 2)
                self.assertEqual(m[0], {'step': 'Finish'})
                self.assertEqual(m[1], {'step': 'Finish'})
                found = True
        self.assertTrue(found)
        
        
    def testWait(self):
        self.msg_seq.wait('enb1--mme1', 10)
        self.msg_seq.wait('mme1--mme2', 10)
        self.msg_seq.wait('mme1--enb1', 20)
        
        for m in self.msg_seq.msg_buff:
            if 'enb1--mme1' in m.names:
                self.assertEqual(len(m), 2)
                self.assertEqual(m[0],
                                 {'step': 'Wait',
                                  'timer': 10})
                self.assertEqual(m[1],
                                 {'step': 'Wait',
                                  'timer': 20})
                found = True
        self.assertTrue(found)
        
    def testEvent(self):
        self.msg_seq.event('enb1--mme1', 'enb2--mme2', 'Something Done!')
        self.msg_seq.event('enb1--mme1', 'mme1--enb1', 'Another thing Done!')
        self.msg_seq.event('enb1--xgw1', 'enb2--mme2', 'XXXX')
        self.msg_seq.event('mme1--mme2', 'xgw1--xgw2', 'YYYY')
        
        for m in self.msg_seq.msg_buff:
            if 'enb1--mme1' in m.names:
                found1 = True
                self.assertEqual(len(m), 3)
                self.assertEqual(m[0],
                                 {'step': 'Send Event',
                                  'event': 'Something Done!'})
                self.assertEqual(m[1],
                                 {'step': 'Send Event',
                                  'event': 'Another thing Done!'})
                self.assertEqual(m[2],
                                 {'step': 'Receive Event',
                                  'event': 'Another thing Done!',
                                  'source': 'simu_enb1'})
            elif 'enb2--mme2' in m.names:
                found2 = True
                self.assertEqual(len(m), 1)
                self.assertEqual(m[0],
                                 {'step': 'Receive Event',
                                  'event': 'Something Done!',
                                  'source': 'simu_enb1'})
                
        self.assertTrue(found1 and found2)
        
    def testRetrieveData(self):
        self.msg_seq.retrieve_data('enb1--mme1',
                                   result='@result',
                                   operation='MessageCount',
                                   paras='message:"AttachRsp", imsi:"46001"',
                                   start_message='message:"AttachReq", index:1, imsi:"46001"',
                                   end_message='message:"DT AttachAccept", index:5')
        self.msg_seq.retrieve_data('enb1--mme1',
                                   result='@result',
                                   operation='MessageCount',
                                   paras='message:"AttachRsp",imsi:"12345"')
        for m in self.msg_seq.msg_buff:
            if 'enb1--mme1' in m.names:
                found = True
                self.assertEqual(len(m), 2)
                self.assertEqual(m[0],
                                 {'step': 'Retrieve Data',
                                  'operation': 'MessageCount',
                                  'variable': 'result',
                                  'paras': [{'name': 'message', 'value':'AttachRsp'},
                                            {'name': 'imsi', 'value': '46001'}],
                                  'start_message': [{'name': 'message', 'value': 'AttachReq'},
                                                    {'name': 'index', 'value': 1},
                                                    {'name': 'imsi', 'value': '46001'}],
                                  'end_message': [{'name': 'message', 'value':'DT AttachAccept'},
                                                  {'name': 'index', 'value': 5}]})
                self.assertEqual(m[1],
                                 {'step': 'Retrieve Data',
                                  'operation': 'MessageCount',
                                  'variable': 'result',
                                  'paras': [{'name': 'message', 'value':'AttachRsp'},
                                            {'name': 'imsi', 'value': '12345'}],
                                  'start_message': [],
                                  'end_message': []})

        self.assertTrue(found)
        
        
    def testCheck(self):
        self.msg_seq.check('1==1', 'check1')
        self.msg_seq.check('"a"=="a"', 'check2')
        self.assertEqual(self.msg_seq.chk_lst.check_list[0].expr, '1==1')
        self.assertEqual(self.msg_seq.chk_lst.check_list[0].info, 'check1')
        self.assertEqual(self.msg_seq.chk_lst.check_list[1].expr, '"a"=="a"')
        self.assertEqual(self.msg_seq.chk_lst.check_list[1].info, 'check2')
    
    
if __name__ == "__main__":
    unittest.main()