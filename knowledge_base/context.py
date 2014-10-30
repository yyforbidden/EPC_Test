import os
from twisted.python import log

class ContextError(Exception):
    pass


class ContextManager:
        
    
    def __init__(self, path):
        self._contexts = []
        self._indexes = {}
        self._load_index_of_context(path)
        self._timeline = dict.fromkeys(self._indexes, [])
    

    # context id
    _current_id = 0

    @classmethod
    def _id(self):
        # generate context id 
        i = self._current_id
        self._current_id += 1
        if self._current_id > 2**32:
            self._current_id = 0
        return i
        
        
    def __str__(self):
        contexts = str(self._contexts)
        indexes = str(self._indexes)
        s = 'ContextManager(\n\tcontexts=%s\n\tindexes=%s)\n' % (contexts, indexes)
        return s
    
    
    def __repr__(self):
        return str(self)
    
        
    def _load_index_of_context(self, path):
        for base, _, files in os.walk(path):
            for fname in files:
                if not fname.endswith('.context'):
                    continue
                fullname = os.path.join(base, fname)
                lines = (l.strip() for l in open(fullname))
                lines = [l for l in lines if l]
                lines.reverse()
                keys = []
                for l in lines:
                    if l.startswith('[') and l.endswith(']'):
                        context = l[1:-1]
                        self._indexes[context] = IndexList(context, keys)
                        keys = []
                    else:
                        keys.append(tuple(l.split()))


    def create_context(self, t, **paras):
        log.msg('creating context, type=%s, paras=%s.' % (t, str(paras)))
        i = self._id()
        c = Context(t, i, **paras)
        self._contexts.append(c)
        self._indexes[t].insert_index(c)
        self._timeline[t].append(c)
        log.msg('context created.')
        return c
        
        
    def get_context(self, t, *paras):
        log.msg('finding context, type=%s, paras=%s' % (t, str(paras)))
        
        if not paras:
            # return last created context if no parameter is specified
            if self._timeline[t]:
                ctxt = self._timeline[t][-1]
            else:
                ctxt = None
        else:
            il = self._indexes[t]
            ctxt = il.get_context(*paras)
            
        log.msg('found context: %s' % str(ctxt))
        return ctxt
        

    def destroy_context(self, ctxt):
        log.msg('destroying context: %s' % str(ctxt))
        self._contexts.remove(ctxt)
        self._timeline[ctxt.type].remove(ctxt)
        for _, (i, v) in ctxt.indexes.items():
            if not v:
                continue
            i.delete_index(v)
        log.msg('context destroyed.')
        
        
    def clear_test(self):
        ctxt_to_destroy = self._contexts[:]
        for c in ctxt_to_destroy:
            self.destroy_context(c)
            

class IndexList:
    
    """
    An IndexList contains all possible indexes of a certain context type.
    """
    
    def __init__(self, ctxt_type, keys):
        self._context_type = ctxt_type
        self._keys = keys
        self._indexes = {}
        
        # Initialize index table
        self._indexes = dict((k, Index(self._context_type, k)) 
                              for k in self._keys)
            
            
    def __str__(self):
        tp = 'context_type=%s' % self._context_type
        key = 'key=%s' % str(self._keys)
        index = 'index=%s' % str(self._indexes)
        data = '\n\t'.join((tp, key, index))
        s = '\nIndexList(\n\t%s)\n' % data
        return s
    
    
    def __repr__(self):
        return str(self)
            
            
    def get_context(self, *paras):
        log.msg('finding context...')
        if not paras:
            log.msg('no parameters given, assuming using last created context')
            ctxt = self._timeline[-1]
        else:
            key, value = zip(*paras)
            try:
                ctxt = self._indexes[key].get_context(value)
            except KeyError:
                log.msg('cannot find context by given keys.')
                ctxt = None
        return ctxt


    def insert_index(self, ctxt):
        log.msg('inserting index and context...')
        if ctxt.type != self._context_type:
            log.msg('context type mismatch.')
            return
        
        # find all matching indexes in the context
        match = [k for k in self._keys
                 if set(k).issubset(set(ctxt.keys()))]
                
        if not match:
            log.msg('no matching keys found.')
            return
                
        # initialize indexes in a context.
        # all index methods must be added to the context
        # The actural value will be recorded if the attribute of the context
        # exist. Or 'None' will be recorded to the potential index.
        for k in self._keys:
            log.msg('inserting index to context: %s' % str(k))
            try:
                v = tuple(ctxt[i] for i in k)
            except KeyError:
                log.msg('context key not exist')
                v = None
            log.msg('value of the key in the context: %s' % str(v))
            ctxt.indexes[k] = (self._indexes[k], v)

        # insert each matching index
        for k in match:
            log.msg('inserting context into index %s' % str(k))
            i = self._indexes[k]
            i.insert_index(ctxt)
        
        
class Index:
    
    """
    An index contains all contexts matching index parameters.
    """
    
    def __init__(self, ctxt_type, key):
        self._context_type = ctxt_type
        self._key = key
        self._indexes = {}
        
    
    def __str__(self):
        tp = 'context_type=%s' % self._context_type
        key = 'key=%s' % str(self._key)
        index = 'index=%s' % str(self._indexes)
        data = '\n\t'.join((tp, key, index))
        s = '\nIndex(\n\t%s)\n' % data
        return s
    
    
    def __repr__(self):
        return str(self)
            
        
    def get_context(self, index):
        ctxt = self._indexes.get(index)
        return ctxt
    
    
    def insert_index(self, ctxt):
        if ctxt.type != self._context_type:
            return
        
        # use parameter value as key to store the matching context
        try:
            i = tuple(ctxt[k] for k in self._key)
        except KeyError:
            return
        self._indexes[i] = ctxt
        
        # the context should update its index as well
        # if a new attribute is added to a context, the index will change the
        # value from None to what it is.
        # If an attribute is changed, the new value will replace the old one.
        ctxt.indexes[self._key] = (self, i)
        
        
    def update_index(self, old_index, ctxt):
        if old_index in self._indexes:
            self.delete_index(old_index)
        self.insert_index(ctxt)
        
        
    def delete_index(self, v):
        self._indexes.pop(v)
        
        
    def delete_all_index(self):
        self._indexes = {}
                
                
class Context(dict):
    
    """
    A context contains all user concerned parameters.
    """

    def __init__(self, tp, id_, *args, **kargs):
        dict.__init__(self, *args, **kargs)
        self.type = tp
        self.indexes = {}
        self['context_id'] = id_
        
        
    def __setitem__(self, name, value):
        # 1. first update the value of the parameter
        dict.__setitem__(self, name, value)

        # 2. update indexes which is refered by the modified parameter.
        # The index in the context is a dictionary structured as {k: (i, v)}
        # 'k' means the index parameter name,
        # 'i' means the index object itself
        # 'v' means the parameter value refered by the index parameter.
        # 'v' is None if the parameter does not exist in the context.
        for k, (i, v) in self.indexes.items():
            if name in k:
                i.update_index(v, self)

