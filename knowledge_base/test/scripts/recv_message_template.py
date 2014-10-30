
def run(msg, ctxts):
    #1. fetch context
    ctxt_1 = ctxts.get_context('some context',
                               ('p1', 'v1'), ('p2', 'v2'))
    ctxt_2 = ctxts.get_context('some other context',
                               ('p1', 'v1'), ('p2', 'v2'))
    
    #2. update context
    ctxt_1['x'] = 'some value 1'
    ctxt_2['y'] = 'some value 2'
    
    #3. compose response
    buff = []
    rsp = {'interface': 'some interface',
           'direction': 'some direction',}
    rsp['layer1'] = {'protocol': 'some protocol',
                     'message': 'some message'}
    rsp['layer1']['parameters'] = {'p1': 'some value',
                                   'p2': 'some value'}
    buff.append(rsp)
    rsp = {'interface': 'some interface',
           'direction': 'some direction',}
    rsp['layer1'] = {'protocol': 'some protocol',
                     'message': 'some message'}
    rsp['layer1']['parameters'] = {'p1': 'some value',
                                   'p2': 'some value'}
    buff.append(rsp)
    
    
    #4. create context
    ctxt_new_1 = ctxts.create_context('some context',
                                      p1=msg['layer3']['parameters']['some_para'],
                                      p2='v2')
    ctxt_new_2 = ctxts.create_context('some context',
                                      [('x', msg['layer3']['parameters']['some_para']),
                                       ('y', 'v2')])
    
    #5. delete context
    ctxt_to_be_del = ctxts.get_context('some context')
    ctxts.delete_context(ctxt_to_be_del)
    
    #6. return message
    return [msg]
