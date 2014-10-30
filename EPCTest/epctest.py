from utils import logger
from topology import Topology
from msgseq import MessageSequence

class epctest:
    """
    The interface to low level keyword.
    All keywords are implemented as dynamic keywords
    Load keywords from modules in .service and TestManager
    """
    
    def __init__(self):
        """
        Create all needed objects and load keywords from them.
        Keyword meta data is available at start time, but they can not be
        called until topology is prepared.
        Use python style dynamic keyword to simplify the process.  
        """
        
        # All functional objects is created here
        self._topology = Topology()
        self._message_seq = MessageSequence(self._topology)

        # Keywords come from these objects.
        # If new keywords source is added, it must be added in this tuple
        # Keywords are bound methods.        
        self._kw_src = (self._topology,
                        self._message_seq)
        
        self._initialize_keywords()
        logger.info('Keywords found: %s' % str(self._keywords.keys()))
        
        
    def __getattr__(self, attr):
        """
        Python style dynamic keywords.
        
        __getattr__ cannot support unicode being used as keyword.
        Use common interface of dynamic keywords to implement unicode
        low-level keywords.
        """
        
        if attr in self._keywords:
            return self._keywords[attr]
        raise AttributeError, 'No such keyword: %s' % attr

    
    def get_keyword_names(self):
        return self._keywords.keys()

    def _initialize_keywords(self):
        self._keywords = {}
        
        # keywords can be recoganized by its attribute 'is_keyword'
        # it is set by the decorator 'keyword' in module 'utils'.
        for obj in self._kw_src:
            attrs = ((a, getattr(obj, a)) for a in dir(obj))
            kw = dict(a for a in attrs if getattr(a[1], 'is_keyword', False))
            self._keywords.update(kw)

