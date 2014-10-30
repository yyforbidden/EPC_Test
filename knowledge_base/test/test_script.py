from twisted.trial import unittest
from knowledge_base import context, script
from twisted.python import log

class TestScript(unittest.TestCase):


    def setUp(self):
        self.cm = context.ContextManager(r'..\knowledge_base\test\contexts')


    def tearDown(self):
        pass


    def test_run_send_script(self):
        s = script.Script(r'..\knowledge_base\test\scripts\demo_attach_req.py', 'send_attach')
        msg = {'interface': 'Iu-PS-Control',
               'direction': 'RNC->SGSN',
               'layer3': {'protocol': 'NAS',
                          'message': 'Attach Request',
                          'parameters': {'imsi': '460001234567890'}}}
        rsp = s.run(msg, self.cm)
        self.assertEqual(rsp['layer3']['message'], 'Attach Request')
        self.assertEqual(rsp['layer3']['parameters']['imsi'], '460001234567890')
        self.assertEqual(rsp['layer3']['parameters']['ti'], '0')
        log.msg(rsp)
        
    
    def test_run_recv_script(self):
        s = script.Script(r'..\knowledge_base\test\scripts\demo_attach_req.py', 'recv_attach')
        msg = {'interface': 'Iu-PS-Control',
               'direction': 'RNC->SGSN',
               'layer3': {'protocol': 'NAS',
                          'message': 'Attach Request',
                          'parameters': {'imsi': '460001234567890'}}}
        s.run(msg, self.cm)

        s = script.Script(r'..\knowledge_base\test\scripts\demo_auth_req.py', 'authentication')
        msg = {'interface': 'Iu-PS-Control',
               'direction': 'RNC<-SGSN',
               'layer1': {'protocol': 'SCCP',
                          'message': 'DataIndication',
                          'parameters': {'sccp_id': '0'}},
               'layer2': {'protocol': 'RANAP',
                          'message': 'Data Transfer',
                          'parameters': {}},
               'layer3': {'protocol': 'NAS',
                          'message': 'Authentication Request',
                          'parameters': {}}}
        rsp = s.run(msg, self.cm)
        log.msg(rsp)
        self.assertEqual(len(rsp), 1)
        self.assertEqual(rsp[0]['layer3']['message'], 'Authentication Response')
        
        
class TestScriptTreeNode(unittest.TestCase):
    

    def setUp(self):
        pass
    
    
    def tearDown(self):
        pass
    
    
    def test_add_child(self):
        n = script.ScriptTreeNode(None, None)
        c1 = script.ScriptTreeNode(None, None)
        c2 = script.ScriptTreeNode(None, None)
        n.add_child(c1)
        n.add_child(c2)
        self.assertEqual(len(n.children), 2)
        self.assertEqual(n.children[0], c1)
        self.assertEqual(n.children[1], c2)
        self.assertEqual(c1.parent, n)
        self.assertEqual(c2.parent, n)
        
        
    def test_del_child(self):
        n = script.ScriptTreeNode(None, None)
        c1 = script.ScriptTreeNode(None, None)
        c2 = script.ScriptTreeNode(None, None)
        n.add_child(c1)
        n.add_child(c2)
        n.del_child(c1)
        self.assertEqual(len(n.children), 1)
        self.assertEqual(n.children[0], c2)
        self.assertEqual(c2.parent, n)
        
        
    def test_specific_than(self):
        n1 = script.ScriptTreeNode(None, {'a': 1, 'b': 2})
        n2 = script.ScriptTreeNode(None, {'a': 1, 'b': 2, 'c': 3})
        n3 = script.ScriptTreeNode(None, {'a': 1})
        n4 = script.ScriptTreeNode(None, {'a': 1, 'c': 2})
        n5 = script.ScriptTreeNode(None, {'c': 1})
        
        self.assertFalse(n1.specific_than(n2))
        self.assertTrue(n1.specific_than(n3))
        self.assertFalse(n1.specific_than(n4))
        self.assertFalse(n1.specific_than(n5))
        
        
class TestScripTree(unittest.TestCase):
    
    def setUp(self):
        self.t = script.ScriptTree()
    
    
    def tearDown(self):
        pass
    
    
    def test_insert(self):
        s = script.Script('', '')
        # insert first child
        #  root
        #    |
        #(a=1,b=2)
        self.t.insert(s, dict(a=1, b=2))
        self.assertEqual(len(self.t.root.children), 1)
        self.assertEqual(self.t.root.children[0].paras,
                         dict(a=1, b=2))
        self.t.show()
        
        # insert a more accurate node
        #  root
        #    |
        #(a=1,b=2)
        #    |
        #(a=1,b=2,c=3)
        self.t.insert(s, dict(a=1, b=2, c=3))
        self.t.show()
        self.assertEqual(len(self.t.root.children[0].children), 1)
        self.assertEqual(self.t.root.children[0].children[0].paras,
                         dict(a=1, b=2, c=3))
        
        # insert a non-match node
        #  root
        #    |------------|
        #(a=1,b=2)      (d=2)
        #    |
        #(a=1,b=2,c=3)
        self.t.insert(s, dict(d=2))
        self.t.show()
        self.assertEqual(len(self.t.root.children), 2)
        self.assertEqual(self.t.root.children[0].children[0].paras,
                         dict(a=1, b=2, c=3))
        self.assertEqual(self.t.root.children[1].paras,
                         dict(d=2))
        
        # insert a node matches two child
        #  root
        #    |------------|
        #(a=1,b=2)      (d=2)
        #    |
        #    |------------|
        #(a=1,b=2,c=3)  (a=1,b=2,d=2)
        self.t.insert(s, dict(a=1,b=2,d=2))
        self.t.show()
        self.assertEqual(len(self.t.root.children[0].children), 2)
        self.assertEqual(self.t.root.children[0].children[0].paras,
                         dict(a=1, b=2, c=3))
        self.assertEqual(self.t.root.children[0].children[1].paras,
                         dict(a=1, b=2, d=2))
        self.assertEqual(self.t.root.children[1].paras,
                         dict(d=2))
        
        # insert a node matches none
        #  root
        #    |------------|-----------|
        #(a=1,b=2)      (d=2)   (a=1,b=3,c=3)
        #    |
        #    |------------|
        #(a=1,b=2,c=3)  (a=1,b=2,d=2)
        self.t.insert(s, dict(a=1, b=3, c=3))
        self.t.show()
        self.assertEqual(len(self.t.root.children), 3)
        self.assertEqual(self.t.root.children[2].paras,
                         dict(a=1, b=3, c=3))
        
        
        # insert a node need two adopt siblings as child
        #  root
        #    |------------|-------------------|
        #(a=1,b=2)      (d=2)             (a=1,b=3)
        #    |                                |
        #    |------------|                   |
        #(a=1,b=2,c=3)  (a=1,b=2,d=2)    (a=1,b=3,c=3)
        self.t.insert(s, dict(a=1, b=3))
        self.t.show()
        self.assertEqual(len(self.t.root.children), 3)
        self.assertEqual(self.t.root.children[2].paras,
                         dict(a=1, b=3))
        self.assertEqual(len(self.t.root.children[2].children), 1)
        self.assertEqual(self.t.root.children[2].children[0].paras,
                         dict(a=1, b=3, c=3))

    
    def test_find(self):
        self.t.insert(script.Script('', '1'), dict(a=1, b=2))
        self.t.insert(script.Script('', '2'), dict(a=1, b=2, c=3))
        self.t.insert(script.Script('', '3'), dict(d=2))
        self.t.insert(script.Script('', '4'), dict(a=1, b=2, c=4))
        self.t.insert(script.Script('', '5'), dict(a=1, b=3, c=3))
        self.t.insert(script.Script('', '6'), dict(a=1, b=3))
        self.t.show()
        
        # acurate match, first child 
        r = self.t.find(dict(a=1, b=2, c=3))
        self.assertEqual(r.module, '2')
        
        # acurate match, not first child
        r = self.t.find(dict(a=1, b=3))
        self.assertEqual(r.module, '6')
        
        # ambiguous match, double match
        r = self.t.find(dict(a=1, b=2, c=3, d=2))
        self.assertEqual(r, None)
        
        # ambiguous match, none match
        r = self.t.find(dict(x=0))
        self.assertEqual(r, None)
        
        # over match, first child, first level
        r = self.t.find(dict(a=1, b=2, c=10))
        self.assertEqual(r.module, '1')
        
        # over match, not first child, not first level
        r = self.t.find(dict(a=1, b=3, c=3, d=10))
        self.assertEqual(r.module, '5')

        
class TestScriptManager(unittest.TestCase):
    
    
    def setUp(self):
        self.cm = context.ContextManager(r'..\knowledge_base\test\contexts')
        self.sm = script.ScriptManager(r'..\knowledge_base\test\scripts')


    def tearDown(self):
        pass


    def test_load_scripts(self):
        self.assertEqual(len(self.sm._scripts), 3)
        auth_tree = self.sm._scripts[('NAS',
                                      'Iu-PS-Control',
                                      'RNC<-SGSN',
                                      'Authentication Request')]
        attach_tree = self.sm._scripts[('NAS',
                                        'Iu-PS-Control',
                                        'RNC->SGSN',
                                        'Attach Request')]
        self.assertEqual(auth_tree.root.children[0].script.module,
                         'response_to_authentication_request')
        self.assertEqual(auth_tree.root.children[0].children[0].script.module,
                         'response_to_authentication_request_2')
        self.assertEqual(attach_tree.root.children[0].script.module,
                         'send_attach_request')
        
        for k, t in self.sm._scripts.items():
            log.msg(k)
            t.show()
    
    
    def test_find_send_script(self):
        msg = {'interface': 'Iu-PS-Control',
               'direction': 'RNC->SGSN',
               'layer3': {'protocol': 'NAS',
                          'message': 'Attach Request',
                          'parameters': {'imsi': '460001234567890'}}}
        s = self.sm.find_script(msg)
        log.msg(s)
        rsp = s.run(msg, self.cm)
        self.assertEqual(rsp['layer3']['message'], 'Attach Request')
        self.assertEqual(rsp['layer3']['parameters']['ti'], '0')
        log.msg(self.sm._scripts)
        log.msg(rsp)
        
        msg = {'interface': 'Iu-PS-Control',
               'direction': 'RNC->SGSN',
               'layer3': {'protocol': 'NAS',
                          'message': 'Attach Request',
                          'parameters': {'imsi': '460001234567890',
                                         'a': '1'}}}
        s = self.sm.find_script(msg)
        log.msg(s)
        rsp = s.run(msg, self.cm)
        self.assertEqual(rsp['layer3']['message'], 'Attach Request')
        self.assertEqual(rsp['layer3']['parameters']['ti'], '10000')
        log.msg(rsp)

    def test_find_recv_script(self):
        msg = {'interface': 'Iu-PS-Control',
               'direction': 'RNC->SGSN',
               'layer3': {'protocol': 'NAS',
                          'message': 'Attach Request',
                          'parameters': {'imsi': '460001234567890'}}}
        s = self.sm.find_script(msg)
        log.msg(s)
        rsp = s.run(msg, self.cm)
        log.msg(rsp)
        
        msg = {'interface': 'Iu-PS-Control',
               'direction': 'RNC<-SGSN',
               'layer1': {'protocol': 'SCCP',
                          'message': 'DataIndication',
                          'parameters': {'sccp_id': '0'}},
               'layer2': {'protocol': 'RANAP',
                          'message': 'Data Transfer',
                          'parameters': {'x': '100'}},
               'layer3': {'protocol': 'NAS',
                          'message': 'Authentication Request',
                          'parameters': {'a': '1',
                                         'b': '2',
                                         'c': '3'}}}
        
        s = self.sm.find_script(msg)
        rsp = s.run(msg, self.cm)
        self.assertEqual(len(rsp), 2)
        self.assertEqual(rsp[0]['layer3']['message'], 'Authentication Response')
        self.assertEqual(rsp[1]['layer3']['message'], 'Authentication Response')
        log.msg(rsp)

        
# if __name__ == "__main__":
#     #import sys;sys.argv = ['', 'Test.testName']
#     unittest.main()