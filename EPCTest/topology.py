from utils import keyword, logger
import ply.lex as lex
import ply.yacc as yacc


class Node:
    """
    Nodes represent NEs in the network.
    
    A node can have attributes and any attribute can be accessed by __getattr__ 
    """
    def __init__(self, name, attrs):
        self.name = name
        self._attrs = attrs


    def __getattr__(self, attr):
        return self._attrs.get(attr, '')
    
    
    def __str__(self):
        attrs = self._attrs.items()
        attrs.sort()
        attrs = ', '.join('%s=%s' % a for a in attrs)
        return 'Node: %s(%s)' % (self.name, attrs)
    
    
class Link:
    """
    Links represent connections between NEs in the network.
    
    A link can have attributes and any attribute can be accessed by __getattr__
    
    A link is in accordance with an OFFICE in PSTT, which describes simulated
    NE, DUT and the signal link between them.
    """
    
    def __init__(self, node1, node2, attrs):
        self.node1 = node1
        self.node2 = node2
        self.names = ('%s--%s' % (node1.name, node2.name),
                      '%s--%s' % (node2.name, node1.name))
        self._attrs = attrs
        self.ne_name = None
        self.ne_address = None
        self.simulator = None
        self.dut = None
        
        
    def __getattr__(self, attr):
        return self._attrs.get(attr, '')
    
    
    def __str__(self):
        attrs = self._attrs.items()
        attrs.sort()
        attrs = ', '.join('%s=%s' % a for a in attrs)
        return 'Link: %s(%s)' % (self.names[0], attrs)
    
    
class Topology:
    """
    A topology defines the virtual network test cases run on.
    
    Test cases know nothing about the real test environment, they only have
    knowledge of the topology. Test cases is not aware of real NEs which
    work as the node in the topology. It is the responsibility of the topology
    to map nodes to real NEs
    
    The topology description file is parsed by PLY - Python LEX and YACC.
    """
    
    def __init__(self):
        self._init_node_link()
        
        
    def node(self, n):
        return self._nodes[n]
    
    
    def link(self, n1, n2):
        link_name = '%s--%s' % (n1, n2)
        for l in self._links:
            if link_name in l.names:
                return l
        
    @keyword
    def load_topology(self, topo_file):
        """ Load topology description from a file. """
        
        self._init_node_link()

        topo = open(topo_file).read()
        
        # the parser will save extracted data to self._nodes and self._links
        parser = TopoParser(self._nodes, self._links)
        parser.parse(topo)
            

    @keyword
    def assign(self, simulator, dut, ne_name, address):
        """
        Assign an office in PSTT to the link in topology.
        
        The name and host address of the office must be specified.
        """
            
        link = self.link(simulator, dut)
        link.ne_name = ne_name
        addr, port = address.split(':')
        port = int(port)
        link.ne_address = (addr, port)
        link.simulator = simulator
        link.dut = dut
        

    def __iter__(self):
        return iter(self._links)
        
    
    def _init_node_link(self):
        self._nodes = {}
        self._links = []
    
    
class TopoParser:
    """
    Syntax of the topology file:
    
    [tokens]
    NODE: @\w+
    LINK: --
    LITERAL: \w+
    
    [ABNF]
    stmt_list: stmt
             | stmt stmt_list
             
    stmt: NODE
        | NODE ':' attr_list
        | NODE LINK NODE
        | NODE LINK NODE ':' attr_list
         
    attr_list: attr
             | attr ',' attr_list
             
    attr: LITERAL '=' LITERAL
    """

    def __init__(self, nodes, links, debug=False):
        self.nodes = nodes
        self.links = links
        self._debug = debug


    def debug(self, s):
        if self._debug:
            logger.info(s)
    # The Lexer
    tokens = ('NODE',
              'LITERAL',
              'LINK',)
    
    t_NODE = r'@\w+'
    t_LINK = '--'
    t_LITERAL = r'\w+'
    
    literals = ':,='
    t_ignore  = ' \t'


    def t_newline(self, t):
        r'\n+'
        t.lexer.lineno += len(t.value)

    
    def t_error(self, t):
        logger.warn("Illegal character: line %d, '%s'" % (t.lexer.lineno, t.value[0]))
        t.lexer.skip(1)
        
        
    # The Parser
    def p_stmt_list_1st(self, p):
        "stmt_list : stmt"
        self.debug("stmt_list : stmt")
        
    def p_stmt_list(self, p):
        "stmt_list : stmt stmt_list"
        self.debug("stmt_list : stmt stmt_list")
        
    def p_stmt_node(self, p):
        "stmt : NODE"
        node = Node(p[1][1:], {})
        if p[1][1:] in self.nodes:
            return
        self.nodes[p[1][1:]] = node
        self.debug("stmt : NODE -> %s" % p[1])
        
    def p_stmt_node_with_attr(self, p):
        "stmt : NODE ':' attr_list"
        node = Node(p[1][1:], dict(p[3]))
        if p[1][1:] in self.nodes:
            return
        self.nodes[p[1][1:]] = node
        self.debug("stmt : NODE ':' attr_list -> %s(%s)" % (p[1], str(p[3])))
        
    def p_stmt_link(self, p):
        "stmt : NODE LINK NODE"
        node1 = self.nodes.get(p[1][1:], None)
        node2 = self.nodes.get(p[3][1:], None)
        name = '%s--%s' % (p[1][1:], p[3][1:])
        for l in self.links:
            if name in l.names:
                return
        if node1 is None or node2 is None:
            logger.warn('Syntax Error: Undefined node in link, line %d, %s' %
                        (p.lineno(1), name))
            return 
        link = Link(node1, node2, {})
        self.links.append(link)
        self.debug("stmt : NODE LINK NODE -> %s--%s" % (p[1], p[3]))
        
    def p_stmt_link_with_attr(self, p):
        "stmt : NODE LINK NODE ':' attr_list"
        node1 = self.nodes.get(p[1][1:], None)
        node2 = self.nodes.get(p[3][1:], None)
        name = '%s--%s' % (p[1][1:], p[3][1:])
        for l in self.links:
            if name in l.names:
                return
        if node1 is None or node2 is None:
            logger.warn('Syntax Error: Undefined node in link, line %d, %s' %
                        (p.lineno(1), name))
            return 
        link = Link(node1, node2, dict(p[5]))
        self.links.append(link)
        self.debug("stmt : NODE LINK NODE ':' attr_list -> %s--%s(%s)" %
                    (p[1], p[3], str(p[5])))
        
    def p_attr_list_1st(self, p):
        "attr_list : attr"
        p[0] = [p[1]]
        self.debug("attr_list : attr -> %s" % str(p[1]))

    def p_attr_list(self, p):
        "attr_list : attr ',' attr_list"
        p[0] = p[3]
        p[0].append(p[1])
        self.debug("attr_list : attr ',' attr_list -> add %s" % str(p[1]))
        
    def p_attr(self, p):
        "attr : LITERAL '=' LITERAL"
        p[0] = (p[1], p[3])
        self.debug("attr : LITERAL '=' LITERAL -> %s=%s" % (p[1], p[3]))
        
    def p_error(self, p):
        if p:
            logger.warn('Syntax Error: line %d near "%s"' % (p.lexer.lineno, p.value))
            yacc.restart()
        else:
            logger.warn('Syntax Error at the end of file or file is empty')
        
    def parse(self, topo):
        lexer = lex.lex(module=self)
        parser = yacc.yacc(module=self, tabmodule='topo_parse_tab')
        parser.parse(topo, lexer=lexer)
