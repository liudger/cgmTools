"""
------------------------------------------
constraint_utils: cgm.core.lib.constraint_utils
Author: Josh Burton
email: jjburton@cgmonks.com
Website : http://www.cgmonks.com
------------------------------------------

Unified location for transform calls. metanode instances may by passed
"""

# From Python =============================================================
import copy
import re
import random

#>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)

# From Maya =============================================================
import maya.cmds as mc
from maya import mel
# From Red9 =============================================================

# From cgm ==============================================================
#CANNOT import Rigging
from cgm.core import cgm_General as cgmGeneral
from cgm.core.cgmPy import validateArgs as VALID
from cgm.core.lib import attribute_utils as ATTR
from cgm.core.lib import list_utils as LISTS
from cgm.core.lib import name_utils as NAMES

#returnObjectConstraints
#returnObjectDrivenConstraints
#returnConstraintTargets

_d_type_to_call = {'parentConstraint':mc.parentConstraint,
                    'orientConstraint':mc.orientConstraint,
                    'pointConstraint':mc.pointConstraint,
                    'scaleConstraint':mc.scaleConstraint,
                    'aimConstraint':mc.aimConstraint}

def get_constraintsTo(node=None, fullPath = False):
    """
    Get the constraints on a given node
    
    :parameters:
        node(str): node to query
        fullPath(bool): How you want list
    :returns
        list of constraints(list)
    """   
    _str_func = 'get_constraintsTo'
    
    node = VALID.mNodeString(node)
    
    _res = mc.listRelatives(node,type='constraint',fullPath=fullPath) or []
    _res = LISTS.get_noDuplicates(_res)
    if fullPath:
        return [NAMES.long(o) for o in _res]
    return _res

def get_constraintsFrom(node=None, fullPath = False):
    """
    Get the constraints a given node drives
    
    :parameters:
        node(str): node to query
        fullPath(bool): How you want list

    :returns
        list of constraints(list)
    """   
    _str_func = 'get_constraintsFrom'
    
    node = VALID.mNodeString(node)
    
    _res = mc.listConnections(node,source = False, destination = True,skipConversionNodes = True, type='constraint') or []

    _res = LISTS.get_noDuplicates(_res)
    #_l_objectConstraints = get(node)
    #for c in _l_objectConstraints:
        #if c in _res:_res.remove(c)
    
    if fullPath:
        return [NAMES.long(o) for o in _res]
    return _res

def get_targets(node=None, fullPath = True):
    """
    Get the constraints a given node drives
    
    :parameters:
        node(str): node to query

    :returns
        list of targets(list)
    """   
    _str_func = 'get_targets'
    
    node = VALID.mNodeString(node)
    _type = VALID.get_mayaType(node)

    _call = _d_type_to_call.get(_type,False)
    if not _call:
        raise ValueError,"|{0}| >> {1} not a known type of constraint. node: {2}".format(_str_func,_type,node)

    _res = _call(node,q=True,targetList=True)
    if fullPath:
        return [NAMES.long(o) for o in _res]
    return _res

def get_targetWeightsDict(node=None):
    """
    Get the constraints a given node drives
    
    :parameters:
        node(str): node to query

    :returns
        list of targets(list)
    """   
    _str_func = 'get_targetWeightsDict'
    
    node = VALID.mNodeString(node)
    
    _type = VALID.get_mayaType(node)
    _d = {}
    _l = []

    _call = _d_type_to_call.get(_type,False)
    if not _call:
        raise ValueError,"|{0}| >> {1} not a known type of constraint. node: {2}".format(_str_func,_type,node)

    aliasList = _call(node,q=True, weightAliasList=True)
    if aliasList:
        for o in aliasList:
            _d[o] = ATTR.get(node,o)

    return _d

def get_constraintsByDrivingObject(node=None, driver = None, fullPath = False):
    """
    Get a list of constraints driving a node by the drivers of those constraints.
    node 1 is driven by 3 constraints. 2 of those constraints use our driver as a target.
    Those 2 will be returned.
    
    :parameters:
        node(str): node to query
        driver(str): driver to check against
        fullPath(bool): How you want list
    :returns
        list of constraints(list)
    """   
    _str_func = 'get_constraintsTo'
    
    node = VALID.mNodeString(node)
    
    driver = VALID.mNodeString(driver)
    _long = NAMES.long(driver)   
    log.debug("|{0}| >> node: {1} | target: {2}".format(_str_func,node, _long))             
    
    l_constraints = get_constraintsTo(node,True)
    _res = False
    
    if l_constraints:
        _res = []
        for c in l_constraints:
            targets = get_targets(c,True)
            log.debug("|{0}| >> targets: {1}".format(_str_func, targets))              
            if _long in targets:
                log.debug("|{0}| >> match found: {1}".format(_str_func, c))                  
                _res.append(c)
    if _res and not fullPath:
        return [NAMES.short(o) for o in _res]
    return _res    
    
 
