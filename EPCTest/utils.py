def keyword(kw):
    """
    Decorator to mark a method as keyword.
    
    Add 'is_keyword' attribute to kw and set it to True.
    RF lib interface module will use this attribute to select keyword from
    different classes.
    """
    kw.is_keyword = True
    return kw

class dummy_logger:
    """
    Logger of debug information.
    
    If _debug is set to False the logger from robot.api will be used.
    """
    
    def info(self, s):
        print '[Info]: %s' % s
        
    def warn(self, s):
        print '[Warn]: %s' % s
        
    def trace(self, s):
        print '[Trace]: %s' % s
        
    def debug(self, s):
        print '[Debug]: %s' % s

_debug = True

if _debug:
    logger = dummy_logger()
else:
    from robot.api import logger    