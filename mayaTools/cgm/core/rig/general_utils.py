"""
------------------------------------------
general_utils: cgm.core.rig
Author: Josh Burton
email: jjburton@cgmonks.com
Website : http://www.cgmonks.com
------------------------------------------


================================================================
"""
# From Python =============================================================
import copy
import re
import time
import pprint

#>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)

# From Maya =============================================================
import maya.cmds as mc

# From cgm ==============================================================
from cgm.core import cgm_Meta as cgmMeta
from cgm.core import cgm_General as cgmGEN
import cgm.core.lib.snap_utils as SNAP
import cgm.core.lib.rigging_utils as RIG
import cgm.core.lib.distance_utils as DIST
import cgm.core.lib.math_utils as MATH
reload(DIST)

def matchValue_iterator(matchObj = None, matchAttr = None, drivenObj = None, drivenAttr = None, driverAttr = None, 
                        minIn = -180, maxIn = 180, maxIterations = 40, matchValue = None):
    """
    Started with Jason Schleifer's afr js_iterator and 'tweaked'
    """
    _str_func = 'matchValue_iterator'
    log.debug("|{0}| >> ...".format(_str_func))    
    
    if type(minIn) not in [float,int]:raise StandardError,"matchValue_iterator>>> bad minIn: %s"%minIn
    if type(maxIn) not in [float,int]:raise StandardError,"matchValue_iterator>>> bad maxIn: %s"%maxIn

    __matchMode__ = False
    
    #>>> Data gather and arg check        
    mi_matchObj = cgmMeta.validateObjArg(matchObj,'cgmObject',noneValid=True)
    d_matchAttr = cgmMeta.validateAttrArg(matchAttr,noneValid=True)
    if mi_matchObj:
        __matchMode__ = 'matchObj'
        minValue = minIn
        maxValue = maxIn 

    elif d_matchAttr:
        __matchMode__ = 'matchAttr'
    elif matchValue is not None:
        __matchMode__ = 'value'
    else:
        raise ValueError,"|{0}| >> No match given. No matchValue given".format(_str_func)
        
    __drivenMode__ = False
    mi_drivenObj = cgmMeta.validateObjArg(drivenObj,'cgmObject',noneValid=True)
    d_drivenAttr = cgmMeta.validateAttrArg(drivenAttr,noneValid=True)    
    if mi_drivenObj:#not an object match but a value
        __drivenMode__ = 'object'
    elif d_drivenAttr:
        __drivenMode__ = 'attr'
        mPlug_driven = d_drivenAttr['mi_plug']
        f_baseValue = mPlug_driven.value	
        minRange = float(f_baseValue - 10)
        maxRange = float(f_baseValue + 10)  
        mPlug_driven
        log.debug("|{0}| >> Attr mode. Attr: {1} | baseValue: {2} ".format(_str_func,mPlug_driven.p_combinedShortName,f_baseValue))
        
    else:
        raise ValueError,"|{0}| >> No driven given".format(_str_func)
        

    d_driverAttr = cgmMeta.validateAttrArg(driverAttr,noneValid=False)
    mPlug_driver = d_driverAttr['mi_plug']
    if not mPlug_driver:
        raise ValueError,"|{0}| >> No driver given".format(_str_func)

    
    log.debug("|{0}| >> Source mode: {1} | Target mode: {2}| Driver: {3}".format(_str_func,__matchMode__,__drivenMode__,mPlug_driver.p_combinedShortName))
    
    #===========================================================================================================
    #>>>>>>> Meat
    #>>> Check autokey
    b_autoFrameState = mc.autoKeyframe(q=True, state = True)
    if b_autoFrameState:
        mc.autoKeyframe(state = False)

    minValue = float(minIn)
    maxValue = float(maxIn)  
    f_lastClosest = None
    f_lastValue = None
    cnt_sameValue = 0
    b_matchFound = None
    b_firstIter = True
    d_valueToSetting = {}

    #Source type: value
    for i in range(maxIterations):
        if __matchMode__ == 'value':
            if __drivenMode__ == 'attr':
                log.debug("matchValue_iterator>>> Step : %s | min: %s | max: %s | baseValue: %s | current: %s"%(i,minValue,maxValue,f_baseValue,mPlug_driven.value))  					
                if MATH.is_float_equivalent(mPlug_driven.value,matchValue,3):
                    log.debug("matchValue_iterator>>> Match found: %s == %s | %s: %s | step: %s"%(mPlug_driven.p_combinedShortName,matchValue,mPlug_driver.p_combinedShortName,minValue,i))  			    
                    b_matchFound = minValue
                    break
                f_currentDist = abs(matchValue-mPlug_driven.value)
                mPlug_driver.value = minValue#Set to min
                f_minDist = abs(matchValue-mPlug_driven.value)#get Dif
                f_minSetValue = mPlug_driven.value
                mPlug_driver.value = maxValue#Set to max
                f_maxDist = abs(matchValue-mPlug_driven.value)#Get dif
                f_maxSetValue = mPlug_driven.value

                f_half = ((maxValue-minValue)/2.0) + minValue#get half
                #First find range
                if f_minSetValue > matchValue or f_maxSetValue < matchValue:
                    log.error("Bad range, alternate range find. minSetValue = %s > %s < maxSetValue = %s"%(f_minSetValue,matchValue,f_maxSetValue))

                if not MATH.is_float_equivalent(matchValue,0) and not MATH.is_float_equivalent(minValue,0) and not MATH.is_float_equivalent(f_minSetValue,0):
                    #if none of our values are 0, this is really fast
                    minValue = (minValue * matchValue)/f_minSetValue
                    log.debug("matchValue_iterator>>> Equated: %s"%minValue)		    
                    f_closest = f_minDist
                    mPlug_driver.value = minValue#Set to min			
                else:	
                    if f_minDist>f_maxDist:#if min dif greater, use half as new min
                        if f_half < minIn:
                            raise StandardError, "half min less than minValue"
                            f_half = minIn
                        minValue = f_half
                        #log.debug("matchValue_iterator>>>Going up")
                        f_closest = f_minDist
                    else:
                        if f_half > maxIn:
                            raise StandardError, "half max less than maxValue"			    
                            f_half = maxIn			
                        maxValue = f_half
                        #log.debug("matchValue_iterator>>>Going down")  
                        f_closest = f_maxDist

                #Old method
                """
		mPlug_driver.value = minValue#Set to min
		f_minDist = abs(matchValue-mPlug_driven.value)#get Dif
		f_minSetValue = mPlug_driven.value
		mPlug_driver.value = maxValue#Set to max
		f_maxDist = abs(matchValue-mPlug_driven.value)#Get dif
		f_maxSetValue = mPlug_driven.value

		f_half = ((maxValue-minValue)/2.0) + minValue#get half	

		#First find range
		if not MATH.is_float_equivalent(matchValue,0) and not MATH.is_float_equivalent(minValue,0) and not MATH.is_float_equivalent(f_minSetValue,0):
		    #if none of our values are 0, this is really fast
		    minValue = (minValue * matchValue)/f_minSetValue
		    log.debug("matchValue_iterator>>> Equated: %s"%minValue)		    
		    f_closest = f_minDist
		    mPlug_driver.value = minValue#Set to min		    
		elif b_firstIter:
		    log.debug("matchValue_iterator>>> first iter. Trying matchValue: %s"%minValue)		    		    
		    b_firstIter = False
		    minValue = matchValue
		    f_closest = f_minDist		    
		elif f_minSetValue > matchValue or f_maxSetValue < matchValue:
		    log.debug("matchValue_iterator>>> Finding Range....")		    
		    if matchValue < mPlug_driven.value:
			#Need to shift our range down
			log.debug("matchValue_iterator>>> Down range: minSetValue: %s"%f_minSetValue)
			f_baseValue = f_maxDist		    
			minValue = f_baseValue - f_minDist
			maxValue = f_baseValue + f_minDist
			f_closest = f_minDist			
		    elif matchValue > mPlug_driven.value:
			#Need to shift our range up
			log.debug("matchValue_iterator>>> Up range: maxSetValue: %s"%f_maxSetValue)  
			f_baseValue = f_minDist		    
			minValue = f_baseValue - f_maxDist
			maxValue = f_baseValue + f_maxDist
			f_closest = f_maxDist			
		else:	
		    if f_minDist>f_maxDist:#if min dif greater, use half as new min
			if f_half < minIn:f_half = minIn
			minValue = f_half
			#log.debug("matchValue_iterator>>>Going up")
			f_closest = f_minDist
		    else:
			if f_half > maxIn:f_half = maxIn			
			maxValue = f_half
			#log.debug("matchValue_iterator>>>Going down")  
			f_closest = f_maxDist"""

                log.debug("matchValue_iterator>>>f1: %s | f2: %s | f_half: %s"%(f_minDist,f_maxDist,f_half))  
                log.debug("#"+'-'*50)

                if f_closest == f_lastClosest:
                    cnt_sameValue +=1
                    if cnt_sameValue >3:
                        log.error("matchValue_iterator>>> Value unchanged. Bad Driver. lastValue: %s | currentValue: %s"%(f_lastValue,mPlug_driven.value))		
                        break
                else:
                    cnt_sameValue = 0 
                f_lastClosest = f_closest
            else:
                log.warning("matchValue_iterator>>> driven mode not implemented with value mode: %s"%__drivenMode__)
                break		

        #>>>>>matchObjMode
        elif __matchMode__ == 'matchObj':
            pos_match = mc.xform(mi_matchObj.mNode, q=True, ws=True, rp=True)
            pos_driven = mc.xform(mi_drivenObj.mNode, q=True, ws=True, rp=True)
            log.debug("matchValue_iterator>>> min: %s | max: %s | pos_match: %s | pos_driven: %s"%(minValue,maxValue,pos_match,pos_driven))  						    
            if MATH.isVectorEquivalent(pos_match,pos_driven,2):
                log.debug("matchValue_iterator>>> Match found: %s <<pos>> %s | %s: %s | step: %s"%(mi_matchObj.getShortName(),mi_drivenObj.getShortName(),mPlug_driver.p_combinedShortName,minValue,i))  			    
                b_matchFound = mPlug_driver.value
                break

            mPlug_driver.value = minValue#Set to min
            pos_min = mc.xform(mi_drivenObj.mNode, q=True, ws=True, rp=True)
            #f_minDist = MATH.mag( MATH.list_subtract(pos_match,pos_min))#get Dif
            f_minDist = distance.returnDistanceBetweenObjects(mi_drivenObj.mNode,mi_matchObj.mNode)

            mPlug_driver.value = maxValue#Set to max
            pos_max = mc.xform(mi_drivenObj.mNode, q=True, ws=True, rp=True)
            f_maxDist = distance.returnDistanceBetweenObjects(mi_drivenObj.mNode,mi_matchObj.mNode)
            f_half = ((maxValue-minValue)/2.0) + minValue#get half	

            if f_minDist>f_maxDist:#if min dif greater, use half as new min
                minValue = f_half
                f_closest = f_minDist
            else:
                maxValue = f_half
                f_closest = f_maxDist	

            if f_minDist==f_maxDist:
                minValue = minValue + .1

            if f_closest == f_lastClosest:
                cnt_sameValue +=1
                if cnt_sameValue >3:
                    log.error("matchValue_iterator>>> Value unchanged. Bad Driver. lastValue: %s | currentValue: %s"%(f_lastValue,mPlug_driver.value))		
                    break
            else:
                cnt_sameValue = 0 
            f_lastClosest = f_closest

            log.debug("matchValue_iterator>>>f1: %s | f2: %s | f_half: %s"%(f_minDist,f_maxDist,f_half))  
            log.debug("#"+'-'*50)	    

        else:
            log.warning("matchValue_iterator>>> matchMode not implemented: %s"%__matchMode__)
            break

    #>>> Check autokey back on
    if b_autoFrameState:
        mc.autoKeyframe(state = True) 

    if b_matchFound is not None:
        return b_matchFound
    #log.warning("matchValue_iterator>>> Failed to find value for: %s"%mPlug_driven.p_combinedShortName)    
    return False