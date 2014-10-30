import unittest
from EPCTest.topology import *
import pprint


class TestNode(unittest.TestCase):


    def setUp(self):
        self.node = Node('mme1', dict(a='1', b='2', c='3'))
        print self.node


    def testNode(self):
        self.assertEqual(self.node.name, 'mme1')
        self.assertEqual(self.node.a, '1')
        self.assertEqual(self.node.b, '2')
        self.assertEqual(self.node.c, '3')
        self.assertEqual(self.node.d, '')
        
    def testNodeString(self):
        self.assertEqual(str(self.node), 'Node: mme1(a=1, b=2, c=3)')
        
        
class TestLink(unittest.TestCase):
    
    def setUp(self):
        self.node1 = Node('mme1', dict(a='1', b='2'))
        self.node2 = Node('mme2', dict(c='3', d='4')) 
        self.link = Link(self.node1, self.node2, dict(x='7', y='8'))
        print self.link
        
    def testLink(self):
        self.assertEqual(self.link.node1.name, self.node1.name)
        self.assertEqual(self.link.node2.name, self.node2.name)
        self.assertEqual(self.link.x, '7')
        self.assertEqual(self.link.y, '8')
        self.assertEqual(self.link.z, '')
        self.assertEqual(self.link.ne_name, None)
        
class TestTopology(unittest.TestCase):
    
    def setUp(self):
        self.topo_file = r'topology.txt'
        self.topo = Topology()
        
    def testLoadTopology(self):
        self.topo.load_topology(self.topo_file)
        self.assertEqual(len(self.topo._nodes), 6)
        self.assertEqual(len(self.topo._links), 5)
            
    def testGetNode(self):
        self.topo.load_topology(self.topo_file)
        node = self.topo.node('mme1')
        self.assertEqual(node.name, 'mme1')
        
    def testGetLink(self):
        self.topo.load_topology(self.topo_file)
        link = self.topo.link('mme1', 'mme2')
        self.assertEqual(link.node1.name, 'mme1')
        self.assertEqual(link.node2.name, 'mme2')
        
        link = self.topo.link('mme2', 'mme1')
        self.assertEqual(link.node1.name, 'mme1')
        self.assertEqual(link.node2.name, 'mme2')
        
    def testIteration(self):
        self.topo.load_topology(self.topo_file)
        for l in self.topo:
            self.assertTrue(isinstance(l, Link))
            
    def testAssign(self):
        self.topo.load_topology(self.topo_file)

        self.topo.assign('enb1', 'mme1', 'simu-enb1', '127.0.0.1:5000')
        self.assertEqual(self.topo.link('mme1', 'enb1').ne_name, 'simu-enb1')
        self.assertEqual(self.topo.link('mme1', 'enb1').ne_address, ('127.0.0.1', 5000))
        self.assertEqual(self.topo.link('mme1', 'enb1').ne_name, 'simu-enb1')
        self.assertEqual(self.topo.link('enb1', 'mme1').ne_address, ('127.0.0.1', 5000))
        link = self.topo.link('mme1', 'enb1')
        self.assertEqual(link.simulator, 'enb1')
        self.assertEqual(link.dut, 'mme1')

        self.topo.assign('enb2', 'mme2', 'simu-enb2', '127.0.0.1:6000')
        self.assertEqual(self.topo.link('mme2', 'enb2').ne_name, 'simu-enb2')
        self.assertEqual(self.topo.link('mme2', 'enb2').ne_address, ('127.0.0.1', 6000))
        link = self.topo.link('mme2', 'enb2')
        self.assertEqual(link.simulator, 'enb2')
        self.assertEqual(link.dut, 'mme2')
      
        
class TestTopoParser(unittest.TestCase):
    
    def setUp(self):
        self.nodes = {}
        self.links = []
        self.parser = TopoParser(self.nodes, self.links)

    
    def tearDown(self):
#         print self.nodes
#         print self.links
        pass

    
    def testNode(self):
        topo = """
        @A
        @B
        """
        self.parser.parse(topo)
        self.assertEqual(len(self.nodes), 2)
        self.assertEqual(self.nodes['A'].name, 'A')
        self.assertEqual(self.nodes['B'].name, 'B')
        
    def testNodeWithAttribute(self):
        topo = """
        @A: x= 1, y = 2
        @B : a= abc, b=xyz
        """
        self.parser.parse(topo)
        self.assertEqual(len(self.nodes), 2)
        self.assertEqual(self.nodes['A'].x, '1')
        self.assertEqual(self.nodes['A'].y, '2')
        self.assertEqual(self.nodes['B'].a, 'abc')
        self.assertEqual(self.nodes['B'].b, 'xyz')
        
    def testLink(self):
        topo = """
        @A
        @B
        @C
        @A--@B
        @B--@C
        @C--@A
        """
        self.parser.parse(topo)
        self.assertEqual(len(self.links), 3)
        found = []
        for l in self.links:
            n = list(l.names)
            n.sort()
            found.append(tuple(n))
        self.assertEqual(set(found),
                         set((('A--B', 'B--A'),
                              ('B--C', 'C--B'),
                              ('A--C', 'C--A'))))
        
    def testLinkWithAttribute(self):
        topo = """
        @A
        @B
        @C
        @A--@B : x=1, y  =  2
        @B--@C : a=aaa
        @C--@A :    x = 333
        """
        self.parser.parse(topo)
        self.assertEqual(len(self.links), 3)
        for l in self.links:
            if 'A--B' in l.names:
                ab = l
            if 'B--C' in l.names:
                bc = l
            if 'A--C' in l.names:
                ac = l
        self.assertEqual(ab.x, '1')
        self.assertEqual(ab.y, '2')
        self.assertEqual(bc.a, 'aaa')
        self.assertEqual(ac.x, '333')
        
    def testIllegalChar(self):
        topo = """
        ###
        @A
        @B
        $$$
        @C
        ()  
        @A--@B
        &&
        @B--@C
        @C--@A
        <>?
        """
        self.parser.parse(topo)
        self.assertEqual(len(self.links), 3)
        self.assertEqual(len(self.nodes), 3)
        
    def testIncompleteNode(self):
        topo = """
        @A
        @B
        @C
        @D :  
        @A--@B
        @B--@C
        @C--@A
        """
        self.parser.parse(topo)
        # Incomplete line will eat the next link defination
        self.assertEqual(len(self.links), 2)
        self.assertEqual(len(self.nodes), 3)
        
    def testInvalidNode(self):
        topo = """
        @A
        @B
        @C
        @D: aaa,bbb
        @A--@B
        @B--@C
        @C--@A
        """
        self.parser.parse(topo)
        self.assertEqual(len(self.links), 3)
        self.assertEqual(len(self.nodes), 3)
        
    def testIncompleteLink(self):
        topo = """
        @A
        @B
        @C
        @A--@
        @B--@C
        @C--@A
        @A--
        """
        self.parser.parse(topo)
        self.assertEqual(len(self.links), 1)
        self.assertEqual(len(self.nodes), 3)
        
    def testInvalidLink(self):
        topo = """
        @A
        @B
        @C
        @A--@B
        @C--@A: aaa, bbb
        @C--A
        @C--A, aaa=1
        @B--@C
        """
        self.parser.parse(topo)
        self.assertEqual(len(self.links), 2)
        self.assertEqual(len(self.nodes), 3)
        
    def testUsingUndefinedNodeInLink(self):
        topo = """
        @A
        @B
        @C
        @A--@B
        @B--@C
        @C--@A
        @C--@D
        @D--@A: x=1, y=2
        """
        self.parser.parse(topo)
        self.assertEqual(len(self.links), 3)
        self.assertEqual(len(self.nodes), 3)
        
    def testEmptyTopo(self):
        topo = """"""
        self.parser.parse(topo)
        self.assertEqual(len(self.links), 0)
        self.assertEqual(len(self.nodes), 0)
        
    def testDuplicationOfNode(self):
        topo = """
        @A
        @B
        @C
        @C
        @A--@B
        @B--@C
        @C--@A
        """
        self.parser.parse(topo)
        self.assertEqual(len(self.links), 3)
        self.assertEqual(len(self.nodes), 3)
        
    def testDubplicationOfLink(self):
        topo = """
        @A
        @B
        @C
        @A--@B
        @B--@C
        @C--@A
        @A--@B
        @C--@B
        """
        self.parser.parse(topo)
        self.assertEqual(len(self.links), 3)
        self.assertEqual(len(self.nodes), 3)
        
        
    def testNodeAfterLink(self):
        topo = """
        @A
        @B
        @C
        @A--@B
        @B--@C
        @C--@A
        @D
        @D--@A
        """
        self.parser.parse(topo)
        self.assertEqual(len(self.links), 4)
        self.assertEqual(len(self.nodes), 4)
        
        
if __name__ == "__main__":
    unittest.main()