import maya.cmds as mc
from cgm.core import cgm_Meta as cgmMeta

import cgm.core.mrs.RigBlocks as RBLOCKS
import cgm.core.mrs.lib.block_utils as BLOCKUTILS
import cgm.core.cgm_General as cgmGEN
import cgm.core.mrs.lib.shared_dat as BLOCKSHARE
cgm.core._reload()

#Let's start with a box or a sphere in scene. select that and then...
b1 = cgmMeta.createMetaNode('cgmRigBlock',name = 'Peter', blockType = 'master', size = 'selection')
b1 # THis will show you a simple read of our metaNode
b1 = cgmMeta.asMeta('Peter_masterBlock')#...this reinitializes our master rigBlock

#...here are the calls to walk through the states. This is a proprty call for b1.changeState() if you prefer that method
b1.p_blockState = 'define'
b1.p_blockState = 'template'
b1.p_blockState = 'prerig'
b1.p_blockState = 'rig'

#There are a series of calls where we can call libraries or specific function sets from our main instance
b1.atUtils #...this accesses cgm.core.mrs.lib.block_utils
b1.atBlockModule #...this accesses cgm.core.mrs.blocks then our block types specific module
b1.atRigModule #...this accesses cgm.core.mrs.lib.module_utils via a connected cgmRigModule to a message attr called moduleTarget
b1.atRigPuppet #...' ' ' '                       .puppet_utils via a connected cgmRigPuppet
b1.asHandleFactory #...cgm.core.mrs.RigBlocks.handleFactory. Need to bridge to access in places that would be import loops. We'll use this in rigging


import cgm.core.lib.curve_Utils as CURVES
reload(CURVES)
CURVES.create_fromName('squareOpen', size = 1)
CURVES.create_controlCurve(b1.mNode, 'circle')

#>>>Get Call size
RBLOCKS.get_callSize()
RBLOCKS.get_callSize('bb')
RBLOCKS.get_callSize('bb')
RBLOCKS.get_callSize(3)
RBLOCKS.get_callSize([1,2,3])
RBLOCKS.get_callSize(None)

#>>>Skeleton ---------------------------------------------------------------------------------------
b1.atBlockModule('build_skeleton')
b1.atBlockUtils('skeleton_getCreateDict')

#>>>Rig process ----------------------------------------------------------------
b1.verify()

mRigFac = RBLOCKS.rigFactory(b1)
mRigFac.log_self()#>>uses pprint
mRigFac.mRigNull.fkHeadJoint
pprint.pprint(b1.__dict__)
mRigFac.mRigNull.headFK.dynParentGroup

mRigFac.atBlockModule('rig_skeleton')

mRigFac.atBlockModule('build_proxyMesh', False)#must have rig joints


mRigFac.atBlockModule('rig_shapes')
mRigFac.atBlockModule('rig_controls')
mRigFac.atBlockModule('rig_neckSegment')
mRigFac.atBlockModule('rig_frame')
mRigFac.atBlockModule('rig_cleanUp')

import cgm.core.lib.attribute_utils as ATTR
ATTR.datList_connect(b1.mNode, 'baseNames', ['head'], mode='string')

b1.atBlockUtils('pivots_setup', pivotResult = 'pivotResult_driver')
