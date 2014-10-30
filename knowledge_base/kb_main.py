import optparse
import sys
from controller import Controller
from twisted.python import log

def parse_arg():
    usage = """
    -p, --port: port number, default to 10798(ascii('k')=107, ascii('b')=98)
    -s, --script: script path, default to '.\script'
    -c, --context: context path, default to '.\context'
    """
    
    parser = optparse.OptionParser(usage)
    h = "The port to listen on."
    parser.add_option('-p', '--port', type='int', help=h, default=10798)

    h = "The path of scripts"
    parser.add_option('-s', '--script', help=h, default=r'.\script')

    h = "The path of contexts"
    parser.add_option('-c', '--context', help=h, default=r'.\context')

    options, args = parser.parse_args()

    return options, args
    
    
def main():
    log.startLogging(sys.stdout)
    opt, _ = parse_arg()
    c = Controller(opt.port, opt.script, opt.context)
    c.run()
    
    
if __name__ == '__main__':
    main()
