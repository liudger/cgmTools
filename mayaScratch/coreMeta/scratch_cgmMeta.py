import maya.cmds as mc
from cgm.core import cgm_Meta as cgmMeta
from cgm.core import cgm_PuppetMeta as cgmPM
import Red9.core.Red9_Meta as r9Meta
from cgm.core import cgm_General as cgmGeneral

import cgm.core
cgm.core._reload()

obj = mc.ls(sl=True)[0] or False
obj = ''
objList = []
orientation = ['xyz']
orientation[1]
cgmMeta.cgmObject(mc.ls(sl=True)[0]).doName()

mi_obj = cgmMeta.cgmObject(obj)
cgmMeta.validateObjArg(mi_obj,cgmMeta.cgmObject)
cgmMeta.validateObjArg(mi_obj)

cgmMeta.validateAttrArg([mi_obj,'tx'])
cgmMeta.validateAttrArg([obj,'tx'])
cgmMeta.validateAttrArg("%s.tx"%obj)

@cgmGeneral.Timer
def check(arg):
    issubclass(arg,cgmMeta.cgmNode):
        return True
    

cgmMeta.validateObjArg(obj)

#>>> verifyAttrDict
d_test = {'string':'string','messageSimple':'messageSimple','bool':'bool','enum':'left:right:center','float':'float'}
cgmMeta.cgmNode(name = 'test').verifyAttrDict(d_test,lock = True)
cgmMeta.cgmNode(name = 'test').verifyAttrDict(d_test,hidden = False,keyable= False)

#>>>cgmControl
obj = 'hips_controlCurve'
i_c = cgmMeta.cgmControl(obj,setClass=True)

#>>> Dynamic Match
dynObject = 'nurbsSphere1'
dynMatchTargets =  [u'pCube1', u'pCube2']
dynSnapTargets = ['worldCenter_loc']
dynNull = 'nurbsSphere1_dynMatchDriver'
a = cgmMeta.cgmDynamicMatch(dynObject=dynObject,dynMatchTargets = dynMatchTargets)
a = cgmMeta.cgmDynamicMatch(dynObject=dynObject,dynNull = dynNull)

a = cgmMeta.cgmDynamicMatch(dynObject=dynObject,dynMatchTargets = dynMatchTargets, dynSnapTargets = dynSnapTargets, dynPrefix = 'fkik')
a = cgmMeta.cgmDynamicMatch(dynObject=dynObject,dynNull = dynNull,dynSuffix = 'fkik')
a.getMessage('dynDrivers',False)
a.getMessage('dynTargets',False)
a.doMatch(1)
a.doMatch(0)
cgmMeta.cgmNode('nurbsSphere1').dynMatchDriver_fkik.doMatch(0)
cgmMeta.cgmNode('nurbsSphere1').dynMatchDriver_fkik.doMatch(1)

#>>> Dynamic group
#=======================================================
parents = mc.ls(sl=True)
dParents = [u'parent1', u'parent2', u'parent3']
dynMode = 'follow'
a = cgmRigMeta.cgmDynParentGroup(dynChild = 'dynChild',dynParents = dParents,dynMode = dynMode)
a.rebuild()
#Hips
dynParents = [ u'cog_anim',u'worldCenter_loc']#hips
dynGroup = 'hips_anim_grp'
dynChild = 'dynChild'

a = cgmRigMeta.cgmDynParentGroup(dynChild = dynChild,dynParents = dynParents, dynGroup = dynGroup,dynMode = dynMode)
#Shoulders
c1 = r9Meta.MetaClass('shoulders_ik_anim')
c1.dynParentGroup
c1.dynParentGroup.dynChild
c1.dynParentGroup.addDynChild('shoulders_ik_anim')
c1.dynParentGroup.rebuild()

dynParents = ['spine_2_fk_anim','cog_anim','|Morphy|Morphy_1_masterAnim','shoulders_ik_anim_spacePivot_anim','shoulders_ik_anim_spacePivot_1_anim']
for o in dynParents:
    c1.dynParentGroup.addDynParent(o)
c1.dynParentGroup.rebuild()


spineFK,cog,world,pivots
dynParents = [ u'spine_2_fk_anim',u'cog_anim',u'worldCenter_loc','pivotAnim']#Shoulderes
dynParents = [ u'spine_2_fk_anim',u'cog_anim',u'worldCenter_loc']#Shoulderes
dynParents = [ u'spine_2_fk_anim',u'cog_anim','hips_anim',u'worldCenter_loc']#Shoulderes
dynGroup = 'shoulders_ik_anim_grp'
dynChild = 'shoulders_ik_anim'
dynMode = 'follow'

#>>>
#================================================================
nf = cgmMeta.NameFactory

i_net1 = cgmMeta.cgmNode(name = 'net',nodeType = 'network')        
i_net1.addAttr('cgmName','net', attrType = 'string')
assert nf(i_net1).getBaseIterator() == 0,"baseIterator: %s"%nf(i_net1).getBaseIterator()

i_net2 = cgmMeta.cgmNode( mc.duplicate(i_net1.mNode)[0] )
assert nf(i_net1).getMatchedSiblings() == [i_net2],"%s"%nf(i_net1).getMatchedSiblings()
assert nf(i_net2).getMatchedSiblings() == [i_net1],"%s"%nf(i_net2).getMatchedSiblings()
assert nf(i_net1).getBaseIterator() == 1,"%s"%"baseIterator: %s"%nf(i_net1).getBaseIterator()
assert i_net1.getNameDict() == i_net2.getNameDict(),"Name dicts not equal"
assert nf(i_net1).getIterator() == 1
i_net1.doName(fastIterate = False)
assert nf(i_net2).getIterator() == 2
nf(i_net2).getIterator()
i_net1.getNameDict()
i_net2.getNameDict()
cgmMeta.log.setLevel(cgmMeta.logging.INFO)
cgmMeta.log.setLevel(cgmMeta.logging.DEBUG)
cgm.core._reload()

nf(i_net1).getFastIterator()
nf(i_net1).getIterator()

cgmMeta.cgmNode(mc.ls(sl=1)[0]).doName()
