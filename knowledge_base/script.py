import imp
import os
import json
from twisted.python import log

class ScriptManager:
    
    def __init__(self, path):
        self._scripts = {}
        self._load_scripts(path)
        

    def _load_scripts(self, path):
        # "meta" folder in the script path contains the message feature mapping
        # to each script. The mapping ".meta" file can be seperated into any
        # number of pieces. User can write each feature in a seperate file to
        # simplify the maintainance of the mapping files. 
        meta_path = os.path.join(path, 'meta')
        for root, _, files in os.walk(meta_path):
            for f in files:
                if not f.endswith('.meta'):
                    continue
                fullpath = os.path.join(root, f)
                f = open(fullpath)
                meta = json.load(f)['scripts']
                for m in meta:
                    self._insert_meta(path, m)
         

    def _insert_meta(self, path, m):
        feature = (m['feature']['protocol'],
                   m['feature']['interface'],
                   m['feature']['direction'],
                   m['feature']['message'])
        script_tree = self._scripts.setdefault(feature, ScriptTree())
        s_path = os.path.join(path, m['script']['path'])
        script = Script(s_path, m['script']['module'])
        script_tree.insert(script, m['feature']['parameters'])

    
    def find_script(self, msg):
        i = msg['interface']
        d = msg['direction']
        
        layers = [l for l in msg.keys() if l.startswith('layer')]
        # sort the layers from top to bottom
        layers.sort(reverse=True)
        
        script_tree = None
        
        for l in layers:
            # layers is sorted by layers, returning the first matching script
            p = msg[l]['protocol']
            m = msg[l]['message']
            script_tree = self._scripts.get((p, i, d, m))
            if script_tree:
                break
            
        if not script_tree:
            log.msg('No script found matching the message')
            return None
        
        script = script_tree.find(self._deflate(msg))
        if not script:
            log.msg('No script found matching the message')
            return None
        log.msg('Script found, module=%s, path=%s' % (script.module, script.path))
        return script
    
    
    def _deflate(self, msg):
        paras = {}
        l_paras = [self._deflate_layer(layer)
                   for k, layer in msg.items()
                   if k.startswith('layer')]
        map(paras.update, l_paras)
        return paras
    
    
    def _deflate_layer(self, layer):
        leading = layer['message']
        paras = self._deflate_para(leading, layer['parameters'])
        return paras


    def _deflate_para(self, leading, para):
        result = {}
        for k, v in para.items():
            para_name = '%s.%s' % (leading, k)
            if type(v) is dict:
                result.update(self._deflate(para_name, v))
            elif type(v) is list:
                # index of list is omitted to match feature writing style
                # feature style for list is the same as for value
                # e.g.
                # feature: Msg.list_para=10
                # message: Msg.list_para=[1,4,10]
                # message after deflated:
                #   Msg.list_para=1, Msg.list_para=4, Msg.list_para=10
                # now the msg can match with the feature
                deflated_list = [(para_name, d) for d in v]
                result.update(dict(deflated_list))
            else:
                result[para_name] = v
        return result
    

class ScriptTree:
    
    def __init__(self, root=None):
        if not root:
            self.root = ScriptTreeNode(None, {})
        else:
            self.root = root
        
        
    def show(self, level=0):
        if level == 0:
            log.msg('\nroot')
        else:
            leading = ' |'*level + '-'
            s = '%s%s:%s' % (leading,
                             str(self.root.paras),
                             str(self.root.script.module))
            log.msg(s)
        if self.root.children == []:
            return
        for c in self.root.children:
            sub_tree = ScriptTree(c)
            sub_tree.show(level+1)
            
        
        
    def insert(self, script, paras):
        node = ScriptTreeNode(script, paras)
        
        # the node can only be inserted to a more general root 
        if not node.specific_than(self.root):
            return False
        
        # try to insert the node to each branch
        for c in self.root.children:
            sub_tree = ScriptTree(c)
            r = sub_tree.insert(script, paras)
            if r:
                return True
            
        # if not inserted into branches, add a new branch
        self.root.add_child(node)
        # check if any siblings of the new node is
        # sub-tree of the new node. If so, move the tree branch
        for c in self.root.children:
            if c == node:
                continue
            if c.specific_than(node):
                c.parent.del_child(c)
                node.add_child(c)
        return True

    
    def find(self, paras):
        virtual_node = ScriptTreeNode(None, paras)
        if not virtual_node.specific_than(self.root):
            return None
        
        n = [c for c in self.root.children
             if virtual_node.specific_than(c)]
        
        cnt = len(n)
        if cnt == 1:
            # node will be find in sub-tree
            sub_tree = ScriptTree(n[0])
            return sub_tree.find(paras)
        elif cnt == 0:
            # node matches none of sub-tree
            return self.root.script
        else:
            # more than one sub-tree matches, ambiguous
            return None
    
    
class ScriptTreeNode:
    
    def __init__(self, script, paras):
        self.paras = paras
        self.script = script
        self.parent = None
        self.children = []
        
        
    def __str__(self):
        return str(self.paras)
    
    
    def __repr__(self):
        return str(self)
    
    
    def add_child(self, node):
        self.children.append(node)
        node.parent = self
    
    
    def del_child(self, node):
        self.children.remove(node)
    
    
    def specific_than(self, node):
        my_para = set(self.paras.items())
        node_para = set(node.paras.items())
        return node_para.issubset(my_para)
        

class Script:
    
    def __init__(self, path, module):
        self.path = path
        self.module = module
        
        
    def __str__(self):
        s = 'module "%s"@%s' % (self.module, self.path)
        return s
        
        
    def __repr__(self):
        return str(self)
    
    
    def run(self, msg, ctxt_mngr):
        log.msg(self.path)
        mdl = imp.load_source(self.module, self.path)
        result = mdl.run(msg, ctxt_mngr)
        return result

