from twisted.trial import unittest
from twisted.python import log
from knowledge_base.context import *


class TestContext(unittest.TestCase):


    def setUp(self):
        self.c = Context('test', 0)


    def tearDown(self):
        pass


    def test_add_field(self):
        self.c.field1 = 10
        self.assertEqual(self.c.field1, 10)
        
        
    def test_mod_field(self):
        self.c.field1 = 10
        self.c.field1 = 'aaa'
        self.assertEqual(self.c.field1, 'aaa')
        
        
class TestIndex(unittest.TestCase):
    
    def setUp(self):
        self.i = Index('user_ctxt_1', ('p1', 'p2'))
        

    def test_get_context(self):
        c = Context('user_ctxt_1', 0, p1=1, p2=2)
        self.i._indexes[(1, 2)] = c
        log.msg(self.i)

        c1 = self.i.get_context((1, 2))
        self.assertEqual(c, c1)
        
        
    def test_insert_index(self):
        c = Context('user_ctxt_1', 0, p1=1, p2=2, a=1)
        self.i.insert_index(c)
        log.msg( self.i)
        c1 = self.i.get_context((1, 2))
        self.assertEqual(c, c1)
        
        c = Context('user_ctxt_1', 1, x=1)
        self.i.insert_index(c)
        log.msg(self.i)
        c1 = self.i.get_context((1,))
        self.assertEqual(c1, None)
        
        c = Context('xxx', 2, p1=1, p2=10)
        self.i.insert_index(c)
        log.msg(self.i)
        c1 = self.i.get_context((1, 10))
        self.assertEqual(c1, None)


    def test_update_index(self):
        c = Context('user_ctxt_1', 0, p1=1, p2=2)
        self.i.insert_index(c)
        log.msg(self.i)
        
        c['p1'] = 10
        log.msg(self.i)
        c1 = self.i.get_context((10, 2))
        self.assertEqual(c, c1)
        log.msg(self.i)
        
        
    def test_delete_all_indexes(self):
        c1 = Context('user_ctxt_1', 0, p1=1, p2=2)
        c2 = Context('user_ctxt_1', 1, p1=2, p2=3)
        c3 = Context('user_ctxt_1', 2, p1=3, p2=4)
        self.i.insert_index(c1)
        self.i.insert_index(c2)
        self.i.insert_index(c3)
        log.msg(self.i)
        self.i.delete_all_index()
        log.msg(self.i)
        
        c = self.i.get_context((1,2))
        self.assertEqual(None, c)
    
        c = self.i.get_context((2,3))
        self.assertEqual(None, c)
        
        c = self.i.get_context((3,4))
        self.assertEqual(None, c)

class TestIndexList(unittest.TestCase):
    
    def setUp(self):
        self.il = IndexList('user_ctxt_1',
                            [('p1', 'p2'), ('x',), ('a', 'b', 'c')])

        
    def test_get_context(self):
        c = Context('user_ctxt_1', 0, p1=1, p2=2)
        self.il._indexes[('p1', 'p2')].insert_index(c)
        log.msg(self.il)
        c1 = self.il.get_context(('p1',1), ('p2',2))
        self.assertEqual(c, c1)
        
        self.assertEqual(None, self.il.get_context(('p1', 1), ('p2',3)))
        self.assertEqual(None, self.il.get_context(('a', 3)))
        
        
    def test_insert_index(self):
        c = Context('user_ctxt_1', 0, p1=1, p2=2, a=3, b=4, c=5, x=6)
        self.il.insert_index(c)
        log.msg(self.il)
        c1 = self.il.get_context(('p1',1), ('p2',2))
        self.assertEqual(c, c1)
        c2 = self.il.get_context(('a', 3), ('b', 4), ('c', 5))
        self.assertEqual(c, c2)
        c3 = self.il.get_context(('x',6))
        self.assertEqual(c, c3)
        
        c = Context('user_ctxt_1', 1, m=10)
        self.il.insert_index(c)
        log.msg(self.il)
        self.assertEqual(None, self.il.get_context(('m', 10)))
        
        c = Context('xxx', 2, p1=1, p2=5)
        self.il.insert_index(c)
        log.msg(self.il)
        self.assertEqual(None, self.il.get_context(('p1', 1), ('p2', 5)))
        
        
    def test_update_index(self):
        c = Context('user_ctxt_1', 0, p1=1, p2=2)
        self.il.insert_index(c)
        log.msg(self.il)
        c['p2']=10
        log.msg(self.il)
        c1 = self.il.get_context(('p1',1), ('p2',10))
        self.assertEqual(c, c1)
        
        c['a'] = 3
        c['b'] = 4
        c['c'] = 5
        log.msg(self.il)
        c2 = self.il.get_context(('a', 3), ('b', 4), ('c', 5))
        self.assertEqual(c, c2)
        
        c['x']=6
        log.msg(self.il)
        c3 = self.il.get_context(('x',6))
        self.assertEqual(c, c3)
        
        
class TestContextManager(unittest.TestCase):
    
    def setUp(self):
        self.cm = ContextManager(r'..\knowledge_base\test\contexts')


    def test_load_index_of_context(self):
        self.assertEqual(len(self.cm._indexes), 7)
        
    
    def test_create_context(self):
        uc = self.cm.create_context('user_context_1',
                                    p1=1, p2=2,
                                    a=3, b=4, c=5,
                                    m=8, n=9)
        uc['x']=6
        uc['y']=7
        
        bc = self.cm.create_context('bearer_context_1', b1=1)
        bc['b2']=2
        bc['b3']=3
        
        log.msg(self.cm)
        
        self.assertEqual(uc.type, 'user_context_1')
        uc.pop('context_id')
        self.assertEqual(uc, dict(p1=1, p2=2,
                                  a=3, b=4, c=5,
                                  x=6, y=7,
                                  m=8, n=9))
        
        self.assertEqual(bc.type, 'bearer_context_1')
        bc.pop('context_id')
        self.assertEqual(bc, dict(b1=1, b2=2, b3=3))
        
        il = self.cm._indexes['user_context_1']
        c1 = il.get_context(('p1', 1), ('p2', 2))
        c2 = il.get_context(('a', 3), ('b', 4), ('c', 5))
        c3 = il.get_context(('x', 6), ('y', 7))
        c4 = il.get_context(('m', 8), ('n', 9))
        self.assertEqual(uc, c1)
        self.assertEqual(uc, c2)
        self.assertEqual(uc, c3)
        self.assertEqual(None, c4)


    def test_get_context(self):
        uc1 = self.cm.create_context('user_context_1',
                                     p1=1, p2=2,
                                     a=3, b=4, c=5,
                                     x=6, y=7,
                                     m=8, n=9)
        
        uc2 = self.cm.create_context('user_context_1',
                                     p1=3, p2=4)
        
        log.msg(self.cm)
        c1 = self.cm.get_context('user_context_1', ('p1', 1), ('p2', 2))
        c2 = self.cm.get_context('user_context_1', ('a', 3), ('b', 4), ('c', 5))
        c3 = self.cm.get_context('user_context_1', ('x', 6), ('y', 7))
        c4 = self.cm.get_context('user_context_1', ('m', 8), ('n', 9))
        
        c_last = self.cm.get_context('user_context_1')
        c1.pop('context_id')
        c_last.pop('context_id')
        self.assertEqual(c1.type, 'user_context_1')
        self.assertEqual(c1, dict(p1=1, p2=2,
                                        a=3, b=4, c=5,
                                        x=6, y=7,
                                        m=8, n=9))

        self.assertEqual(uc1, c1)
        self.assertEqual(uc1, c2)
        self.assertEqual(uc1, c3)
        self.assertEqual(None, c4)
        self.assertEqual(uc2, c_last)
    
        self.assertEqual(c_last.type, 'user_context_1')
        self.assertEqual(c_last, dict(p1=3, p2=4))
        
    
    def test_destroy_context(self):
        uc2 = self.cm.create_context('user_context_1',
                                     a=1,b=2,c=3)
        
        uc = self.cm.create_context('user_context_1',
                                    p1=1, p2=2,
                                    a=3, b=4, c=5,
                                    x=6, y=7,
                                    m=8, n=9)
        log.msg(self.cm)
        
        c = self.cm.get_context('user_context_1')
        self.assertEqual(uc, c)
        
        self.cm.destroy_context(uc)
        log.msg(self.cm)
        
        c1 = self.cm.get_context('user_context_1', ('p1', 1), ('p2', 2))
        c2 = self.cm.get_context('user_context_1', ('a', 3), ('b', 4), ('c', 5))
        c3 = self.cm.get_context('user_context_1', ('x', 6), ('y', 7))
        c4 = self.cm.get_context('user_context_1')
        self.assertEqual(None, c1)
        self.assertEqual(None, c2)
        self.assertEqual(None, c3)
        self.assertEqual(uc2, c4)
        
    def test_clear_test(self):
        uc1 = self.cm.create_context('user_context_1',
                                      a=1,b=2,c=3)
        
        uc2 = self.cm.create_context('user_context_1',
                                     p1=1, p2=2,
                                     a=3, b=4, c=5,
                                     x=6, y=7,
                                     m=8, n=9)
        uc3 = self.cm.create_context('user_context_1',
                                      x=1, y=2)
        
        log.msg(self.cm)
        log.msg('cliearing...')
        self.cm.clear_test()
        log.msg('After clear')
        log.msg(self.cm)
        c1 = self.cm.get_context('user_context_1', ('a', 1), ('b', 2), ('c', 3))
        c2 = self.cm.get_context('user_context_1', ('p1', 1), ('p2', 2))
        c3 = self.cm.get_context('user_context_1', ('x', 1), ('y', 2))
        
        self.assertEqual(c1, None)
        self.assertEqual(c2, None)
        self.assertEqual(c3, None)
    
# if __name__ == "__main__":
#     #import sys;sys.argv = ['', 'Test.testName']
#     unittest.main()