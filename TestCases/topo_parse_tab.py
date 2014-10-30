
# topo_parse_tab.py
# This file is automatically generated. Do not edit.
_tabversion = '3.2'

_lr_method = 'LALR'

_lr_signature = '\x01F\xc0\x95~\x9b\x89\xe2O\x88oo5p\xfd\t'
    
_lr_action_items = {'NODE':([0,2,3,5,7,8,10,14,15,16,],[2,-3,2,10,-7,-4,-5,-8,-9,-6,]),',':([7,15,],[11,-9,]),'LITERAL':([4,11,12,13,],[9,9,15,9,]),'LINK':([2,],[5,]),':':([2,10,],[4,13,]),'=':([9,],[12,]),'$end':([1,2,3,6,7,8,10,14,15,16,],[0,-3,-1,-2,-7,-4,-5,-8,-9,-6,]),}

_lr_action = { }
for _k, _v in _lr_action_items.items():
   for _x,_y in zip(_v[0],_v[1]):
      if not _x in _lr_action:  _lr_action[_x] = { }
      _lr_action[_x][_k] = _y
del _lr_action_items

_lr_goto_items = {'stmt_list':([0,3,],[1,6,]),'attr_list':([4,11,13,],[8,14,16,]),'stmt':([0,3,],[3,3,]),'attr':([4,11,13,],[7,7,7,]),}

_lr_goto = { }
for _k, _v in _lr_goto_items.items():
   for _x,_y in zip(_v[0],_v[1]):
       if not _x in _lr_goto: _lr_goto[_x] = { }
       _lr_goto[_x][_k] = _y
del _lr_goto_items
_lr_productions = [
  ("S' -> stmt_list","S'",1,None,None,None),
  ('stmt_list -> stmt','stmt_list',1,'p_stmt_list_1st','E:\\eclipse_prj\\EPC_Service_Demo_3\\EPCTest\\topology.py',184),
  ('stmt_list -> stmt stmt_list','stmt_list',2,'p_stmt_list','E:\\eclipse_prj\\EPC_Service_Demo_3\\EPCTest\\topology.py',188),
  ('stmt -> NODE','stmt',1,'p_stmt_node','E:\\eclipse_prj\\EPC_Service_Demo_3\\EPCTest\\topology.py',192),
  ('stmt -> NODE : attr_list','stmt',3,'p_stmt_node_with_attr','E:\\eclipse_prj\\EPC_Service_Demo_3\\EPCTest\\topology.py',200),
  ('stmt -> NODE LINK NODE','stmt',3,'p_stmt_link','E:\\eclipse_prj\\EPC_Service_Demo_3\\EPCTest\\topology.py',208),
  ('stmt -> NODE LINK NODE : attr_list','stmt',5,'p_stmt_link_with_attr','E:\\eclipse_prj\\EPC_Service_Demo_3\\EPCTest\\topology.py',224),
  ('attr_list -> attr','attr_list',1,'p_attr_list_1st','E:\\eclipse_prj\\EPC_Service_Demo_3\\EPCTest\\topology.py',241),
  ('attr_list -> attr , attr_list','attr_list',3,'p_attr_list','E:\\eclipse_prj\\EPC_Service_Demo_3\\EPCTest\\topology.py',246),
  ('attr -> LITERAL = LITERAL','attr',3,'p_attr','E:\\eclipse_prj\\EPC_Service_Demo_3\\EPCTest\\topology.py',252),
]