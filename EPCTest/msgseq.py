from utils import keyword, logger
from checklist import CheckList
from dispatcher import Dispatcher
import re

class MessageSequence:
    
    def __init__(self, topo):
        self._topology = topo
#         self._address = addr
#         self._port = int(port)
        self.msg_buff = None
        self._on_recv_found = False
        self.trigger = None
        
        p_name = r'([_a-zA-Z]\w*)'
        p_digits = r'(\d+)'
        p_var = r'(@%s)' % p_name
        p_string = r'("[^"]*")'
        p_eq = '\s*:\s*'
        
        p_pat = (p_name + p_eq + p_digits + '|' +
                         p_name + p_eq + p_string + '|' +
                         p_name + p_eq + p_var)
        
        self.para_pat = re.compile(p_pat)
        
        
    @keyword
    def send(self, msg, src, dst, paras='', paras_to_save='', delay=0):
        """
        Composing a message sending from simulator to dut.
        """
        
        if self.msg_buff is None:
            self._init_msg_buff()
        
        ne_link = self._topology.link(src, dst)

        if ne_link is None:
            logger.warn('No link between NEs to send message. '
                        '%s->%s: %s' % (src, dst, msg))
            return
        
        if not (ne_link.simulator == src and ne_link.dut == dst):
            logger.warn('Not a message from simulator to dut. '
                        '%s->%s: %s' % (src, dst, msg))
            return
            
        msg_str = self._compose_send(msg, paras, paras_to_save, delay)
        msg_buff = self._get_msg_buff(ne_link.names[0])
        msg_buff.append(msg_str)
        logger.info('"send %s" added to buffer of %s' %
                    (msg, ne_link.names[0]))
        
        if self.trigger is None and not self._on_recv_found:
            self.trigger = msg_buff.ne_name
            logger.info('Found trigger: %s' % src)
        
        
    @keyword
    def on_recieve(self, msg, src, dst, paras='', paras_to_save='', index=0):
        """
        The start of the action to a message recieved.
        
        This keyword starts a sub-procedure used as the reaction to a message
        recieved. The sub-procedure ended when next on_recieve met.
        
        The action set to certain message is only valid for one test case.
        """
        
        if self.msg_buff is None:
            self._init_msg_buff()
        
        ne_link = self._topology.link(src, dst)

        if ne_link is None:
            logger.warn('No link between NEs to send message. '
                        '%s<-%s: %s' % (dst, src, msg))
            return
        
        if not (ne_link.simulator == dst and
                ne_link.dut == src):
            logger.warn('Not a message from dut to simulator. '
                        '%s<-%s: %s' % (dst, src, msg))
            return
            
        msg_str = self._compose_on_recv(msg, paras, paras_to_save, index)
        msg_buff = self._get_msg_buff(ne_link.names[0])
        msg_buff.append(msg_str)
        logger.info('"send %s" added to buffer of %s' %
                    (msg, ne_link.names[0]))
    
        
    @keyword
    def finish(self, link):
        """
        The stop point of test case. At least one stop point must be exist
        in each test case.
        
        This keyword represents the end of the test case. Test tool will send
        stop signal to dispatcher then the dispatcher will notify all other
        tools to stop. After all tools stopped, the dispatcher will send test
        reports to the verification module to be verified.
        """
        
        if self.msg_buff is None:
            self._init_msg_buff()
        
        src, dst = link.split('--')
        
        ne_link = self._topology.link(src, dst)

        if ne_link is None:
            logger.warn('No link between NEs to send message. '
                        '%s--%s: Stop' % (src, dst))
            return

        if ((not (ne_link.simulator == src and ne_link.dut == dst)) and
            (not (ne_link.simulator == dst and ne_link.dut == src))):
            logger.warn('Finish on unassigned link. '
                        '%s--%s: Stop' % (src, dst))
            return

        msg_str = self._compose_finish()
        msg_buff = self._get_msg_buff(ne_link.names[0])
        msg_buff.append(msg_str)
        
        logger.info('"Finish" added to buffer of %s' %
                    ne_link.names[0])
        
        
    @keyword
    def event(self, src_link, dst_link, event):
        """
        An event must be sent when this keyword is executed by test tools.
        
        The event must be between simulators. Self-loop event is allowed and
        in this situation, 'recieve event' is executed before 'send event'. 
        """

        if self.msg_buff is None:
            self._init_msg_buff()
            
        src_node1, src_node2 = src_link.split('--')
        dst_node1, dst_node2 = dst_link.split('--')
        
        src_ne_link = self._topology.link(src_node1, src_node2)
        dst_ne_link = self._topology.link(dst_node1, dst_node2)
        
        if src_ne_link is None or dst_ne_link is None:
            logger.warn('No link between NEs to send message. '
                        '%s -> %s: Event %s' % (src_link, dst_link, event))
            return
            
        
        if ((not (src_ne_link.simulator == src_node1 and
                  src_ne_link.dut == src_node2)) and
            (not (src_ne_link.simulator == src_node2 and
                  src_ne_link.dut == src_node1))):
            logger.warn('Event on unassigned link. '
                        '%s -> %s: Event %s' % (src_link, dst_link, event))
            return
        
        if ((not (dst_ne_link.simulator == dst_node1 and
                  dst_ne_link.dut == dst_node2)) and
            (not (dst_ne_link.simulator == dst_node2 and
                  dst_ne_link.dut == dst_node1))):
            logger.warn('Event on unassigned link. '
                        '%s %s: Event %s' % (src_link, dst_link, event))
            return
        
        send_msg_str = self._compose_send_event(event)
        recv_msg_str = self._compose_recv_event(src_ne_link.ne_name, event)
        
        send_msg_buff = self._get_msg_buff(src_ne_link.names[0])
        recv_msg_buff = self._get_msg_buff(dst_ne_link.names[0])
        
        send_msg_buff.append(send_msg_str)
        recv_msg_buff.append(recv_msg_str)
        
        logger.info('"send event %s" added to buffer %s' % 
                    (event, src_ne_link.names[0]))
        logger.info('"recieve event %s" added to buffer %s' % 
                    (event, dst_ne_link.names[0]))
        
    
    @keyword
    def wait(self, link, tm):
        """
        Wait for certain seconds specified by 'tm'.
        
        'tm' is the time to be waited in millisecond.
        """
        
        if self.msg_buff is None:
            self._init_msg_buff()
        
        src, dst = link.split('--')
        ne_link = self._topology.link(src, dst)
        
        if ne_link is None:
            logger.warn('No link between NEs to send message. '
                        '%s->%s: Wait' % (src, dst))
            return

        if ((not (ne_link.simulator == src and ne_link.dut == dst)) and
            (not (ne_link.simulator == dst and ne_link.dut == src))):
            logger.warn('Stop on unassigned link. '
                        '%s-%s: Stop' % (src, dst))
            return

        msg_str = self._compose_wait(tm)
        msg_buff = self._get_msg_buff(ne_link.names[0])
        msg_buff.append(msg_str)

        logger.info('"wait %s" added to buffer %s' %
                    (tm, ne_link.names[0]))
        
    
    @keyword
    def retrieve_data(self, link,
                      result, operation, paras='',
                      start_message='', end_message=''):
        
        if self.msg_buff is None:
            self._init_msg_buff()
        
        src, dst = link.split('--')
        
        ne_link = self._topology.link(src, dst)

        if ne_link is None:
            logger.warn('No link between NEs to send message. '
                        '%s--%s: Retrieve %s' % (src, dst, operation))
            return

        if ((not (ne_link.simulator == src and ne_link.dut == dst)) and
            (not (ne_link.simulator == dst and ne_link.dut == src))):
            logger.warn('Retrieve data on unassigned link. '
                        '%s--%s: Retrieve %s' % (src, dst, operation))
            return

        msg_str = self._compose_retrieve_data(result, operation, paras,
                                              start_message, end_message)
        msg_buff = self._get_msg_buff(ne_link.names[0])
        msg_buff.append(msg_str)
        
        logger.info('"Retrieve" added to buffer of %s' %
                    ne_link.names[0])
    
       
    @keyword
    def check(self, expr, info=''):
        
        if self.msg_buff is None:
            self._init_msg_buff()
        
        self.chk_lst.check(expr, info)
        logger.info('"Check" added to check list')
        
        
    @keyword 
    def execute(self, timeout=0):
        #TODO: validate script
        logger.info('Send script to tools and starting to run...')
        buf = [{'type': 'send script',
                'office': m.ne_name,
                'script': m.buffer} for m in self.msg_buff]
        addresses = dict((m.ne_name, m.address) for m in self.msg_buff)
        name_map = dict((m.names, m.ne_name) for m in self.msg_buff)
        logger.info('Scripts: %s' % str(buf))
        logger.info('Addresses: %s' % addresses)
        dispatcher = Dispatcher(buf, self.trigger, addresses, name_map, timeout)
        report, var, e = dispatcher.run_scripts()
        logger.info('Test case complete, checking...')
        if e:
            self.chk_lst.exception(e)
        else:
            self.chk_lst.save_report(report)
            self.chk_lst.save_variable(var)
            self.chk_lst.start_check()
        
    
    def _init_msg_buff(self):
        """
        Initialize message buffer of simulators.
        
        A message buffer is attached to each node labeled to be simulator.
        """
        
        logger.info('Initializing message buffer...')
        self.msg_buff = [MessageBuffer(l) for l in self._topology
                         if l.simulator is not None]
        self.chk_lst = CheckList()
        logger.info('Message buffer for %s initialized.'
                    % ', '.join(m.names[0] for m in self.msg_buff))
        
        
    def _get_msg_buff(self, name):
        for m in self.msg_buff:
            if name in m.names:
                return m
            
    
    def _get_paras(self, para_str):
        if para_str == '':
            return []
        
        para_seg = self.para_pat.findall(para_str)
        if not para_seg:
            return None
        
        para_obj = []
        for para in para_seg:
            valid_para = [p for p in para if p!=''][:2]
            if valid_para[1].isdigit():
                valid_para[1] = int(valid_para[1])
            elif valid_para[1].startswith('"'):
                valid_para[1] = valid_para[1][1:-1]
            else:
                pass
            para_obj.append(valid_para)
        return para_obj
            
        
    def _compose_send(self, msg, paras, paras_to_save, delay):
        p = self._get_paras(paras)
        paras_obj = [{'name': n, 'value': v}
                     for n, v in p
                     if not (type(v) is str and v.startswith('@'))]
        paras_to_retrieve_obj = [{'name': n, 'var': v[1:]}
                                 for n, v in p
                                 if type(v) is str and v.startswith('@')]
        
        p = self._get_paras(paras_to_save)
        paras_to_save_obj = [{'name': n, 'var': v[1:]}
                                 for n, v in p]
        
        delay = int(delay)
        
        rslt = {'step': 'Send Message',
                'paras': paras_obj,
                'paras_to_save': paras_to_save_obj,
                'paras_to_retrieve': paras_to_retrieve_obj,
                'delay': delay}
        
        if msg.find(' ') == -1:
            rslt['message_alias'] = msg
        else:
            rslt['message_name'] = msg
            
        return rslt
        
    
    def _compose_on_recv(self, msg, paras, paras_to_save, index):
        p = self._get_paras(paras)
        paras_obj = [{'name': n, 'value': v}
                     for n, v in p
                     if not (type(v) is str and v.startswith('@'))]
        paras_to_retrieve_obj = [{'name': n, 'var': v[1:]}
                                 for n, v in p
                                 if type(v) is str and v.startswith('@')]
        
        p = self._get_paras(paras_to_save)
        paras_to_save_obj = [{'name': n, 'var': v[1:]}
                                 for n, v in p]
        
        index = int(index)
        
        rslt = {'step': 'Receive Message',
                'paras': paras_obj,
                'paras_to_save': paras_to_save_obj,
                'paras_to_retrieve': paras_to_retrieve_obj,
                'index': index}
        
        if msg.find(' ') == -1:
            rslt['message_alias'] = msg
        else:
            rslt['message_name'] = msg
            
        return rslt

    
    def _compose_finish(self):
        rslt = {'step': 'Finish'}
        return rslt
    
    
    def _compose_send_event(self, event):
        rslt = {'step': 'Send Event',
                'event': event}
        return rslt


    def _compose_recv_event(self, src, event):
        rslt = {'step': 'Receive Event',
                'source': src,
                'event': event}
        return rslt


    def _compose_wait(self, tm):
        rslt = {'step': 'Wait',
                'timer': tm}
        return rslt
    
    
    def _compose_retrieve_data(self, result, operation, paras,
                               start_message, end_message):
        p = self._get_paras(paras)
        paras_obj = [{'name': n, 'value': v} for n, v in p]
        
        p = self._get_paras(start_message)
        start_msg_obj = [{'name': n, 'value': v} for n, v in p]
        
        p = self._get_paras(end_message)
        end_msg_obj = [{'name': n, 'value': v} for n, v in p]
        
        rslt = {'step': 'Retrieve Data',
                'variable': result[1:],
                'operation': operation,
                'paras': paras_obj,
                'start_message': start_msg_obj,
                'end_message': end_msg_obj}
        
        return rslt
    
    
class MessageBuffer:
    
    def __init__(self, link):
        self.names = link.names
        self.address = link.ne_address
        self.ne_name = link.ne_name
        self.buffer = []
        
    def __iter__(self):
        return iter(self.buffer)
    
    
    def __getattr__(self, name):
        return getattr(self.buffer, name)
