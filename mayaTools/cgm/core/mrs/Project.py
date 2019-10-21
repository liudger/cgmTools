"""
skinDat
Josh Burton 
www.cgmonks.com

Core skinning data handler for cgm going forward.

Storing joint positions and vert positions so at some point can implement a method
to apply a skin without a reference object in scene if geo or joint counts don't match

Currently only regular skin clusters are storing...

Features...
- Skin data gather
- Read/write skin data to a readable config file
- Apply skinning data to geo of different vert count
- 

Thanks to Alex Widener for some ideas on how to set things up.

"""
__version__ = "10.01.2019"
__MAYALOCAL = 'CGMPROJECT'


# From Python =============================================================
import copy
import os
import pprint

#>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)

# From Maya =============================================================
import maya.cmds as mc
import maya.mel as mel
#import maya.OpenMaya as OM
#import maya.OpenMayaAnim as OMA

# From Red9 =============================================================
from Red9.core import Red9_Meta as r9Meta
import Red9.packages.configobj as configobj
import Red9.startup.setup as r9Setup    

# From cgm ==============================================================
from cgm.core import cgm_Meta as cgmMeta
from cgm.core import cgm_General as cgmGEN
from cgm.core.cgmPy import validateArgs as cgmValid
import cgm.core.classes.GuiFactory as cgmUI
import cgm.core.cgmPy.path_Utils as PATHS
import cgm.core.lib.string_utils as CORESTRINGS
import cgm.images as cgmImages
mImagesPath = PATHS.Path(cgmImages.__path__[0])

mUI = cgmUI.mUI


d_projectFramework = {
    'Art':{
    'Character':{},
    'Enviornment':{},
    'FX':{},
    'images':{},
    'mocap_library':{},
    'movies':{},
    'Poses':{},
    'Props':{},
    'UI':{},
    'visdev':{}
    },
    'audio':{
    'BGM':{},
    'Debug':{},
    'SFX':{},
    'UI':{}
    },
    'design':{},
    'media':{},
    'ref':{}
}

l_projectDat = ['name','type',]
l_projectTypes = ['asset','unity','unreal','commercial']
l_projectPaths = ['content','export','poses','image']

d_animSettings = {'fps':'int',
                  }
#RangeSlider|MainPlaybackRangeLayout|formLayout9|formLayout13|optionMenuGrp1
#timeField -e -v `playbackOptions -q -ast` RangeSlider|MainPlaybackRangeLayout|formLayout9|timeField2; timeField -e -v `playbackOptions -q -aet` RangeSlider|MainPlaybackRangeLayout|formLayout9|timeField5;

from cgm.lib import (search,
                     names,
                     cgmMath,
                     attributes,
                     rigging,
                     distance,
                     skinning)

class ui(cgmUI.cgmGUI):
    USE_Template = 'cgmUITemplate'
    WINDOW_NAME = 'cgmProjectManager'    
    WINDOW_TITLE = 'cgmProjectManager - {0}'.format(__version__)
    DEFAULT_MENU = None
    RETAIN = True
    MIN_BUTTON = True
    MAX_BUTTON = False
    FORCE_DEFAULT_SIZE = True  #always resets the size of the window when its re-created  
    DEFAULT_SIZE = 350,500
    TOOLNAME = 'cgmProjectManager.ui'
    
    def insert_init(self,*args,**kws):
        _str_func = '__init__[{0}]'.format(self.__class__.TOOLNAME)            
        log.info("|{0}| >>...".format(_str_func))        

        if kws:log.debug("kws: %s"%str(kws))
        if args:log.debug("args: %s"%str(args))
        log.info(self.__call__(q=True, title=True))

        self.__version__ = __version__
        self.__toolName__ = self.__class__.WINDOW_NAME	

        #self.l_allowedDockAreas = []
        self.WINDOW_TITLE = self.__class__.WINDOW_TITLE
        self.DEFAULT_SIZE = self.__class__.DEFAULT_SIZE
        
        self.pathProject = None
        self.mDat = data()
        self.path_projectConfig = None
        
        self.var_project = cgmMeta.cgmOptionVar('cgmVar_projectCurrent',defaultValue = '')
        self.var_pathProject = cgmMeta.cgmOptionVar('cgmVar_projectPath',defaultValue = '')
        
        self.mPathList = cgmMeta.pathList('cgmProjectPaths')
        
        self.d_tf = {}
        
    def uiProject_pushPaths(self):
        _str_func = 'uiProject_load'
        log.info("|{0}| >>...".format(_str_func))        
        
        mPath = PATHS.Path( self.d_tf['paths']['content'].getValue() )
        if mPath.exists():
            mel.eval('setProject "{0}";'.format(mPath.asString()))
        else:
            log.error('Invalid Path: {0}'.format(mPath))
            
    def uiProject_load(self,path=None,revert=False):
        _str_func = 'uiProject_load'
        log.info("|{0}| >>...".format(_str_func))
        
        if path == None and revert is True:
            path = self.path_projectConfig or self.mDat.str_filepath
            
        #if revert is not True:
        self.mDat.read(path)
        
        log.debug(cgmGEN.logString_sub(_str_func,"general"))
        for k,v in self.mDat.d_project.iteritems():
            log.info(cgmGEN.logString_msg(_str_func,"{0} | {1}".format(k,v)))
            try:
                self.d_tf['project'][k].setValue(v)
            except Exception,err:
                log.error("Missing data field: {0}".format(k))
                log.error("err | {0}".format(err))
                
                #mUi.setValue(v)
 
 
        log.debug(cgmGEN.logString_sub(_str_func,"paths"))
        for k,v in self.mDat.d_paths.iteritems():
            log.info(cgmGEN.logString_msg(_str_func,"{0} | {1}".format(k,v)))
            
            try:
                self.d_tf['paths'][k].setValue(v)
            except Exception,err:
                log.error("Missing data field: {0}".format(k))
                log.error("err | {0}".format(err))
        
        
        #Set maya project path
        log.debug(cgmGEN.logString_sub(_str_func,"Push Paths..."))
        self.uiProject_pushPaths()
        
        
        
        
        log.debug(cgmGEN.logString_sub(_str_func,"PathList append: {0}".format(self.mDat.str_filepath)))
        
        self.path_projectConfig = self.mDat.str_filepath
        self.mPathList.append(self.mDat.str_filepath)
        self.mPathList.log_self()        
        
        
        #Set pose path
        #Update file dir
        
        #Project image
        _imagePath = os.path.join(mImagesPath.asFriendly(),
                                  'cgm_project_{0}.png'.format(self.d_tf['project']['type'].getValue()))
        
        #self.uiImage_Project= mUI.MelImage(imageRow,w=350, h=50)
        self.uiImage_Project.setImage(_imagePath)        
        
        #self.uiImage_Project.setImage(mThumb)
        

        log.info(True)
        
    
    def uiProject_save(self, path = None, updateFile = False):
        _str_func = 'uiProject_save'
        log.debug("|{0}| >>...".format(_str_func))
        
        if path == None and updateFile:
            if self.mDat.str_filepath:
                log.info("|{0}| >> Saving to existing mDat: {1}".format(_str_func,self.mDat.str_filepath))
                path = self.mDat.str_filepath        
            
        for k,ui in self.d_tf['project'].iteritems():
            self.mDat.d_project[k] = ui.getValue()
            
        
        for k,ui in self.d_tf['paths'].iteritems():
            self.mDat.d_paths[k] = ui.getValue()
            
        self.mDat.log_self()
        
        self.mDat.write( self.path_projectConfig)
        
    def uiProject_saveAs(self):
        _str_func = 'uiProject_saveAs'
        log.debug("|{0}| >>...".format(_str_func))
        
        self.uiProject_save(None,True)
        
    def uiProject_revert(self):
        _str_func = 'uiProject_revert'
        log.debug("|{0}| >>...".format(_str_func))
        
        self.uiProject_load(None,True)    
    

    def build_menus(self):
        self.uiMenu_FirstMenu = mUI.MelMenu(l='Setup', pmc = cgmGEN.Callback(self.buildMenu_first))
        self.uiMenu_help = mUI.MelMenu(l='Help', pmc = cgmGEN.Callback(self.buildMenu_help))
        

    def buildMenu_first(self):
        self.uiMenu_FirstMenu.clear()
        
        #>>> Reset Options		                     
        mUI.MelMenuItemDiv( self.uiMenu_FirstMenu, label='Project' )
        mUI.MelMenuItem( self.uiMenu_FirstMenu, l="Load",
                         c = lambda *a:mc.evalDeferred(self.uiProject_load,lp=True))
        mUI.MelMenuItem( self.uiMenu_FirstMenu, l="Save ",
                         c = lambda *a:mc.evalDeferred(self.uiProject_save,lp=True))
        mUI.MelMenuItem( self.uiMenu_FirstMenu, l="Save As",
                         c = lambda *a:mc.evalDeferred(self.uiProject_saveAs,lp=True))        
        mUI.MelMenuItem( self.uiMenu_FirstMenu, l="Revert",
                         c = lambda *a:mc.evalDeferred(self.uiProject_revert,lp=True))
        
        self.mPathList.verify()
        _recent = mUI.MelMenuItem( self.uiMenu_FirstMenu, l="Recent",subMenu=True)
        for i,p in enumerate(self.mPathList.l_paths):
            mUI.MelMenuItem(_recent,
                            label = PATHS.Path(p).asTruncate(2,3),
                            ann = "Set the project to: {0} | {1}".format(i,p),
                            c=cgmGEN.Callback(self.uiProject_load,p))
            
        mUI.MelMenuItemDiv(_recent)
        mUI.MelMenuItem(_recent,
                        label = "Clear Recent",
                        ann="Clear the recent projects",
                        c=cgmGEN.Callback(self.mPathList.clear))        
        
        
        mUI.MelMenuItemDiv( self.uiMenu_FirstMenu, label='Settings' )
        #uiMenuItem_matchMode(self,self.uiMenu_FirstMenu)
        
        mUI.MelMenuItemDiv( self.uiMenu_FirstMenu, label='Utils' )
        
        mUI.MelMenuItem( self.uiMenu_FirstMenu, l="Dock",
                         c = lambda *a:self.do_dock())        

        mUI.MelMenuItem( self.uiMenu_FirstMenu, l="Reload",
                         c = lambda *a:mc.evalDeferred(self.reload,lp=True))
        mUI.MelMenuItem( self.uiMenu_FirstMenu, l="Reset",
                         c = lambda *a:mc.evalDeferred(self.reload,lp=True))
        
    def buildMenu_help( self, *args):
        self.uiMenu_help.clear()
        
        _log = mUI.MelMenuItem( self.uiMenu_help, l="Logs:",subMenu=True)
        
        
        mUI.MelMenuItem( _log, l="Dat",
                         c=lambda *a: self.mDat.log_self())
        mUI.MelMenuItem( _log, l="PathList",
                         c=lambda *a: self.mPathList.log_self())
        
        mc.menuItem(parent=self.uiMenu_help,
                    l = 'Get Help',
                    c='import webbrowser;webbrowser.open("https://http://docs.cgmonks.com/mrs.html");',                        
                    rp = 'N')    
        mUI.MelMenuItem( self.uiMenu_help, l="Log Self",
                         c=lambda *a: cgmUI.log_selfReport(self) )   

        
    def build_layoutWrapper(self,parent):
        _str_func = 'build_layoutWrapper'
    
        _MainForm = mUI.MelFormLayout(self,ut='cgmUITemplate')
        
        _column = mUI.MelScrollLayout(parent=_MainForm)
        self.bUI_main(_column)
        #self.mManager = manager(parent = _column)
        
        #for k in self.__dict__.keys():
        #    if str(k).startswith('var_'):
        #        self.mManager.__dict__[k] = self.__dict__[k]
        
        _row_cgm = cgmUI.add_cgmFooter(_MainForm)            
        _MainForm(edit = True,
                  af = [(_column,"top",0),
                        (_column,"left",0),
                        (_column,"right",0),
                        (_row_cgm,"left",0),
                        (_row_cgm,"right",0),                        
                        (_row_cgm,"bottom",0),
    
                        ],
                  ac = [#(_column,"top",2,_context),
                        (_column,"bottom",2,_row_cgm),
                        ],
                  attachNone = [(_row_cgm,"top")])
        
    def bUI_main(self,parent):
        #self.mLabel_projectName = mUI.MelLabel(parent,label='Project X'.upper(), al = 'center', ut = 'cgmUIHeaderTemplate')
        
        
        '''
        #Pose Path ===============================================================================
        uiRow_pose = mUI.MelHSingleStretchLayout(parent,ut='cgmUISubTemplate')
        self.uiPop_root = None
        
        mUI.MelSpacer(uiRow_pose,w=2)    
        
        mUI.MelLabel(uiRow_pose,label='Root:')
        mUI.MelSpacer(uiRow_pose,w=2)    
        """
        self.uiField_path = mUI.MelLabel(uiRow_pose,
                                         ann='Change the current path',
                                         label = 'None',
                                         ut='cgmUIInstructionsTemplate',w=100) """   
        
        
        self.tf_projectPath = mUI.MelTextField(uiRow_pose,
                                               ann='The root path for our project',
                                               #cc = lambda *x:self._uiCB_setPosePath(field=False),
                                               text = '')
                                                 
        uiRow_pose.setStretchWidget(self.tf_projectPath)
        
        mc.button(parent=uiRow_pose,
                  l = 'Set Path',
                  ut = 'cgmUITemplate',
                  c= lambda *x:self.uiCB_setProjectPath(fileDialog=True),
                  #en = _d.get('en',True),
                  #c = cgmGEN.Callback(uiCB_contextualAction,self,**_arg),
                  #ann = _d.get('ann',b))
                  )
        """
        mc.button(parent=uiRow_pose,
                  l = 'Test',
                  ut = 'cgmUITemplate',
                  c= lambda *x:log.info("Mode: {0} | local: {1} | project: {2}".format(self.var_pathMode.getValue(),self.posePathLocal, self.posePathProject)),
                  )"""
        mUI.MelSpacer(uiRow_pose,w=2)
        uiRow_pose.layout()
        mc.setParent(self)
        '''
        
        # Image
        _imageFailPath = os.path.join(mImagesPath.asFriendly(),'cgm_project.png')
        imageRow = mUI.MelHRowLayout(parent,bgc=[.6,.3,.3])
        
        #mUI.MelSpacer(imageRow,w=10)
        self.uiImage_Project= mUI.MelImage(imageRow,w=350, h=50)
        self.uiImage_Project.setImage(_imageFailPath)
        #mUI.MelSpacer(imageRow,w=10)	
        imageRow.layout()        
        
        #self.uiPopup_setPath()
        
        self.buildFrame_baseDat(parent)
        self.buildFrame_paths(parent)
        self.buildFrame_content(parent)
        
    def uiCB_setProjectPath(self, path=None, field = False, fileDialog=False):
        '''
        Manage the PosePath textfield and build the PosePath
        '''
        _str_func = 'uiCB_setProjectPath'
        
        mVar = self.var_pathProject
    
        if not path and not field and not fileDialog:
            self.pathProject = mVar.getValue()
        
        if path:
            self.pathProject = path
            
        elif fileDialog:
            log.debug("|{0}| >> file dialog mode...".format(_str_func))
            try:
                if r9Setup.mayaVersion() >= 2011:
                    _dir = self.tf_projectPath.getValue() or ''
                    log.debug("|{0}| >> dir: {1}".format(_str_func,_dir))                    
                    self.pathProject = mc.fileDialog2(fileMode=3,
                                                   dir=_dir)[0]
                else:
                    print 'Sorry Maya2009 and Maya2010 support is being dropped'
                    def setPosePath(fileName, fileType):
                        self.pathProject = fileName
                    mc.fileBrowserDialog(m=4, fc=setPosePath, ft='image', an='setPoseFolder', om='Import')
            except Exception,err:
                log.warning('No Folder Selected or Given | {0}'.format(err))
        elif field:
            self.pathProject = self.tf_projectPath.getValue()
        
        if not PATHS.Path(self.pathProject):
            log.error("|{0}| >> Invalid path: {1}".format(_str_func,self.pathProject))            
            self.pathProject = ''
            return 
        
        mVar.setValue(self.pathProject)
        
        self.tf_projectPath.setValue(self.pathProject,executeChangeCB=False)
        self.tf_projectPath(edit=True, ann = self.pathProject)
        


        #self.uiScrollList_dir.rebuild(self.posePath)

        return    
    
    def buildFrame_baseDat(self,parent):
        try:self.var_projectBaseDatCollapse
        except:self.create_guiOptionVar('projectBaseDatCollapse',defaultValue = 0)
        mVar_frame = self.var_projectBaseDatCollapse
        
        _frame = mUI.MelFrameLayout(parent,label = 'General',vis=True,
                                    collapse=mVar_frame.value,
                                    collapsable=True,
                                    enable=True,
                                    useTemplate = 'cgmUIHeaderTemplate',
                                    expandCommand = lambda:mVar_frame.setValue(0),
                                    collapseCommand = lambda:mVar_frame.setValue(1)
                                    )	
        _inside = mUI.MelColumnLayout(_frame,useTemplate = 'cgmUISubTemplate') 
        
        #>>>Hold ===================================================================================== 
        cgmUI.add_LineSubBreak()
        self.d_tf['project'] = {}
        _d = self.d_tf['project']
        for key in l_projectDat:
            mUI.MelSeparator(_inside,ut='cgmUISubTemplate',h=3)
            
            _row = mUI.MelHSingleStretchLayout(_inside,ut='cgmUISubTemplate',padding = 5)
            mUI.MelSpacer(_row,w=5)                          
            mUI.MelLabel(_row,l='{0}: '.format(CORESTRINGS.capFirst(key)))            
            if key == 'type':
                _d[key] = mUI.MelOptionMenu(_row,ut = 'cgmUITemplate')
                
                for t in l_projectTypes:
                    _d[key].append(t)
        
                #_d[key].selectByIdx(self.setMode,False)                
                
                
            else:
                #_rowContextKeys.setStretchWidget( mUI.MelSeparator(_rowContextKeys) )
                _d[key] =  mUI.MelTextField(_row,
                                            ann='Project settings | {0}'.format(key),
                                            text = '')
                
            _row.setStretchWidget(_d[key])
            mUI.MelSpacer(_row,w=5)
            _row.layout()
            
    def buildFrame_paths(self,parent):
        try:self.var_projectPathsCollapse
        except:self.create_guiOptionVar('projectPathsCollapse',defaultValue = 0)
        mVar_frame = self.var_projectPathsCollapse
        
        _frame = mUI.MelFrameLayout(parent,label = 'Paths',vis=True,
                                    collapse=mVar_frame.value,
                                    collapsable=True,
                                    enable=True,
                                    useTemplate = 'cgmUIHeaderTemplate',
                                    expandCommand = lambda:mVar_frame.setValue(0),
                                    collapseCommand = lambda:mVar_frame.setValue(1)
                                    )	
        _inside = mUI.MelColumnLayout(_frame,useTemplate = 'cgmUISubTemplate') 
        
        #>>>Hold ===================================================================================== 
        cgmUI.add_LineSubBreak()
        self.d_tf['paths'] = {}
        _d = self.d_tf['paths']
        
        for key in l_projectPaths:
            mUI.MelSeparator(_inside,ut='cgmUISubTemplate',h=3)
            
            _row = mUI.MelHSingleStretchLayout(_inside,ut='cgmUISubTemplate',padding = 5)

            mUI.MelSpacer(_row,w=5)                          
            mUI.MelLabel(_row,l='{0}: '.format(CORESTRINGS.capFirst(key)))            
            #_rowContextKeys.setStretchWidget( mUI.MelSeparator(_rowContextKeys) )
            _d[key] =  mUI.MelTextField(_row,
                                        ann='Project Path | {0}'.format(key),
                                        text = '')
            
            mc.button(parent=_row,
                      l = 'Set',
                      ut = 'cgmUITemplate',
                      c = cgmGEN.Callback(self.uiButton_setPathToTextField,key)
                      #en = _d.get('en',True),
                      #c = cgmGEN.Callback(uiCB_contextualAction,self,**_arg),
                      #ann = _d.get('ann',b))
                      )            
            
            _row.setStretchWidget(_d[key])
            mUI.MelSpacer(_row,w=5)
            _row.layout()

    def buildFrame_content(self,parent):
        try:self.var_projectContentCollapse
        except:self.create_guiOptionVar('projectContentCollapse',defaultValue = 0)
        mVar_frame = self.var_projectContentCollapse
        
        _frame = mUI.MelFrameLayout(parent,label = 'Content',vis=True,
                                    collapse=mVar_frame.value,
                                    collapsable=True,
                                    enable=True,
                                    useTemplate = 'cgmUIHeaderTemplate',
                                    expandCommand = lambda:mVar_frame.setValue(0),
                                    collapseCommand = lambda:mVar_frame.setValue(1)
                                    )	
        _inside = mUI.MelColumnLayout(_frame,useTemplate = 'cgmUISubTemplate') 
        
        return
        #>>>Hold ===================================================================================== 
        cgmUI.add_LineSubBreak()
        self.d_tf['content'] = {}
        _d = self.d_tf['paths']
        
        for key in l_projectPaths:
            _row = mUI.MelHSingleStretchLayout(_inside,ut='cgmUISubTemplate',padding = 5)

            mUI.MelSpacer(_row,w=5)                          
            mUI.MelLabel(_row,l='{0}: '.format(key))
            #_rowContextKeys.setStretchWidget( mUI.MelSeparator(_rowContextKeys) )
            _d[key] =  mUI.MelTextField(_row,
                                        ann='Project Path | {0}'.format(key),
                                        text = '')
            
            mc.button(parent=_row,
                      l = 'Set',
                      ut = 'cgmUITemplate',
                      c = cgmGEN.Callback(self.uiButton_setPathToTextField,key)
                      #c = lambda *x:self.uiButton_setPathToTextField(key),
                      #c= lambda *x:self.uiCB_setProjectPath(fileDialog=True),
                      #en = _d.get('en',True),
                      #c = cgmGEN.Callback(uiCB_contextualAction,self,**_arg),
                      #ann = _d.get('ann',b))
                      )            
            
            _row.setStretchWidget(_d[key])
            mUI.MelSpacer(_row,w=5)
            _row.layout()
    
    def uiButton_setPathToTextField(self,key):
        basicFilter = "*"
        x = mc.fileDialog2(fileFilter=basicFilter, dialogStyle=2, fm=3)
        if x:
            self.d_tf['paths'][key].setValue( x[0] )
            #self.optionVarExportDirStore.setValue( self.exportDirectory )    


class data(object):
    '''
    Class to handle skin data. Utilizes red9.packages.ConfigObj for storage format. Storing what might be an excess of info
    to make it more useful down the road for applying skinning data to meshes that don't have the same vert counts or joint counts.
    
    :param sourchMesh: Mesh to export data from
    :param targetMesh: Mesh to import data to
    :param filepath: File to read on call or via self.read() call to browse to one
    
    '''    
    _configToStored = {'general':'d_project',
                       'enviornment':'d_env',
                       'paths':'d_paths',
                       'animSettings':'d_animSettings'}
    _geoToComponent = {'mesh':'vtx'}
    
    
    def __init__(self, project = None, filepath = None, **kws):
        """

        """        
        self.str_filepath = None
        self.d_env = cgmGEN.get_mayaEnviornmentDict()
        self.d_env['file'] = mc.file(q = True, sn = True)
        self.d_project = {}
        self.d_animSettings = {}
        self.d_paths = {}
        
        if filepath is not None:
            try:self.read(filepath)
            except:log.error("Filepath failed to read.")
            
            
        return
        if sourceMesh is not None:
            self.validateSourceMesh(sourceMesh)
        if targetMesh is not None:
            self.validateTargetMesh(targetMesh)
        if sourceMesh is None and targetMesh is None and mc.ls(sl=True):
            self.validateSourceMesh(sourceMesh)            

    @classmethod   
    def validateMeshArg(self, mesh = None):
        '''
        Validates a mesh and returns a dict of data
        
        :param mesh: mesh to evaluate
        
        '''        
        _mesh = None 
        _skin = None
        if mesh is None:
            #if self.d_kws.get('sourceMesh'):
                #log.info("Using stored sourceMesh data")
                #sourceMesh = self.d_kws.get('sourceMesh')
            #else:
            log.info("No source specified, checking if selection found")
            _bfr = mc.ls(sl=True)
            if not _bfr:raise ValueError,"No selection found and no source arg"
            mesh = _bfr[0]
            
        _type = search.returnObjectType(mesh)
        
        if _type in ['mesh', 'nurbsCurve', 'nurbsSurface']:
            if _type in ['nurbsCurve','nurbsSurface']:
                raise  NotImplementedError, "Haven't implemented nurbsCurve or nurbsSurface yet"
            log.info("Skinnable object '{0}', checking skin".format(mesh))
            _mesh = mesh
            _skin = skinning.querySkinCluster(_mesh) or False
            if _skin:
                log.info("Found skin '{0}' on '{1}'".format(_skin,_mesh))
        elif _type in ['skinCluster']:
            log.info("skinCluster '{0}' passed...".format(mesh))
            _skin = mesh
            _mesh = attributes.doGetAttr(_skin,'outputGeometry')[0]
            log.info("Found: {0}".format(_mesh))
        else:
            raise ValueError,"Not a usable mesh type : {0}".format(_type)
        
        _shape = mc.listRelatives(_mesh,shapes=True,fullPath=False)[0]
        _return = {'mesh':_mesh,
                   'meshType':_type,
                   'shape':_shape,
                   'skin':_skin,
                   'component':data._geoToComponent.get(_type, False),
                   'pointCount':mc.polyEvaluate(_shape, vertex=True)
                   }
        return _return  

    def validateFilepath(self, filepath = None, fileMode = 0):
        '''
        Validates a given filepath or generates one with dialog if necessary
        '''        
        if filepath is None:
            startDir = mc.workspace(q=True, rootDirectory=True)
            filepath = mc.fileDialog2(dialogStyle=2, fileMode=fileMode, startingDirectory=startDir,
                                      fileFilter='Config file (*.cfg)')
            if filepath:filepath = filepath[0]
            
        if filepath is None:
            return False
        self.str_filepath = str(filepath)
        log.info("filepath validated...")        
        return filepath

    def write(self, filepath = None, update = False):
        '''
        Write the Data ConfigObj to file
        '''
        if update:
            filepath = self.str_filepath
            
        filepath = self.validateFilepath(filepath)
            
        ConfigObj = configobj.ConfigObj(indent_type='\t')
        ConfigObj['configType']= 'cgmProject'
        for k in data._configToStored.keys():
            ConfigObj[k] = self.__dict__[data._configToStored[k]] 
        
        ConfigObj.filename = filepath
        ConfigObj.write()
        
        if update:
            self.str_filepath = filepath
        return True
        
    def read(self, filepath = None, report = False):
        '''
        Read the Data ConfigObj from file and report the data if so desired.
        '''        
        filepath = self.validateFilepath(filepath, fileMode = 1)
        if not os.path.exists(filepath):            
            raise ValueError('Given filepath doesnt not exist : %s' % filepath)   
        
        _config = configobj.ConfigObj(filepath)
        #if _config.get('configType') != 'cgmSkinConfig':
            #raise ValueError,"This isn't a cgmSkinConfig config | {0}".format(filepath)
                
        for k in data._configToStored.keys():
            if _config.has_key(k):
                self.__dict__[data._configToStored[k]] = _config[k]
            else:
                log.error("Config file missing section {0}".format(k))
                return False
            
        if report:self.log_self()
        self.str_filepath = filepath
        
        return True
    
    def log_self(self):
        _d = copy.copy(self.__dict__)
        pprint.pprint(_d)
        

        
#>>> Utilities
#===================================================================
