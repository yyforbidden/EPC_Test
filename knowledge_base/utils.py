from twisted.python import log as LOG

def log(s):
    s = str(s)
    LOG.msg(s)