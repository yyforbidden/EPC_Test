"""
How to response to Authentication Request
"""

def run(msg, ctxts):
    #1. fetch context
    sccp_ctxt = ctxts.get_context('sccp_context',
                                  ('sccp_id', msg['layer1']['parameters']['sccp_id']))
    nas_ctxt = ctxts.get_context('nas_transaction_context',
                                 ('context_id', sccp_ctxt['nas_ctxt_id']))
    user_ctxt = ctxts.get_context('user_context',
                                  ('context_id', nas_ctxt['user_ctxt_id']))
    
    #2. update context
    
    #3. compose response
    buff = []
    
    rsp = {'interface': 'Iu-PS-Control',
           'direction': 'RNC->SGSN',}
    rsp['layer1'] = {'protocol': 'SCCP',
                     'message': 'DataIndication'}
    rsp['layer1']['parameters'] = {'sccp_id': sccp_ctxt['sccp_id']}
    rsp['layer2'] = {'protocol': 'RANAP',
                     'message': 'Data Transfer'}
    rsp['layer2']['parameters'] = {}
    rsp['layer3'] = {'protocol': 'NAS',
                     'message': 'Authentication Response'}
    rsp['layer3']['parameters'] = {'ti': nas_ctxt['ti'],
                                   'imsi': user_ctxt['imsi']}
    buff.append(rsp)

    rsp = {'interface': 'Iu-PS-Control',
           'direction': 'RNC->SGSN',}
    rsp['layer1'] = {'protocol': 'SCCP',
                     'message': 'DataIndication'}
    rsp['layer1']['parameters'] = {'sccp_id': sccp_ctxt['sccp_id']}
    rsp['layer2'] = {'protocol': 'RANAP',
                     'message': 'Data Transfer'}
    rsp['layer2']['parameters'] = {}
    rsp['layer3'] = {'protocol': 'NAS',
                     'message': 'Authentication Response'}
    rsp['layer3']['parameters'] = {'ti': nas_ctxt['ti'],
                                   'imsi': user_ctxt['imsi']}
    buff.append(rsp)
    
    #4. create context
    
    #5. delete context
    
    #6. return message
    return buff

