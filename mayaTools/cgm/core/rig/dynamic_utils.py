import maya.cmds as mc
from cgm.core import cgm_General as cgmGEN
import cgm.core.lib.distance_utils as DIST
import cgm.core.lib.attribute_utils as ATTR
import cgm.core.lib.euclid as euclid
import cgm.core.lib.rigging_utils as CORERIG
import cgm.core.lib.locator_utils as LOC
import cgm.core.lib.curve_Utils as CURVE
from cgm.core.cgmPy.validateArgs import simpleAxis
import cgm.core.lib.name_utils as NAMES
import cgm.core.cgm_Meta as cgmMeta
import pprint
import copy
import maya.mel as mel


import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)


class chain(object):
    hairSystem = None
    nucleus = None
    follicles = []
    ml_follicles = []
    outCurves = []
    targets = []
    baseName = None
        
    
    def __init__(self, objs = None, fwd = 'z+', up = 'y+', hairSystem=None, baseName = 'cgmDynHair', name = None):
        self.hairSystem = hairSystem
        
        _sel = mc.ls(sl=1)
        if not objs:
            if _sel:
                objs = _sel
                
        self.baseName = baseName
                
        if objs:
            self.CreateChain(objs, fwd, up, name)
            


    def CreateChain(self, objs = None, fwd = 'z+', up='y+',name = None):
        _str_func = 'CreateChain'
        
        objs = cgmMeta.asMeta( mc.ls(sl=True) )
        
        if not objs:
            return log.warning("No objects passed. Unable to createChain")
            
        if name is None:
            name = objs[-1].p_nameBase

        self.targets = self.targets + objs

        fwdAxis = simpleAxis(fwd)
        upAxis = simpleAxis(up)

        crvPositions = []

        for obj in objs:
            crvPositions.append(obj.p_position)

        crvPositions.append( DIST.get_pos_by_axis_dist(objs[-1], fwdAxis.p_string,
                                                       DIST.get_distance_between_points(crvPositions[-1],crvPositions[-2])) )

        crvPositions.insert(0, DIST.get_pos_by_axis_dist(objs[0], fwdAxis.inverse.p_string,
                                                         DIST.get_distance_between_points(crvPositions[0],crvPositions[1])*.5) )

        crv = CORERIG.create_at(create='curve',l_pos= crvPositions, baseName = name)

        # make the dynamic setup
        b_existing = False
        if self.hairSystem != None:
            log.info(cgmGEN.logString_msg(_str_func,'Using existing system: {0}'.format(self.hairSystem)))
            mc.select(self.hairSystem, add=True)
            b_existing = True
            
        mel.eval('makeCurvesDynamic 2 { "0", "0", "1", "1", "0" }')

        # get relevant nodes
        follicle = mc.listRelatives(crv,parent=True)[0]
        mFollicle = cgmMeta.asMeta(follicle)
        mFollicle.rename("{0}_foll".format(name))
        follicle = mFollicle.mNode
        self.ml_follicles.append(mFollicle)
        
        follicleShape = mc.listRelatives(mFollicle.mNode, shapes=True)[0]
        self.hairSystem = mc.listRelatives( mc.listConnections('%s.currentPosition' % follicleShape)[0], shapes=True)[0]
        if not b_existing:
            mHairSys = cgmMeta.asMeta(self.hairSystem)
            mHairSysDag = mHairSys.getTransform(asMeta=1)
            
            mHairSysDag.rename("{0}_hairSys".format(self.baseName))
            self.hairSystem = mHairSys.mNode
            
        outCurve = mc.listConnections('%s.outCurve' % follicle)[0]
        outCurveShape = mc.listRelatives(outCurve, shapes=True)[0]
        self.nucleus = mc.listConnections( '%s.currentState' % self.hairSystem )[0]
        if not b_existing:
            pass
        mc.select( objs[0].getParent() )

        self.follicles.append(follicle)
        self.outCurves.append(outCurve)
        
        # set default properties
        mc.setAttr( '%s.pointLock' % follicleShape, 1 )
        mc.parentConstraint(objs[0].getParent(), follicle, mo=True)

        # create locators on objects
        locators = []
        prs = []

        for i, obj in enumerate(objs):
            loc = LOC.create(obj.getNameLong())
            locators.append(loc)
            
            aimNull = mc.group(em=True)
            aimNull = mc.rename('%s_aim' % obj.getShortName())
            
            poc = mc.createNode('pointOnCurveInfo', name='%s_pos' % loc)
            pocAim = mc.createNode('pointOnCurveInfo', name='%s_aim' % loc)
            pr = CURVE.getUParamOnCurve(loc, outCurve)
            
            mc.connectAttr( '%s.worldSpace[0]' % outCurveShape, '%s.inputCurve' % poc, f=True )
            mc.connectAttr( '%s.worldSpace[0]' % outCurveShape, '%s.inputCurve' % pocAim, f=True )

            mc.setAttr( '%s.parameter' % poc, pr )
            
            if i < len(objs)-1:
                nextpr = CURVE.getUParamOnCurve(objs[i+1], outCurve)
                mc.setAttr('%s.parameter' % pocAim, (nextpr + pr) * .5)
            else:
                mc.setAttr( '%s.parameter' % pocAim, len(objs)+1 )
            
            locParent = mc.group(em=True)
            locParent = mc.rename( '%s_pos' % obj.getShortName() )

            mc.connectAttr( '%s.position' % poc, '%s.translate' % locParent)
            mc.connectAttr( '%s.position' % pocAim, '%s.translate' % aimNull)
            
            aimConstraint = mc.aimConstraint( aimNull, locParent, aimVector=fwdAxis.p_vector, upVector = upAxis.p_vector, worldUpType = "objectrotation", worldUpVector = upAxis.p_vector, worldUpObject = objs[0].getParent() )

            mc.parent(loc, locParent)

    def SelectTargets(self):
        mc.select(cl = True)
        for obj in self.targets:
            mc.select(obj, add=True)
            
            
    def report(self):
        pprint.pprint(self.__dict__)
        
    def delete(self):
        pass
    
    
class cgmDynFK(cgmMeta.cgmObject):
    baseName = None
    fwd = None
    up = None
    startFrame = None
    
    def __init__(self,node = None, name = None,
                 objs = None, fwd = 'z+', up = 'y+',
                 hairSystem=None, baseName = 'hair',
                 startFrame = -50,
                 *args,**kws):
        """ 

        """
        ### input check  
        _sel = mc.ls(sl=1)
        if not objs and node is None:
            if _sel:objs = _sel
        
        super(cgmDynFK, self).__init__(node = node,name = name,nodeType = 'transform') 
        #>>> TO USE Cached instance ---------------------------------------------------------
        if self.cached:
            return
        
        #====================================================================================
        #for a in 'arg_ml_dynParents','_mi_dynChild','_mi_followDriver','d_indexToAttr','l_dynAttrs':
            #if a not in self.UNMANAGED:
                #self.UNMANAGED.append(a)
                
        self.dagLock(ignore=['v'])

        if kws:log.debug("kws: %s"%str(kws))
        if args:log.debug("args: %s"%str(args))
        
        self.fwd = fwd
        self.up = up
        self.startFrame = startFrame
        self.baseName = baseName
        
        if not node:
            self.rename("{0}_dynFK".format(self.baseName))
                
        if objs:self.chain_create(objs, fwd, up, name)        
        
        self.report()
        
        if _sel:
            mc.select(_sel)
    
    def get_nextIdx(self):
        return ATTR.get_nextAvailableSequentialAttrIndex(self.mNode, "chain")
        
    def chain_rebuild(self, idx = None, objs = None):
        pass
    
    def chain_deleteByIdx(self, idx = None):
        if idx is None:
            return log.warning("Must have an idx to remove")
        
        mGrp = self.getMessageAsMeta("chain_{0}".format(idx))
        if mGrp:
            mGrp.delete()
            return log.info("Removed idx: {0}".format(idx))
        else:
            return log.warning("No chain found at idx: {0}".format(idx))
            
    def chain_removeAll(self):
        ml = self.msgList_get('chain')
        for i,mGrp in enumerate(ml):
            log.warning("Removing: {0} | {1}".format(i,mGrp.mNode))
            mGrp.delete()
        
        self.msgList_purge('chain')
        
    def chain_create(self, objs = None,
                     fwd = None, up=None,
                     name = None):
        
        _str_func = 'chain_create'
        
        if not objs:
            _sel = mc.ls(sl=1)
            if _sel:objs = _sel
            
        ml = cgmMeta.asMeta( objs, noneValid = True )
        ml_baseTargets = copy.copy(ml)
        
        if not ml:
            return log.warning("No objects passed. Unable to chain_create")
            
        if name is None:
            name = ml[-1].p_nameBase
                    
        _idx = self.get_nextIdx()
        
        #Make our sub group...
        mGrp = self.doCreateAt(setClass=1)
        mGrp.p_parent = self
        mGrp.rename("chain_{0}_{1}_grp".format(_idx,name))
        mGrp.dagLock()
        self.connectChildNode(mGrp.mNode,'chain_{0}'.format(_idx),'owner')
        
        
        #holders and dat...
        ml_targets = []
        ml_posLocs = []
        ml_aim_locs = []
        
        fwd = fwd or self.fwd
        up = up or self.up

        fwdAxis = simpleAxis(fwd)
        upAxis = simpleAxis(up)

        #Curve positions...
        l_pos = []
        
        if len(ml) < 2:
            log.debug(cgmGEN.logString_msg(_str_func, 'Single count. Adding extra handle.'))
            mLoc = ml[0].doLoc()
            mLoc.rename("chain_{0}_{1}_end_loc".format(_idx, name))
            mLoc.p_position = ml[0].getPositionByAxisDistance(fwdAxis.p_string,1.0)
            ml.append(mLoc)
            mLoc.p_parent = mGrp
        
        for obj in ml:
            l_pos.append(obj.p_position)
            
        l_pos.append( DIST.get_pos_by_axis_dist(ml[-1],
                                                fwdAxis.p_string,
                                                DIST.get_distance_between_points(l_pos[-1],l_pos[-2])) )

        l_pos.insert(0, DIST.get_pos_by_axis_dist(ml[0],
                                                  fwdAxis.inverse.p_string,
                                                  DIST.get_distance_between_points(l_pos[0],l_pos[1])*.5) )


        crv = CORERIG.create_at(create='curve',l_pos= l_pos, baseName = name)
        

        # make the dynamic setup
        log.debug(cgmGEN.logString_sub(_str_func,'dyn setup'))
        b_existing = False
        
        mHairSys = self.getMessageAsMeta('mHairSysShape')
        if mHairSys:
            mHairSysDag = mHairSys.getTransform(asMeta=1)
            log.info(cgmGEN.logString_msg(_str_func,'Using existing system: {0}'.format(mHairSys.mNode)))
            mc.select(mHairSysDag.mNode, add=True)
            b_existing = True            
            
        mel.eval('makeCurvesDynamic 2 { "0", "0", "1", "1", "0" }')

        # get relevant nodes
        follicle = mc.listRelatives(crv,parent=True)[0]
        mFollicle = cgmMeta.asMeta(follicle)
        mFollicle.rename("{0}_foll".format(name))
        mFollicle.getParent(asMeta=1).p_parent = mGrp
        mFollicleShape = mFollicle.getShapes(1)[0]
        
        _follicle = mFollicle.mNode
        mGrp.connectChildNode(mFollicle.mNode,'mFollicle','group')
        
        follicleShape = mFollicleShape.mNode#mc.listRelatives(mFollicle.mNode, shapes=True)[0]
        _hairSystem = mc.listRelatives( mc.listConnections('%s.currentPosition' % follicleShape)[0],
                                        shapes=True)[0]
        if not b_existing:
            mHairSys = cgmMeta.asMeta(_hairSystem)
            mHairSysDag = mHairSys.getTransform(asMeta=1)
            
            mHairSysDag.rename("{0}_hairSys".format(self.baseName))
            self.connectChildNode(mHairSysDag.mNode,'mHairSysDag','owner')
            self.connectChildNode(mHairSys.mNode,'mHairSysShape','owner')
            
            mHairSysDag.p_parent = self
            
        outCurve = mc.listConnections('%s.outCurve' % _follicle)[0]
        outCurveShape = mc.listRelatives(outCurve, shapes=True)[0]
        _nucleus = mc.listConnections( '%s.currentState' % mHairSys.mNode )[0]
        if not b_existing:
            mNucleus = cgmMeta.asMeta(_nucleus)
            mNucleus.rename("cgmDynFK_nucleus")            
            self.connectChildNode(mNucleus.mNode,'mNucleus')
            #self.connectChildNode(mNucleus.mNode,'mNucleus','owner')
            
            if self.startFrame is not None:
                mNucleus.startFrame = self.startFrame
            
        
        ml[0].getParent(asMeta=1).select()
        mCrv = cgmMeta.asMeta(outCurve)
        mGrp.connectChildNode(mCrv.mNode,'mOutCrv','group')

        #self.follicles.append(follicle)
        #self.outCurves.append(outCurve)
        
        # set default properties
        mFollicleShape.pointLock = 1
        #mc.setAttr( '%s.pointLock' % follicleShape, 1 )
        mc.parentConstraint(ml[0].getParent(), _follicle, mo=True)
        
        # create locators on objects
        locators = []
        prs = []
        
        ml_locs = []
        ml_aims = []
        ml_prts = []
        
        #Let's make an up object as the parent of the root isn't good enough
        mUp = ml[0].doCreateAt(setClass=1)
        mUp.rename("chain_{0}_{1}_up".format(_idx,name))
        mUp.p_parent = mGrp
        mc.parentConstraint(ml[0].getParent(), mUp.mNode, mo=True)
        
        for i, mObj in enumerate(ml):
            mLoc = cgmMeta.asMeta( LOC.create(mObj.getNameLong()) )
            loc = mLoc.mNode
            ml_locs.append(mLoc)
            #loc = LOC.create(mObj.getNameLong())
            
            mAim = mLoc.doGroup(False,False,
                                 asMeta=True,
                                 typeModifier = 'aim',
                                 setClass='cgmObject')
            ml_aims.append(mAim)
            #aimNull = mc.group(em=True)
            #aimNull = mc.rename('%s_aim' % mObj.getShortName())
            
            
            poc = mc.createNode('pointOnCurveInfo', name='%s_pos' % loc)
            pocAim = mc.createNode('pointOnCurveInfo', name='%s_aim' % loc)
            pr = CURVE.getUParamOnCurve(loc, outCurve)
            
            mc.connectAttr( '%s.worldSpace[0]' % outCurveShape, '%s.inputCurve' % poc, f=True )
            mc.connectAttr( '%s.worldSpace[0]' % outCurveShape, '%s.inputCurve' % pocAim, f=True )

            mc.setAttr( '%s.parameter' % poc, pr )
            
            if i < len(ml)-1:
                nextpr = CURVE.getUParamOnCurve(ml[i+1], outCurve)
                mc.setAttr('%s.parameter' % pocAim, (nextpr + pr) * .5)
            else:
                mc.setAttr( '%s.parameter' % pocAim, len(ml)+1 )
            
            mLocParent = mLoc.doGroup(False,False,
                                      asMeta=True,
                                      typeModifier = 'pos',
                                      setClass='cgmObject')
            ml_prts.append(mLocParent)
            #locParent = mc.group(em=True)
            #locParent = mc.rename( '%s_pos' % mObj.getShortName() )

            mc.connectAttr( '%s.position' % poc, '%s.translate' % mLocParent.mNode)
            mc.connectAttr( '%s.position' % pocAim, '%s.translate' % mAim.mNode)
            
            aimConstraint = mc.aimConstraint( mAim.mNode, mLocParent.mNode, aimVector=fwdAxis.p_vector, upVector = upAxis.p_vector, worldUpType = "objectrotation", worldUpVector = upAxis.p_vector, worldUpObject = mUp.mNode )
            
            mLoc.p_parent = mLocParent
            mAim.p_parent = mGrp
            mLocParent.p_parent = mGrp
            
            #mc.parent(loc, locParent)
            
        mCrv.rename("{0}_outCrv".format(name))
        mCrvParent = mCrv.getParent(asMeta=1)
        mCrvParent.p_parent = mGrp
        
        mGrp.msgList_connect('mLocs',ml_locs)
        mGrp.msgList_connect('mAims',ml_aims)
        mGrp.msgList_connect('mParents',ml_prts)
        mGrp.msgList_connect('mTargets',ml)
        mGrp.msgList_connect('mBaseTargets',ml_baseTargets)
        
        

    def report(self):
        _d = {'up':self.up,
              'fwd':self.fwd,
              'baseName':self.baseName}
        
        pprint.pprint(_d)
        
    def get_dat(self):
        _res = {'mNucleus':self.getMessageAsMeta('mNucleus'),
                'mHairSysDag':self.getMessageAsMeta('mHairSysDag'),
                'mHairSysShape':self.getMessageAsMeta('mHairSysShape'),
                'chains':{},
                }
        
        ml_chains = self.msgList_get('chain')
        for i,mGrp in enumerate(ml_chains):
            _d = {'mGrp':mGrp,
                  'mFollicle':mGrp.getMessageAsMeta('mFollicle'),
                  'mOutCrv':mGrp.getMessageAsMeta('mOutCrv'),
                  }
            
            for lnk in 'mLocs','mAims','mParents','mTargets':
                _d[lnk] = mGrp.msgList_get(lnk)
                
            _res['chains'][i] = _d
        
        pprint.pprint(_res)
        return _res
    
    def profile_load(self,arg='default'):
        mNucleus=self.getMessageAsMeta('mNucleus')
        mHairSysShape=self.getMessageAsMeta('mHairSysShape')
        if not mNucleus and mHairSysShape:
            return log.warning("Nucleus and hairShape required for profile load")
        
        _d = d_chainProfiles.get(arg)
        if not _d:
            return log.warning("Profile has no data: {0}".format(arg))
        
        
        d_n = _d.get('n') or {}
        d_hs = _d.get('hs') or {}
        
        pprint.pprint(_d)
        _nucleus = mNucleus.mNode
        for a,v in d_n.iteritems():
            log.debug("Nucleus || {0} | {1}".format(a,v))
            try:
                mNucleus.__setattr__(a,v)
            except Exception,err:
                log.warning("Nucleus | Failed to set: {0} | {1} | {2}".format(a,v,err))
                
        for a,v in d_hs.iteritems():
            log.debug("mHairSys || {0} | {1}".format(a,v))            
            try:
                mHairSysShape.__setattr__(a,v)
            except Exception,err:
                log.warning("mHairSys | Failed to set: {0} | {1} | {2}".format(a,v,err))
        
        return True
                
    def delete(self):
        pass        
        
        
        
d_chainProfiles = {'default':
                   {'n':
                    {'subSteps':12,
                    'maxCollisionIterations':49,
                    'gravity':98,
                    'gravityDirection':[0,-1,0]},
                    'hs':
                    {'bendFollow':1.0,
                     'hairWidth':1.2,
                     'solverDisplay':1,
                     'stretchResistance':105,
                     'drag':.1,
                     'tangentalDrag':.1,
                     }
                    },
                   'wind':
                   {'n':
                    {'windSpeed':900,
                                'windDirection':[0,0,-1],
                                'windNoise':5},
                    'hs':{'intensity':1.0,
                          'frequency':5.0,
                          'speed':.2}}}


#=========================================================================      
# R9 Stuff - We force the update on the Red9 internal registry  
#=========================================================================      
cgmMeta.r9Meta.registerMClassInheritanceMapping()