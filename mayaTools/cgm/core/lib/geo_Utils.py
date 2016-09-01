#=================================================================================================================================================
#=================================================================================================================================================
#	geo - a part of cgmTools
#=================================================================================================================================================
#=================================================================================================================================================
# 
# DESCRIPTION:
#	Series of tools for working with geo
# 
# ARGUMENTS:
# 	Maya
# 
# AUTHOR:
# 	Josh Burton (under the supervision of python guru (and good friend) David Bokser) - jjburton@gmail.com
#	http://www.cgmonks.com
# 	Copyright 2011 CG Monks - All Rights Reserved.
# 
#=================================================================================================================================================

import maya.cmds as mc
import maya.mel as mel
import maya.OpenMaya as OM

from cgm.core import cgm_General as cgmGeneral
from cgm.core.cgmPy import validateArgs as cgmValid
from cgm.core.lib import selection_Utils as cgmSELECT
from cgm.core.cgmPy import OM_Utils as cgmOM
from cgm.lib import guiFactory
from cgm.lib import cgmMath
from cgm.core.lib import rayCaster as cgmRAYS
import re

from cgm.lib import search
from cgm.lib import distance
from cgm.lib import names
from cgm.lib import attributes

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)

def compare_area(sourceObj, targetList, shouldMatch = True):
    """
    Looks at the area of two pieces of geo. Most likely used for culling out unecessary blend targets that don't do anything.

    :parameters:
        sourceObj | Object to base comparison on
        targetList | List of objects to compare with
        shouldMatch | Mode with which to return data ('same' or not)

    :returns
        list of objects matching conditions
    """  
    _f_baseArea = mc.polyEvaluate(sourceObj, area = True)
    result = []
    for o in targetList:
        _f_area = mc.polyEvaluate(o, area = True)
        if shouldMatch:
            if cgmValid.isFloatEquivalent(_f_baseArea,_f_area):
                log.info("Match: {0}".format(o))
                result.append(o)
        else:
            if not cgmValid.isFloatEquivalent(_f_baseArea,_f_area):        
                log.info("Nonmatch: {0}".format(o))
                result.append(o)                     
    return result
    
def compare_points(sourceObj = None,targetList = None, shouldMatch = True):
    """
    Compares points of geo mesh. Most likely used for culling out unecessary blend targets that don't do anything.
    Can work of selection as well when no arguments are passed for source and target in a source then targets selection format.
    
    Thanks for the help: Travis Miller and Raffaele
    :parameters:
        sourceObj | Object to base comparison on
        targetList | List of objects to compare with
        shouldMatch | Mode with which to return data ('same' or not)

    :returns
        list of objects matching conditions
    """      
    result = []
    
    #Get our objects if we don't have them
    if sourceObj is None and targetList is None:
        _sel = mc.ls(sl=True)
        sourceObj = _sel[0]
        targetList = _sel[1:]
        
    #Maya OpenMaya 2.0 came in 2012 and is better but we want this to work in previous versions...
    if mel.eval('getApplicationVersionAsFloat') <2012:
        sel = OM.MSelectionList()#..make selection list
        for o in [sourceObj] + targetList:
            sel.add(o)#...add objs
    
        meshPath = OM.MDagPath()#...mesh path holder
        sel.getDagPath(0,meshPath)#...get source dag path
        fnMesh  = OM.MFnMesh(meshPath)#...fnMesh holder
        basePoints = OM.MFloatPointArray() #...data array
        fnMesh.getPoints(basePoints)#...get our data
        
        sel.remove(0)#...remove the source form our list
        
        morph = OM.MDagPath()#...dag path holder
        morphPoints = OM.MFloatPointArray()#...data array
        targets = OM.MSelectionList()#...new list for found matches
        
        for i in xrange(sel.length()):
            sel.getDagPath(i, morph)#...get the target
            fnMesh.setObject(morph)#...get it to our fnMesh obj
            fnMesh.getPoints(morphPoints)#...get comparing data
            _match = True                    
            for j in xrange(morphPoints.length()):
                if (morphPoints[j] - basePoints[j]).length() > 0.0001:#...if they're different   
                    _match = False
                    if not shouldMatch:
                        log.info("{0} doesn't match".format(morph))                                        
                        targets.add(morph)
                        break
                elif shouldMatch and j == (morphPoints.length()-1) and _match:#if we get to the end and they haven't found a mismatch
                    log.info("{0} match".format(morph))                                        
                    targets.add(morph)   
                    
        OM.MGlobal.setActiveSelectionList(targets)#select our targets
        return mc.ls(sl=True)#...return
    
    else:#We can use the new OpenMaya 2.0
        from maya.api import OpenMaya as OM2   
        
        sel = OM2.MSelectionList()#...make selection list
        for o in [sourceObj] + targetList:
            sel.add(o)#...add them to our lists        
            
        basePoints = OM2.MFnMesh(sel.getDagPath(0)).getPoints()#..base points data
        sel.remove(0)#...remove source obj
        
        count = sel.length()
        targets = OM2.MSelectionList()#...target selection list
        
        for i in xrange(count):
            comparable = OM2.MFnMesh(sel.getDagPath(i)).getPoints()#...target points data
            compareMesh = sel.getDagPath(i)#...dag path for target
            _match = True
            for ii in xrange(basePoints.__len__()):
                if (basePoints[ii] - comparable[ii]).length() > 0.0001:#...if they're different
                    _match = False
                    if not shouldMatch:
                        log.debug("'{0}' doesn't match".format(compareMesh))                         
                        targets.add(compareMesh)
                        break  
                elif shouldMatch and _match and  ii == (basePoints.__len__()-1):
                    log.debug("'{0}' match".format(compareMesh))                                                                
                    targets.add(compareMesh)                    
                
        if targets:
            OM2.MGlobal.setActiveSelectionList(targets)#...select our targets            
            result = targets.getSelectionStrings()#...get the strings
                
    return result

def is_equivalent(sourceObj = None, target = None, tolerance = .0001):
    """
    Compares points of geo mesh. Most likely used for culling out unecessary blend targets that don't do anything.
    Can work of selection as well when no arguments are passed for source and target in a source then targets selection format.
    
    :parameters:
        sourceObj | Object to base comparison on
        target | List of objects to compare with

    :returns
        list of objects matching conditions
    """      
    result = []
    
    #Get our objects if we don't have them
    if sourceObj is None and target is None:
        _sel = mc.ls(sl=True)
        sourceObj = _sel[0]
        target = _sel[1]
        
    #Maya OpenMaya 2.0 came in 2012 and is better but we want this to work in previous versions...
    if mel.eval('getApplicationVersionAsFloat') <2012:
        sel = OM.MSelectionList()#..make selection list
        for o in sourceObj,target:
            sel.add(o)#...add objs
    
        meshPath = OM.MDagPath()#...mesh path holder
        sel.getDagPath(0,meshPath)#...get source dag path
        fnMesh  = OM.MFnMesh(meshPath)#...fnMesh holder
        basePoints = OM.MFloatPointArray() #...data array
        fnMesh.getPoints(basePoints)#...get our data
        
        sel.remove(0)#...remove the source form our list
        
        morph = OM.MDagPath()#...dag path holder
        morphPoints = OM.MFloatPointArray()#...data array
        targets = OM.MSelectionList()#...new list for found matches
        
        for i in xrange(sel.length()):
            sel.getDagPath(i, morph)#...get the target
            fnMesh.setObject(morph)#...get it to our fnMesh obj
            fnMesh.getPoints(morphPoints)#...get comparing data
            _match = True                    
            for j in xrange(morphPoints.length()):
                if (morphPoints[j] - basePoints[j]).length() > tolerance:#...if they're different   
                    return False 
        return True
    
    else:#We can use the new OpenMaya 2.0
        from maya.api import OpenMaya as OM2   
        
        sel = OM2.MSelectionList()#...make selection list
        for o in sourceObj,target:
            sel.add(o)#...add them to our lists        
            
        basePoints = OM2.MFnMesh(sel.getDagPath(0)).getPoints()#..base points data
        sel.remove(0)#...remove source obj
        
        count = sel.length()
        targets = OM2.MSelectionList()#...target selection list
        
        for i in xrange(count):
            comparable = OM2.MFnMesh(sel.getDagPath(i)).getPoints()#...target points data
            compareMesh = sel.getDagPath(i)#...dag path for target
            _match = True
            for ii in xrange(basePoints.__len__()):
                if (basePoints[ii] - comparable[ii]).length() > 0.0001:#...if they're different
                    return False

    return True

def get_proximityGeo(sourceObj= None, targets = None, mode = 1, returnMode = 0, selectReturn = True,
                     expandBy = None, expandAmount = 0):
    """
    Method for checking targets components or entirty are within a source object.

    :parameters:
        sourceObj(str): Object to check against
        targets(list): list of objects to check
        mode(int):search by
           0: rayCast interior
           1: bounding box -- THIS IS MUCH FASTER
        returnMode(int):Data to return 
           0:obj
           1:face
           2:edge
           3:verts/cv
           4:proximity mesh -- proxmity mesh of the faces of the target mesh affected
        selectReturn(bool): whether to select the return or not
        expandBy(str): None
                       expandSelection: uses polyTraverse to grow selection
                       softSelect: use softSelection with linear falloff by the expandAmount Distance
        expandAmount(float/int): amount to expand

    :returns
        list items matching conditions
        
    :acknowledgements
    http://forums.cgsociety.org/archive/index.php?t-904223.html
    http://maya-tricks.blogspot.com/2009/04/python.html -- idea of raycasting to resolve if in interior of object
    http://forums.cgsociety.org/archive/index.php?t-1065459.html
    
    :TODO
    Only works with mesh currently
    """      
    __l_returnModes = ['obj/transform','face','edge/span','vert/cv','proximity mesh']
    __l_modes = ['raycast interior','bounding box']
    __l_expandBy = [None, 'expandSelection','softSelect']
    result = []
    
    _mode = cgmValid.valueArg(mode, inRange=[0,1], noneValid=False, calledFrom = 'get_contained')    
    log.info("mode: {0}".format(_mode))
    
    _returnMode = cgmValid.valueArg(returnMode, inRange=[0,4], noneValid=False, calledFrom = 'get_contained')
    log.info("returnMode: {0}".format(_returnMode))
    
    _selectReturn = cgmValid.boolArg(selectReturn, calledFrom='get_contained')
    
    _expandBy = None
    if expandBy is not None:
        if expandBy in __l_expandBy:
            _expandBy = expandBy
        else:
            raise ValueError,"'{0}' expandBy arg not found in : {1}".format(expandBy, __l_expandBy)
        
    #Validate our expand amount =======================================================================================================
    if expandAmount is 'default':
        expandAmount = distance.returnBoundingBoxSizeToAverage(sourceObj)    
        
    #Get our objects if we don't have them
    if sourceObj is None and targets is None:
        _sel = mc.ls(sl=True)
        sourceObj = _sel[0]
        targets = _sel[1:]

    targets = cgmValid.listArg(targets)#...Validate our targets as a list
    l_targetCounts = []
    
    for o in targets:
        _d = cgmValid.MeshDict(o)
        l_targetCounts.append(_d['pointCountPerShape'][0])
        
    sel = OM.MSelectionList()#..make selection list
    for i,o in enumerate([sourceObj] + targets):
        try:
            sel.add(o)#...add objs
        except Exception,err:   
            raise Exception,"{0} fail. {1}".format(o,err)

    _dagPath = OM.MDagPath()#...mesh path holder
    matching = []#...our match holder
    _l_found = OM.MSelectionList()#...new list for found matches
    
    guiFactory.doProgressWindow(winName='get_contained', 
                                statusMessage='Progress...', 
                                startingProgress=1, 
                                interruptableState=True)
    if _mode is 1:
        log.info('bounding box mode...')        
        try:#Get our source bb info
            sel.getDagPath(0,_dagPath)
            fnMesh_source = OM.MFnMesh(_dagPath)
            matrix_source = OM.MMatrix(_dagPath.inclusiveMatrix())    
            
            bb_source = fnMesh_source.boundingBox()
            bb_source.transformUsing(matrix_source) 
                
            sel.remove(0)#...remove the source
            
        except Exception,err:
            raise Exception,"Source validation fail | {0}".format(err)
       
        for i in xrange(sel.length()):
            _tar = targets[i]
            _vtxCount = l_targetCounts[i]
            log.info("Checking '{0}'".format(_tar))
            
            guiFactory.doUpdateProgressWindow("Checking {0}".format(_tar), i, 
                                              sel.length(), 
                                              reportItem=False)
            
            sel.getDagPath(i, _dagPath)#...get the target 
            
            fnMesh_target = OM.MFnMesh(_dagPath)#...get the FnMesh for the target
            fnMesh_target.setObject(_dagPath)
            pArray_target = OM.MPointArray()#...data array  
            fnMesh_target.getPoints(pArray_target)#...get comparing data
            
            matrix_target = OM.MMatrix(_dagPath.inclusiveMatrix())    
            fnMesh_target = OM.MFnMesh(_dagPath)
            bb_target = fnMesh_source.boundingBox()
            bb_target.transformUsing(matrix_target)         
            
            if bb_source.contains( cgmOM.Point(mc.xform(_tar, q=True, ws=True, t=True))) or bb_source.intersects(bb_target):
                if _returnMode is 0:#...object
                    _l_found.add(_dagPath)
                    continue
            iter = OM.MItGeometry(_dagPath)
            while not iter.isDone():
                vert = iter.position(OM.MSpace.kWorld)
                if bb_source.contains(vert):
                    _l_found.add(_dagPath, iter.currentItem())
                iter.next()                
                
    elif _mode is 0:
        log.info('Ray cast Mode...')
        sel.remove(0)#...remove the source        
        for i in xrange(sel.length()):
            _tar = targets[i]
            _vtxCount = l_targetCounts[i]            
            log.info("Checking '{0}'".format(_tar))
            sel.getDagPath(i, _dagPath)#...get the target 
            fnMesh_target = OM.MFnMesh(_dagPath)#...get the FnMesh for the target
            fnMesh_target.setObject(_dagPath)
            
            guiFactory.doUpdateProgressWindow("Checking {0}".format(_tar), i, 
                                              sel.length(), 
                                              reportItem=False)
            
            iter = OM.MItGeometry(_dagPath)
            _cnt = 0            
            if _returnMode is 0:#...if the object intersects
                _found = False
                while not iter.isDone():
                    guiFactory.doUpdateProgressWindow("Checking vtx[{0}]".format(_cnt), _cnt, 
                                                      _vtxCount, 
                                                      reportItem=False)          
                    _cnt +=1
                    vert = iter.position(OM.MSpace.kWorld)
                    _inside = True                           
                    for v in cgmValid.d_stringToVector.itervalues():
                        d_return = cgmRAYS.findMeshIntersection(sourceObj, vert, 
                                                                v, 
                                                                maxDistance=10000, 
                                                                tolerance=.1)
                        if not d_return.get('hit'):#...if we miss once, it's not inside
                            _inside = False
                    if _inside:
                        _l_found.add(_dagPath)
                        _found = True
                    iter.next()                              
            else:#...vert/edge/face mode...
                while not iter.isDone():
                    guiFactory.doUpdateProgressWindow("Checking vtx[{0}]".format(_cnt), _cnt,  
                                                      _vtxCount, 
                                                      reportItem=False)          
                    _cnt +=1                    
                    vert = iter.position(OM.MSpace.kWorld)
                    _good = True                           
                    p = cgmOM.Point(vert)
                    for v in cgmValid.d_stringToVector.itervalues():
                        d_return = cgmRAYS.findMeshIntersection(sourceObj, vert, 
                                                                v, 
                                                                maxDistance=10000, 
                                                                tolerance=.1)
                        if not d_return.get('hit'):#...if we miss once, it's not inside
                            _good = False
                    if _good:
                        _l_found.add(_dagPath, iter.currentItem())
                    iter.next()  
                
    guiFactory.doCloseProgressWindow()
    
    #Post processing =============================================================================
    _l_found.getSelectionStrings(matching)#...push data to strings    
    log.info("Found {0} vers contained...".format(len(matching)))
    
    if not matching:
        log.warning("No geo found in the provided proximity")
        log.warning("Source: {0}".format(sourceObj))
        log.warning("Targets: {0}".format(targets))
        return False
    
    #Expand ========================================================================================
    if _expandBy is not None and returnMode > 0:
        log.info("Expanding result by '{0}'...".format(_expandBy))   
        _sel = mc.ls(sl=True) or []        
        _expandFactor = int(expandAmount)  
        mc.select(matching)        
        if _expandBy is 'expandSelection':
            for i in range(_expandFactor):
                mel.eval("PolySelectTraverse 1;")
            matching = mc.ls(sl = True)
        if _expandBy is 'softSelect':
            mc.softSelect(softSelectEnabled=True,ssc='1,0,0,0,1,2', softSelectFalloff = 1, softSelectDistance = _expandFactor)
            matching = cgmSELECT.get_softSelectionItems()   
            mc.softSelect(softSelectEnabled=False)
        #if _sel:mc.select(_sel)   

    if _returnMode > 0 and _returnMode is not 3 and matching:#...need to convert
        log.info("Return conversion necessary")
        if _returnMode is 1:#...face
            matching = mc.polyListComponentConversion(matching, fv=True, tf=True, internal = True)
        elif _returnMode is 2:#...edge
            matching = mc.polyListComponentConversion(matching, fv=True, te=True, internal = True )
        elif _returnMode is 4:#...proximity mesh
            #Get our faces
            matching = mc.polyListComponentConversion(matching, fv=True, tf=True, internal = True)
            
            #Sort out the list to the objects to a new dict
            _d_sort = {}
            #d[obj] = [list of .f entries]
            for o in matching:
                _split = o.split('.')#...split our obj from the f data obj.f[1] format
                if _split[0] not in _d_sort.keys():
                    _d_sort[_split[0]] = []
                _d_sort[_split[0]].append( _split[1] )
                
            _l_created = []
            for o,l in _d_sort.iteritems():
                #Dupliate the mesh =======================================================================================================
                _dup = mc.duplicate(o, po = False, n = "{0}_to_{1}_proximesh".format(names.getBaseName(o),
                                                                                     names.getBaseName(sourceObj)))[0]
                log.debug("Dup: {0}".format(_dup))
                
                _longNameDup = names.getShortName(_dup)
                
                #Split out the faces we want =======================================================================================================
                _datNew = ["{0}.{1}".format(_longNameDup,f) for f in l]    
                
                log.debug("Faces:")
                for i,o in enumerate(l):
                    log.debug(''*4 + o + "  >  " + _datNew[i])   
                    
                mc.select(_datNew)
                mel.eval('invertSelection')
                if mc.ls(sl=True):
                    mc.delete(mc.ls(sl=True))   
                _l_created.append(_dup)
            if len(_l_created) == 1:
                attributes.storeInfo(sourceObj, 'proximityMesh', _dup)
            matching = _l_created
            
    if _selectReturn and matching:
        mc.select(matching)
    return matching  

def create_proximityMeshFromTarget(sourceObj= None, target = None, mode = 1, expandBy = 'softSelect', expandAmount = 'default'):
    """
    Create a proximity mesh from another one

    :parameters:
        sourceObj(str): Object to check against
        target(str): object to check
        mode(int):search by
           0: rayCast interior
           1: bounding box -- THIS IS MUCH FASTER
        expandBy(str): None
                       expandSelection: uses polyTraverse to grow selection
                       softSelect: use softSelection with linear falloff by the expandAmount Distance
        expandAmount(float/int): amount to expand. if it's 

    :returns
        New Mesh
        
    """
    raise DeprecationWarning, "Not gonna use this"
    _result = []
    
    #Get our objects if we don't have them
    if sourceObj is None and target is None:
        _sel = mc.ls(sl=True)
        sourceObj = _sel[0]
        targets = _sel[1]

    
    #Validate our expand amount =======================================================================================================
    _expandAmount = expandAmount
    if expandAmount is 'default':
        _expandAmount = distance.returnBoundingBoxSizeToAverage(sourceObj)
    
    #Get our faces =======================================================================================================
    _dat = get_contained(sourceObj, target, mode = mode, returnMode = 1, expandBy = expandBy, expandAmount = _expandAmount)
    
    if not _dat:
        raise ValueError,"No data found on get_contained call!"
    
    #Dupliate the mesh =======================================================================================================
    _dup = mc.duplicate(target, po = False, n = "{0}_proximesh".format(names.getBaseName(target)))[0]
    log.debug("Dup: {0}".format(_dup))
    
    _key = _dat[0].split('.')[0]
    _longNameDup = names.getShortName(_dup)
    
    #Split out the faces we want =======================================================================================================
    _datNew = [ o.replace(_key, _longNameDup) for o in _dat]    
    
    log.debug("Faces:")
    for i,o in enumerate(_dat):
        log.debug(''*4 + o + "  >  " + _datNew[i])   
        
    mc.select(_datNew)
    mel.eval('invertSelection')
    if mc.ls(sl=True):
        mc.delete(mc.ls(sl=True))
    mc.select(_dup)
    
    attributes.storeInfo(sourceObj, 'proximityMesh', _dup)
    return _dup

def get_deltaBaseLine(mNode = None, excludeDeformers = True):
    """
    Get the base positional informaton against which to do other functions.
    I know there must be a better way to do this...

    :parameters:
        sourceObj(str): Must be a cgmObject or subclass
        noDeformers(bool): Whether to 

    :returns
        
    """
    _str_funcName = 'get_deltaBaseLine: '
    
    if excludeDeformers:
        _deformers = mNode.getDeformers(asMeta = True)
        
    else:
        _deformers = []
        
    _d_wiring = {}
    #...go through and zero out the envelops on the deformers
    for mDef in _deformers:
        _d = {}
        _envelopeAttr = "{0}.envelope".format(mDef.mNode)
        _plug = attributes.returnDriverAttribute(_envelopeAttr) or False
        if _plug:
            attributes.doBreakConnection(_envelopeAttr)
        _d['plug'] = _plug
        _d['value'] = mDef.envelope
        _d['attr'] = _envelopeAttr
        _d_wiring[mDef] = _d
        mDef.envelope = 0

    #meat...
    _result = []
    _dict = cgmValid.MeshDict(mNode.mNode)
    for i in range(_dict['pointCount']):
        _result.append(mc.xform("{0}.vtx[{1}]".format(mNode.mNode,i), t = True, os = True, q=True))

    #...rewire
    for mDef in _d_wiring.keys():
        _d = _d_wiring[mDef]
        if _d.get('plug'):
            attributes.doConnectAttr( _d.get('plug'),_d['attr'])
        else:
            mDef.envelope = _d.get('value')
    return _result

def get_shapePosData(meshShape = None, space = 'os'):
    _str_funcName = 'get_shapePosData'
    
    __space__ = {'world':['w','ws'],'object':['o','os']}
    _space = cgmValid.kw_fromDict(space, __space__, calledFrom=_str_funcName)    
    
    _result = []
    _dict = cgmValid.MeshDict(meshShape)
    #cgmGeneral.log_info_dict(_dict,'get_shapePosData: {0}'.format(meshShape))
    for i in range(_dict['pointCount']):
        if _space == 'world':
            _result.append(mc.xform("{0}.vtx[{1}]".format(_dict['shape'],i), t = True, ws = True, q=True))                
        else:
            _result.append(mc.xform("{0}.vtx[{1}]".format(_dict['shape'],i), t = True, os = True, q=True))    
    return _result

def meshMath(sourceObj = None, target = None, mode = 'blend', space = 'object', createNew = True, multiplier = None):
    """
    Create a new mesh by adding,subtracting etc the positional info of one mesh to another

    :parameters:
        sourceObj(str): The mesh we're using to change our target
        target(str): Mesh to be modified itself or by duplication
        mode(str)
            add : (target + source) * multiplier
            subtract : (target - source) * multiplier
            multiply : (target * source) * multiplier
            average: ((target + source) /2 ) * multiplier
            difference: delta
            addDiff: target + (delta * multiplier)
            subtractDiff: target + (delta * multiplier)
            blend: pretty much blendshape result if you added as a target using multiplier as weight
            copyTo: resets to target to the source
        space(str): object,world
        createNew(bool):whether to create a new mesh result or apply result to target
        multiplier(float): default 1 -- value to use as a multiplier during the different modes. 

    :returns
        mesh(str) -- which has been modified
        
    """
    _sel = mc.ls(sl=True)
    _str_funcName = 'meshMath'
    __modes__ = ['add','subtract','multiply','average','difference','addDiff','subtractDiff','blend','copyTo']
    __space__ = {'world':['w','ws'],'object':['o','os']}
    _mode = cgmValid.kw_fromList(mode, __modes__, calledFrom=_str_funcName)
    _space = cgmValid.kw_fromDict(space, __space__, calledFrom=_str_funcName)
    _multiplier = cgmValid.valueArg(multiplier, calledFrom=_str_funcName)
    if not _multiplier:
        if _mode == 'blend':
            _multiplier = .5
        else:
            _multiplier = 1
    
    #>> Get our objects if we don't have them...
    if sourceObj is None or target is None:
        _sel = mc.ls(sl=True)
        if not _sel:
            raise ValueError,"{0} must have a sourceObj or selection".format(_str_funcName)
        
        if sourceObj is None:
            sourceObj = _sel[0]
            
        if target is None:
            try:
                target = _sel[1]
            except:
                raise ValueError,"{0} must have a target".format(_sel)
            
    _d_source = cgmValid.MeshDict(sourceObj,False, calledFrom=_str_funcName)
    _d_target = cgmValid.MeshDict(target,False, calledFrom=_str_funcName)

    for k in ['meshType']:
        if _d_source[k] != _d_target[k]:
            raise ValueError,"{0} Mesh dicts keys must match. {1} failed".format(_str_funcName,k)
    
    log.debug(cgmGeneral._str_subLine)	
    log.debug("{0}...".format(_str_funcName))
    #cgmGeneral.log_info_dict(_d_source,'Source')
    #cgmGeneral.log_info_dict(_d_target,'Target')
    log.debug("sourceObj: {0}".format(sourceObj))	
    log.debug("target: {0}".format(target))	
    log.debug("mode: {0}".format(_mode))	
    log.debug("space: {0}".format(_space))
    log.debug("multiplier: {0}".format(_multiplier))

    #meat...
    _l_pos_obj = get_shapePosData(_d_source['shape'],space)
    _l_pos_targ = get_shapePosData(_d_target['shape'],space)
    _len_obj = len(_l_pos_obj)
    _len_target = len(_l_pos_targ) 
    assert _len_obj == _len_target, "{0} Must have same vert count. lenSource> {1} != {2} <lenTarget".format(_str_funcName,_len_obj, _len_target)
        
    log.debug("obj pos: {0}".format(_l_pos_obj))	
    log.debug("tar pos: {0}".format(_l_pos_targ))   
    _l_toApply = []
    
    if _mode == 'copyTo':
        _l_toApply = _l_pos_obj  
    else:
        
        for i,pos in enumerate(_l_pos_targ):
            _nPos = []
            if _mode == 'add':
                _nPos = cgmMath.list_add(pos, _l_pos_obj[i]) * _multiplier
            elif _mode == 'subtract':
                _nPos = cgmMath.list_subtract(pos, _l_pos_obj[i]) * _multiplier  
            elif _mode == 'multiply':
                for ii,p in enumerate(pos):
                    _nPos.append((p * _l_pos_obj[i][ii]) * _multiplier)
            elif _mode == 'average':
                for ii,p in enumerate(pos):
                    _nPos.append(((p + _l_pos_obj[i][ii])/2) * _multiplier)
            elif _mode == 'difference':
                for ii,p in enumerate(pos):
                    _nPos.append((p - _l_pos_obj[i][ii]) * _multiplier) 
            elif _mode == 'addDiff':
                for ii,p in enumerate(pos):
                    #_nPos.append(_l_pos_obj[i][ii] + ((_l_pos_obj[i][ii] - p) * _multiplier))                  
                    _nPos.append(p + (((p - _l_pos_obj[i][ii])) * _multiplier))  
            elif _mode == 'subtractDiff':
                for ii,p in enumerate(pos):
                    _nPos.append(p - (((p - _l_pos_obj[i][ii])) * _multiplier))    
            elif _mode == 'blend':
                for ii,p in enumerate(pos):
                    _nPos.append(p - ((p - _l_pos_obj[i][ii]) * (_multiplier)))  
            else:
                raise NotImplementedError,"{0} mode not implemented: '{1}'".format(_str_funcName,_mode)
            _l_toApply.append(_nPos)
            
    log.debug("res pos: {0}".format(_l_toApply))   
    log.debug(cgmGeneral._str_subLine)  
    
    if createNew:
        _result = mc.duplicate(target)[0]
        _result = mc.rename(_result,"{0}_from_{1}_{2}_x{3}_result".format(target,sourceObj,_mode,_multiplier))
        
    else:
        _result = target
        
    for i,pos in enumerate(_l_toApply):
        if _space == 'world':
            mc.xform("{0}.vtx[{1}]".format(_result,i), t = pos, ws = True)             
        else:
            mc.xform("{0}.vtx[{1}]".format(_result,i), t = pos, os = True)      
            
    if _sel:mc.select(_sel)
    return _result
    
    
    
    


