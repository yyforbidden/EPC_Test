"""
How to send Attach Request by RNC to SGSN. 
"""

def run(msg, ctxts):
    #1. fetch context
    
    #2. update context
    
    #3. set message parameter
    msg.setdefault('layer1', {'protocol': 'SCCP',
                              'message': 'Connection Request',
                              'parameters': {}})
    msg.setdefault('layer2', {'protocol': 'RANAP',
                              'message': 'Initial UE',
                              'parameters': {}})
    msg['layer1']['parameters'].setdefault('sccp_id', '0')
    msg['layer3']['parameters'].setdefault('ti', '0')
    
    #4. create context
    user_ctxt = ctxts.create_context('user_context',
                                     imsi=msg['layer3']['parameters']['imsi'])
    nas_ctxt = ctxts.create_context('nas_transaction_context',
                                    ti=msg['layer3']['parameters']['ti'],
                                    user_ctxt_id=user_ctxt['context_id'])
    sccp_ctxt_ = ctxts.create_context('sccp_context',
                                      sccp_id=msg['layer1']['parameters']['sccp_id'],
                                      nas_ctxt_id=nas_ctxt['context_id'])
    
    #5. delete context
    
    #6. return message
    return msg
