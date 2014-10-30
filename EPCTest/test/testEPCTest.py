import unittest
import EPCTest.epctest as epctest

class TestEPCTest(unittest.TestCase):
    
    def setUp(self):
        self.e = epctest.epctest()
        
    def testKeywordsExisted(self):
        for kwname in self.e._keywords:
            kw = self.e._keywords[kwname]
            for obj in self.e._kw_src:
                attr = getattr(obj, kwname, None)
                if attr is not None:
                    break
            self.assertEqual(kw, attr)
            
    def testKeywordsFromTopology(self):
        self.assertTrue(callable(self.e.load_topology))
        self.assertTrue(callable(self.e.assign))
        
        self.assertTrue(self.e.load_topology.is_keyword)
        self.assertTrue(self.e.assign.is_keyword)
        
    def testKeywordsFromMessageSequence(self):
        self.assertTrue(callable(self.e.send))
        self.assertTrue(callable(self.e.on_recieve))
        self.assertTrue(callable(self.e.finish))
        self.assertTrue(callable(self.e.event))
        self.assertTrue(callable(self.e.wait))
        self.assertTrue(callable(self.e.retrieve_data))
        self.assertTrue(callable(self.e.check))
        self.assertTrue(callable(self.e.execute))
        
        self.assertTrue(self.e.send.is_keyword)
        self.assertTrue(self.e.on_recieve.is_keyword)
        self.assertTrue(self.e.finish.is_keyword)
        self.assertTrue(self.e.event.is_keyword)
        self.assertTrue(self.e.wait.is_keyword)
        self.assertTrue(self.e.retrieve_data.is_keyword)
        self.assertTrue(self.e.check.is_keyword)
        self.assertTrue(self.e.execute.is_keyword)
            
    def testCallOfNonExistedKeyword(self):
        def wild_call():
            self.e.foobar()
            
        self.assertRaises(AttributeError, wild_call)
        
if __name__ == "__main__":
    unittest.main()        