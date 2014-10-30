"""
Some description.
"""

def run(msg, ctxts, system):
    #1. fetch context
    ctxt_1 = ctxts.get_context('some context',
                               ('p1', 'v1'), ('p2', 'v2'))
    ctxt_2 = ctxts.get_context('some other context',
                               ('p1', 'v1'), ('p2', 'v2'))
    
    #2. update context
    ctxt_1['x'] = 'some value 1'
    ctxt_2['y'] = 'some value 2'
    
    #3. set message parameter
    msg['layer1']['parameters']['some_para'] = 'some value'
    msg['layer3']['parameters']['some_para'] = 'some value'
    
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
