from utils import logger
import threading
import socket
import json
import select
import Queue
import struct
import time


class Dispatcher:
    
    def __init__(self, scripts, trigger, addresses, name_map, timeout):
        self._scripts = scripts
        self._trigger = trigger
        self._addresses = addresses
        self._name_map = name_map
        self._timeout = timeout
        self._finished = False
        self._script_cnt = len(self._scripts)
        
        self._state = 'idle'
        self._script_sent_cnt = 0
        self._script_start_cnt = 0
        self._stopped_tools = set()

        self._main_queue = Queue.Queue()
        self._start_timer_handler()
        # Buffer events & vars before all tools started
        self._event_buffer = []
        self._var_buffer = []
        
        # Result of the execution of test
        self.error = None
        self.report = {}
        self.vars = {}
        
        
    def _find_real_ne_name(self, ne):
        for n, rn in self._name_map.items():
            if ne in n:
                return rn
            
    def _find_ne_name(self, real_ne):
        for n, rn in self._name_map.items():
            if rn == real_ne:
                return n
        
        
    def _start_timer_handler(self):
        self._timer_queue = Queue.Queue()
        tm = Timer(0.01, self._timer_queue, self._main_queue)
        self._timer_handler = threading.Thread(target=tm.start)
        self._timer_handler.daemon = True
        self._timer_handler.start()
        logger.info('Timer handler started')
        
        
    def _start_timer(self, name, tm):
        self._timer_queue.put(('start', name, tm))
        logger.info('Timer %s(%f) started' % (name, tm))
        
        
    def _kill_timer(self, name):
        self._timer_queue.put(('kill', name))
        logger.info('Timer %s killed' % name)
        
        
    def _connect_to_tools(self):
        addrs = set(self._addresses.values())
        self._socks = dict.fromkeys(addrs, None)
        self._recv_buff = dict.fromkeys(addrs, '')

        self._sock_queue = Queue.Queue()

        for addr in addrs:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            
            try:
                logger.info('Connecting to tool at %s...' % str(addr))
                sock.connect(addr)
            except socket.error:
                logger.warn('Cannot connect to tool %s' % str(addr))
                self._report_link_broken(addr)
            
            self._socks[addr] = sock
            self._recv_buff[addr] = ''
        logger.info('All tools connected.')
    
        # Sender & Reciever live in seperate threads.
        # Communicate with the main thread by using queues
        self.sender = threading.Thread(target=self._send_handler)
        self.reciever = threading.Thread(target=self._receive_handler)
        self.sender.daemon = True       # thread dies after main thread exit
        self.reciever.daemon = True     # thread dies after main thread exit
        self.sender.start()
        self.reciever.start()
        
    
    def _close_connection(self):
        for addr, s in self._socks.items():
            logger.info('Tool at %s closed.' % str(addr))
            s.close()
    
    
    def _send(self, addr, data):
        # send() in the main thread
        # put data in the queue for the sub-thread to read
        data = json.dumps(data)
        self._sock_queue.put((addr, data))
    
    
    def _receive(self):
        # receive() in the main thread
        # get data from the queue
        # this method will block on reading the queue
        data = self._main_queue.get()
        return data
    
    
    def _send_handler(self):
        # the send thread which operates the socket
        logger.info('Sender started.')
        while True:
            data = self._sock_queue.get()
            sock = self._socks[data[0]]
            l = struct.pack('!I', len(data[1]))
            try:
                sock.send(l + data[1])
            except socket.error:
                # put Exception directly to the receive_queue
                data = self._report_link_broken(data[0])
    
    
    def _receive_handler(self):
        # the receive thread which operates the socket
        # 1. poll all socket connect to read.
        # 2. get data from the read ready socket.
        # 3. add data to the string buffer of the socket
        # 4. try to dissect all json object from the string
        # 5. put json object into receive queue
        # 6. do this until the data read is exhausted
        # 7. put Exception in recieve queue if:
        #    1) receive of empty data, this means peer shutdown normally;
        #    2) recv raises an error. 
        logger.info('Receiver started.')
        while True:
            try:
                socks, _, _ = select.select(self._socks.values(), [], [])
            except socket.error:
#                 self._close_connection()
                data = self._report_link_broken(self._socks.keys())
                break
            
            for s in socks:
                addr = [a for a, so in self._socks.items() if so==s][0]
                try:
                    data = s.recv(1024)
                    addr = s.getpeername()
                except socket.error:
                    logger.info('Link broken')
                    data = self._report_link_broken(addr)
                    break
                
                # connection closed normally by peer
                if not data:
                    logger.info('Link closed by peer')
                    data = self._report_link_broken(addr)
                    break
                    
                    
                buff_str = self._recv_buff[addr] + data
                
                # decode json object until not enough data
                if len(buff_str) <= 4:
                    logger.info('Not enough data to unpack: data=%s' % buff_str)
                    
                while len(buff_str) > 4:
                    l = struct.unpack('!I', buff_str[:4])[0]
                    # incomplete segment of data
                    if len(buff_str)-4 < l:
                        logger.info('Not enough data to unpack: len=%d, data=%s' %
                                    (l, buff_str))
                        break
                    json_str, buff_str = buff_str[4:l+4], buff_str[l+4:]
                    json_obj = json.loads(json_str)
                    self._main_queue.put(json_obj)
                self._recv_buff[addr] = buff_str
 

    def _on_script_received(self, msg):
        ne_name = msg['office']
        state = self._state
        if state == 'wait_script_received':
            self._script_sent_cnt += 1
            logger.info('%d scripts received by tools.' % self._script_sent_cnt)
            if self._script_sent_cnt == self._script_cnt:
                logger.info('All scriptd sent.')
                self._kill_timer(self._state)
                self._send_start()
                self._state = 'wait_started'
                self._start_timer(self._state, 1)
                
        elif state == 'wait_report':
            # SCRIPT RECEIVED is on the way while some tool issue stop or exception
            logger.info('Receive script_received on WAIT_REPORT, skipping...')
            pass
        else:
            logger.warn('SCRIPT RECEIVED on unexpected state: %s' % state)
            self._report_unexpected_message(ne_name)
    
    
    def _on_started(self, msg):
        ne_name = msg['office']
        state = self._state
        if state == 'wait_started':
            self._script_start_cnt += 1
            logger.info('%d scripts started by tools.' % self._script_start_cnt)
            if self._script_start_cnt == self._script_cnt:
                logger.info('All scriptd started.')
                logger.info('Sending buffered events and variables...')
                self._kill_timer('wait_started')
                self._send_cached_events()
                self._send_cached_vars()
                self._state = 'started'
        elif state == 'wait_report':
            # STARTED is on the way while some tool issue stop or exception
            logger.info('Receive started on WAIT_REPORT, skipping...')
            pass
        else:
            logger.warn('STARTED on unexpected state: %s' % state)
            self._report_unexpected_message(ne_name)
            
            
    def _on_event(self, msg):
        ne_name = msg['office']
        state = self._state
        if state == 'started':
            logger.info('Received event on STARTED state, dispatching...')
            self._event_buffer.append(msg)
            self._send_cached_events()
        elif state == 'wait_started':
            logger.info('Received event on WAIT_STARTED state, buffering...')
            self._event_buffer.append(msg)
        elif state == 'wait_report':
            # EVENT is on the way while some tool issue stop or exception
            logger.info('Receive event on WAIT_REPORT, skipping...')
            pass
        else:
            logger.warn('EVENT on unexpected state: %s' % state)
            self._report_unexpected_message(ne_name)
            
    
    def _on_variable(self, msg):
        ne_name = msg['office']
        state = self._state
        if state == 'started':
            logger.info('Received variable on STARTED state, dispatching...')
            self._var_buffer.append(msg)
            self._send_cached_vars()
        elif state == 'wait_started':
            logger.info('Received variable on WAIT_STARTED state, buffering...')
            self._var_buffer.append(msg)
        elif state == 'wait_report':
            # VARIABLE is on the way while some tool issue stop or exception
            logger.info('Receive variable on WAIT_REPORT, skipping...')
            pass
        else:
            logger.warn('VARIABLE on unexpected state: %s' % state)
            self._report_unexpected_message(ne_name)
            
            
    def _on_report(self, msg):
        ne_name = msg['office']
        state = self._state
        
        rpt = dict((r['name'], r['value']) for r in msg['report'])
        self.report.update(rpt)

        self._stopped_tools.add(ne_name)
        
        if state == 'started':
            logger.info('Receive report on STARTED state')

            if self._stopped_tools == set(self._addresses.keys()):
                logger.info('All report received, test finished.')
                self._kill_timer('wait_report')
                self._state = 'finished'
            else:
                self._send_stop()
                logger.info('Waiting for more report...')
                self._state = 'wait_report'
                self._start_timer(self._state, 1)
            
        elif state == 'wait_started':
            logger.info('Receive report on WAIT_STARTED state')
            if self._stopped_tools == set(self._addresses.keys()):
                logger.info('All report received, test finished.')
                self._kill_timer('wait_report')
                self._state = 'finished'
            else:
                self._send_stop()
                logger.info('Waiting for more report...')
                self._state = 'wait_report'
                
        elif state == 'wait_report':
            # some tool stopped by RF
            logger.info('Receive report on WAIT_REPORT state, saving report...')
            if self._stopped_tools == set(self._addresses.keys()):
                logger.info('All report received, test finished.')
                self._kill_timer('wait_report')
                self._state = 'finished'
                
        else:
            logger.warn('REPORT on unexpected state: %s' % state)
            self._report_unexpected_message(ne_name)
            return
            
            
    def _on_exception(self, msg):
        #TODO: reconsider how to process link broken 
        ne_names = msg['office'].split(',')
        self.error = msg['reason']
        
        for ne in ne_names:
            self._stopped_tools.add(ne)
            
        logger.info('Receive exception "%s" on state %s.' %
                    (msg['reason'], self._state))        
        self._send_stop()
        self._kill_timer('wait_report')
        self._state = 'finished'
        
            
    def _on_timer(self, msg):
        tm = msg['name']
        logger.info('Receive timer %s timeout on state %s' % (tm, self._state))
        
        if tm == 'execution' or self._state == tm:
            self._report_timeout(tm)
        else:
            logger.info('Unknown timer met.')
            self._report_timeout(tm)
        
        
    def _on_unknown_message(self, msg):
        ne_name = msg['office']
        logger.info('Receive unknown message %s, raising exception...' % msg['type'])
        self._report_unexpected_message(ne_name)
        
        
    def _send_script(self):
        for s in self._scripts:
            ne_name = s['office']
            logger.info('Sending script to %s...' % ne_name)
            addr = self._addresses[ne_name]
            self._send(addr, s)

        self._state = 'wait_script_received'
        self._start_timer(self._state, 1)
        self._script_sent_cnt = 0


    def _send_start(self):
        start = {"type": "start",
                 "office": None,
                 "timer": self._timeout}
        
        # start all tools before Trigger starting
        for ne, addr in self._addresses.items():
            # skip the trigger
            if ne == self._trigger:
                continue
            logger.info('Sending START to %s...' % ne)
            start['office'] = ne
            self._send(addr, start)
        
        # start the Trigger after all other tools started
        logger.info('Triggering: sending START to %s...' % self._trigger)
        trigger_addr = self._addresses[self._trigger]
        start['office'] = self._trigger
        self._send(trigger_addr, start)
        
        self._script_start_cnt = 0
        
        
    def _send_event(self, msg):
        msg['source'] = msg['office']
        for ne, addr in self._addresses.items():
            # need not to send to the source
            if ne == msg['source']:
                continue
            logger.info('Sending EVENT to %s...' % ne)
            msg['office'] = ne
            self._send(addr, msg)
            
            
    def _send_variable(self, msg):
        src = msg['office']
        for ne, addr in self._addresses.items():
            # need not to send to the source
            if ne == src:
                continue
            logger.info('Sending VARIABLE to %s...' % ne)
            msg['office'] = ne
            self._send(addr, msg)
            
            
    def _send_stop(self):
        for ne, addr in self._addresses.items():
            msg = {'type': 'stop',
                   'office': ne}
            if ne not in self._stopped_tools:
                logger.info('Sending STOP to %s...' % ne)
                self._send(addr, msg)
        

    def _send_cached_events(self):
        for e in self._event_buffer:
            self._send_event(e)
        self._event_buffer = []
        
        
    def _send_cached_vars(self):
        for v in self._var_buffer:
            self._send_variable(v)
            vars_ = dict((item['name'], item['value']) for item in v['variable'])
            self.vars.update(vars_)
        self._var_buffer = []
            

    def _report_link_broken(self, addresses):
        if type(addresses) is tuple:
            addresses = [addresses]
        nes = ''
        for addr in addresses:
            nes += ','.join(ne for ne, a in self._addresses.items() if a==addr)
        e = {"type": "Exception",
             "office": nes,
             "code": 3002,
             "reason": "Link to test tools broken"}
        self._main_queue.put(e)
        
        
    def _report_unexpected_message(self, ne):
        e = {'type': 'exception',
             'office': ne,
             'code': 3001,
             'reason': 'Unexpected message received'}
        self._main_queue.put(e)
        
        
    def _report_timeout(self, tm):
        e = {'type': 'exception',
             'office': '',
             'code': 3003,
             'reason': '%s time out' % tm}
        self._main_queue.put(e)
        
 
    def _main_loop(self):
        # handle all message from tools
        # each message is processed in a unique handler
        fsm = {'script received': self._on_script_received,
               'started': self._on_started,
               'event': self._on_event,
               'variable': self._on_variable,
               'report': self._on_report,
               'exception': self._on_exception,
               'timer': self._on_timer,
               'unknown message': self._on_unknown_message}
        
        while not self._state == 'finished':
            msg = self._receive()
            msg_type = msg['type'].lower()
            ne_name = msg['office']
            logger.info('Receive %s from NE %s at state %s' %
                        (msg['type'], ne_name, self._state))
            handler = fsm.get(msg_type, fsm['unknown message'])
            handler(msg)
    
    
    def run_scripts(self):
        st = time.clock()
        self._connect_to_tools()
        if self._timeout != 0:
            self._start_timer('execution', self._timeout)
        self._send_script()
        self._main_loop()
        if self._timeout != 0:
            self._kill_timer('execution')
        self._close_connection()
        et = time.clock()
        logger.info('execution time %f' % (et-st))
        return self.report, self.vars, self.error


class Timer:
    
    def __init__(self, r, in_q, out_q):
        self._resolution = r
        self._in_q = in_q
        self._out_q = out_q
        self._timer_pool = {}
        
    
    def start(self):
        while True:
            time.sleep(self._resolution)
            now = time.clock()
            self._check_timer(now)
                    
            try:
                cmd = self._in_q.get(block=False)
            except Queue.Empty:
                continue
            else:
                if cmd[0] == 'start':
                    self._start_timer(cmd[1], cmd[2], now)
                elif cmd[0] == 'kill':
                    self._kill_timer(cmd[1])
                elif cmd[0] == 'end':
                    self._timer_pool = {}
                    break
                else:
                    pass
                
                
    def _start_timer(self, name, tm, now):
        self._timer_pool[name] = (now, tm)
        
        
    def _kill_timer(self, name):
        try:
            self._timer_pool.pop(name)
        except KeyError:
            pass
        

    def _check_timer(self, now):
        for n, (st, tm) in self._timer_pool.items():
            if now - st >= tm:
                tm_evt = {'type': 'timer',
                          'office': '',
                          'name': n}
                self._out_q.put(tm_evt)
                self._kill_timer(n)

            