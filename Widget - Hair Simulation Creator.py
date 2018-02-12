from maya import cmds

if int( cmds.about( v=1 ) ) < 2017:
    from PySide import QtGui, QtCore
    import shiboken
    from PySide.QtGui import QListWidgetItem, QDialog, QListWidget, QMainWindow, QWidget, QColor, QLabel,\
    QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton, QAbstractItemView, QMenu,QCursor, QMessageBox, QBrush, QSplitter,\
    QScrollArea, QSizePolicy, QTextEdit, QApplication, QFileDialog, QCheckBox, QDoubleValidator, QSlider, QIntValidator,\
    QImage, QPixmap, QTransform, QPaintEvent, QTabWidget, QFrame, QTreeWidgetItem, QTreeWidget, QComboBox, QGroupBox, QAction,\
    QFont, QGridLayout
else:
    from PySide2 import QtGui, QtCore, QtWidgets
    import shiboken2 as shiboken
    from PySide2.QtWidgets import QListWidgetItem, QDialog, QListWidget, QMainWindow, QWidget, QVBoxLayout, QLabel,\
    QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton, QAbstractItemView, QMenu, QMessageBox, QSplitter,\
    QScrollArea, QSizePolicy, QTextEdit, QApplication, QFileDialog, QCheckBox, QSlider,\
    QTabWidget, QFrame, QTreeWidgetItem, QTreeWidget, QComboBox, QGroupBox, QAction, QGridLayout
    
    from PySide2.QtGui import QColor, QCursor, QBrush, QDoubleValidator, QIntValidator, QImage, QPixmap, QTransform,\
    QPaintEvent, QFont




from maya import OpenMayaUI, OpenMaya, mel, cmds
import pymel.core
import json, os



class BaseValues:
    
    expressionname = 'ex_hairSimulationCreator'
    allgroupname = 'hairSimulationCreator_grp'
    translatorMessageName = 'translateTarget'



class BaseCommands:
    
    @staticmethod
    def makeFolder( pathName ):
        if os.path.exists( pathName ):return None
        os.makedirs( pathName )
        return pathName


    @staticmethod
    def makeFile( filePath ):
        if os.path.exists( filePath ): return None
        filePath = filePath.replace( "\\", "/" )
        splits = filePath.split( '/' )
        folder = '/'.join( splits[:-1] )
        BaseCommands.makeFolder( folder )
        f = open( filePath, "w" )
        json.dump( {}, f )
        f.close()

    
    @staticmethod
    def writeData( data, filePath ):
        BaseCommands.makeFile( filePath )
        f = open( filePath, 'w' )
        json.dump( data, f, indent=2 )
        f.close()
    
    
    @staticmethod
    def readData( filePath ):
        BaseCommands.makeFile( filePath )
        
        f = open( filePath, 'r' )
        data = {}
        try:
            data = json.load( f )
        except:
            pass
        f.close()
        
        return data
    
    
    @staticmethod
    def addAttr( target, **options ):
    
        items = options.items()
        
        attrName = ''
        channelBox = False
        keyable = False
        for key, value in items:
            if key in ['ln', 'longName']:
                attrName = value
            elif key in ['cb', 'channelBox']:
                channelBox = True
                options.pop( key )
            elif key in ['k', 'keyable']:
                keyable = True 
                options.pop( key )
        
        if pymel.core.attributeQuery( attrName, node=target, ex=1 ): return None
        
        pymel.core.addAttr( target, **options )
        
        if channelBox:
            pymel.core.setAttr( target+'.'+attrName, e=1, cb=1 )
        elif keyable:
            pymel.core.setAttr( target+'.'+attrName, e=1, k=1 )
    
    
    @staticmethod
    def addOptionAttribute( inputTarget, enumName = "Options" ):
    
        target = pymel.core.ls( inputTarget )[0]
        
        barString = '____'
        while pymel.core.attributeQuery( barString, node=target, ex=1 ):
            barString += '_'
        
        target.addAttr( barString,  at="enum", en="%s:" % enumName )
        target.attr( barString ).set( e=1, cb=1 )


    @staticmethod
    def createBaseCurve( inputCtls ):
        
        ctls = [ pymel.core.ls( inputCtl )[0] for inputCtl in inputCtls ]
        
        if not pymel.core.pluginInfo( 'matrixNodes.mll', q=1, l=1 ):
            pymel.core.loadPlugin( "matrixNodes.mll" )
        
        def listToMatrix( mtxList ):
            if type( mtxList ) == OpenMaya.MMatrix:
                return mtxList
            matrix = OpenMaya.MMatrix()
            if type( mtxList ) == list:
                resultMtxList = mtxList
            else:
                resultMtxList = []
                for i in range( 4 ):
                    for j in range( 4 ):
                        resultMtxList.append( mtxList[i][j] )
            
            OpenMaya.MScriptUtil.createMatrixFromList( resultMtxList, matrix )
            return matrix
        
        
        def getConstrainMatrix( inputFirst, inputTarget ):
            first = pymel.core.ls( inputFirst )[0]
            target = pymel.core.ls( inputTarget )[0]
            mm = pymel.core.createNode( 'multMatrix' )
            first.wm >> mm.i[0]
            target.pim >> mm.i[1]
            return mm
        
        
        def getDecomposeMatrix( matrixAttr ):
            
            matrixAttr = pymel.core.ls( matrixAttr )[0]
            cons = matrixAttr.listConnections( s=0, d=1, type='decomposeMatrix' )
            if cons: 
                pymel.core.select( cons[0] )
                return cons[0]
            decomposeMatrix = pymel.core.createNode( 'decomposeMatrix' )
            matrixAttr >> decomposeMatrix.imat
            return decomposeMatrix
        
        
        def constrain_all( first, target, connectShear=False ):
            
            mm = getConstrainMatrix( first, target )
            dcmp = getDecomposeMatrix( mm.matrixSum )
            cmds.connectAttr( dcmp + '.ot',  target + '.t', f=1 )
            cmds.connectAttr( dcmp + '.or',  target + '.r', f=1 )
            cmds.connectAttr( dcmp + '.os',  target + '.s', f=1 )
            if connectShear:cmds.connectAttr( dcmp + '.osh',  target + '.s', f=1 )
        
        
        def setTransformDefault( inputTarget ):
            target = pymel.core.ls( inputTarget )[0]
            attrs = ['tx','ty','tz','rx','ry','rz','sx','sy','sz']
            values = [0,0,0,0,0,0,1,1,1]
            for i in range( len( attrs ) ):
                try:cmds.setAttr( target + '.' + attrs[i], values[i] )
                except:pass
        
        base    = ctls[0].getParent()
        baseMtx = listToMatrix( base.wm.get() )
        
        curveBase = pymel.core.createNode( 'transform' )
        constrain_all( base, curveBase )
        
        poses = []
        for sel in ctls:
            pos = OpenMaya.MPoint( *pymel.core.xform( sel, q=1, ws=1, t=1 ) )
            
            localPos = pos * baseMtx.inverse()
            poses.append( [ localPos.x, localPos.y, localPos.z ] )
        
        
        curve = pymel.core.curve( ep=poses )
        curve.setParent( curveBase )
        setTransformDefault( curve )
        
        return curve, curveBase
    
    
    @staticmethod
    def makeDynamicCurve( curve, curveBase ):
        
        def setTransformDefault( target ):
            defaultMatrix = [1,0,0,0, 0,1,0,0, 0,0,1,0, 0,0,0,1 ]
            pymel.core.xform( target, os=1, matrix=defaultMatrix )
        
        curveShape = curve.getShape()
        nodeRebuild = pymel.core.createNode( 'rebuildCurve' )
        
        nodeRebuild.attr( 'rebuildType' ).set( 0 )
        nodeRebuild.attr( 'degree' ).set( 1 )
        nodeRebuild.attr( 'endKnots' ).set( 1 )
        nodeRebuild.attr( 'keepRange' ).set( 0 )
        nodeRebuild.attr( 'keepControlPoints' ).set( 1 )
        nodeRebuild.attr( 'keepEndPoints' ).set( 1 )
        
        ioCurve = pymel.core.createNode( 'nurbsCurve' )
        
        curveShape.local >> nodeRebuild.inputCurve
        nodeRebuild.outputCurve >> ioCurve.create
        
        ioCurve.io.set( 1 )
        ioCurveParent = ioCurve.getParent()
        
        pymel.core.parent( ioCurve, curve, add=1, shape=1 )
        
        follicleShape = pymel.core.createNode( 'follicle' )
        ioCurve.local >> follicleShape.attr( 'startPosition' )
        curve.wm >> follicleShape.attr( 'startPositionMatrix' )
        
        trGeo = pymel.core.createNode( 'transformGeometry' )
        follicleShape.outCurve >> trGeo.inputGeometry
        curve.wim >> trGeo.transform
        
        dynamicCurveShape = pymel.core.createNode( 'nurbsCurve' )
        dynamicCurve = dynamicCurveShape.getParent()
        trGeo.outputGeometry >> dynamicCurveShape.attr( 'create' )
        
        follicle = follicleShape.getParent()
        follicle.setParent( curveBase )
        setTransformDefault( follicle )
        curve.setParent( follicle )
        dynamicCurve.setParent( curveBase )
        setTransformDefault( dynamicCurve )
        curve.v.set( 0 )
        pymel.core.delete( ioCurveParent )
        
        follicleShape.restPose.set( 1 )
        follicleShape.startDirection.set( 1 )
        
        return dynamicCurve, follicle



    @staticmethod
    def createSymmnulationSystem( follicles ):
        
        hairSystemNode = pymel.core.createNode( 'hairSystem' )
        for i in range( len( follicles ) ):
            follicle = follicles[i]
            follicle.outHair >> hairSystemNode.inputHair[i]
            hairSystemNode.outputHair[i] >> follicle.currentPosition
        nucleus = pymel.core.createNode( 'nucleus' )
        hairSystemNode.startState >> nucleus.inputActiveStart[0]
        hairSystemNode.currentState >> nucleus.inputActive[0]
        nucleus.startFrame >> hairSystemNode.startFrame
        nucleus.outputObjects[0] >> hairSystemNode.nextState
        pymel.core.ls( 'time1' )[0].outTime >> nucleus.currentTime
        pymel.core.ls( 'time1' )[0].outTime >> hairSystemNode.currentTime
        return hairSystemNode.getParent(), nucleus



    @staticmethod
    def createCtlsTranslators( inputCtls, inputCurve, inputCurveBase ):
        
        ctls = [ pymel.core.ls( inputCtl )[0] for inputCtl in inputCtls ]
        curve = pymel.core.ls( inputCurve )[0]
        curveBase = pymel.core.ls( inputCurveBase )[0]
        
        def getDagPath( inputTarget ):
            target = pymel.core.ls( inputTarget )[0]
            dagPath = OpenMaya.MDagPath()
            selList = OpenMaya.MSelectionList()
            selList.add( target.name() )
            try:
                selList.getDagPath( 0, dagPath )
                return dagPath
            except:
                return None


        def getMPoint( inputSrc ):
            
            if type( inputSrc ) in [ type( OpenMaya.MVector() ), type( OpenMaya.MPoint() ) ]:
                return OpenMaya.MPoint( inputSrc )
            elif type( inputSrc ) == list:
                return OpenMaya.MPoint( *inputSrc )
            return OpenMaya.MPoint( *pymel.core.xform( inputSrc, q=1, ws=1, t=1 ) )


        def getClosestParamAtPoint( inputTargetObj, inputCurve ):
    
            curve = pymel.core.ls( inputCurve )[0]
            
            if curve.nodeType() == 'transform':
                crvShape = curve.getShape()
            else:
                crvShape = curve
            
            if type( inputTargetObj ) in [ list, type( OpenMaya.MPoint() ), type( OpenMaya.MVector() ) ]:
                pointTarget = getMPoint( inputTargetObj )
            else:
                targetObj = pymel.core.ls( inputTargetObj )[0]
                dagPathTarget = getDagPath( targetObj )
                mtxTarget = dagPathTarget.inclusiveMatrix()
                pointTarget = OpenMaya.MPoint( mtxTarget[3] )
                
            
            dagPathCurve  = getDagPath( crvShape )
            mtxCurve  = dagPathCurve.inclusiveMatrix()
            pointTarget *= mtxCurve.inverse()
            
            fnCurve = OpenMaya.MFnNurbsCurve( getDagPath( crvShape ) )
            
            util = OpenMaya.MScriptUtil()
            util.createFromDouble( 0.0 )
            ptrDouble = util.asDoublePtr()
            fnCurve.closestPoint( pointTarget, 0, ptrDouble )
            
            paramValue = OpenMaya.MScriptUtil().getDouble( ptrDouble )
            return paramValue
        
        def attachToCurve( inputTargetObj, inputCurve, connectTangent=False ):
            targetObj = pymel.core.ls( inputTargetObj )[0]
            curve = pymel.core.ls( inputCurve )[0]
            
            if curve.nodeType() == 'transform':
                crvShape = curve.getShape()
            else:
                crvShape = curve
            
            param = getClosestParamAtPoint( targetObj, curve )
            curveInfo = pymel.core.createNode( 'pointOnCurveInfo' )
            
            crvShape.ws >> curveInfo.inputCurve
            targetObj.addAttr( 'param', min=crvShape.minValue.get(), max=crvShape.maxValue.get(), dv=param, k=1 )
            targetObj.attr( 'param' ) >> curveInfo.parameter
            
            vectorNode = pymel.core.createNode( 'vectorProduct' )
            vectorNode.op.set( 4 )
            curveInfo.position >> vectorNode.input1
            targetObj.pim >> vectorNode.matrix
            vectorNode.output >> targetObj.t
            return curveInfo
            
            
        def getLookAtAngleNode( inputLookTarget, inputRotTarget, **options ):

            def createLookAtMatrix( lookTarget, rotTarget ):
                mm = pymel.core.createNode( 'multMatrix' )
                compose = pymel.core.createNode( 'composeMatrix' )
                mm2 = pymel.core.createNode( 'multMatrix' )
                invMtx = pymel.core.createNode( 'inverseMatrix' )
                
                lookTarget.wm >> mm.i[0]
                rotTarget.t >> compose.it
                compose.outputMatrix >> mm2.i[0]
                rotTarget.pm >> mm2.i[1]
                mm2.matrixSum >> invMtx.inputMatrix
                invMtx.outputMatrix >> mm.i[1]
                return mm
            
            if options.has_key( 'direction' ) and options['direction']:
                direction = options['direction']
            else:
                direction = [1,0,0]
            
            lookTarget = pymel.core.ls( inputLookTarget )[0]
            rotTarget = pymel.core.ls( inputRotTarget )[0]
            
            dcmpLookAt = pymel.core.createNode( 'decomposeMatrix' )
            createLookAtMatrix( lookTarget, rotTarget ).matrixSum >> dcmpLookAt.imat
            
            abnodes = dcmpLookAt.listConnections( type='angleBetween' )
            if not abnodes:
                node = cmds.createNode( 'angleBetween' )
                cmds.setAttr( node + ".v1", *direction )
                cmds.connectAttr( dcmpLookAt + '.ot', node + '.v2' )
            else:
                node = abnodes[0]
            return node
        
        
        def getDirectionIndex( inputVector ):
            
            import math
            
            if type( inputVector ) in [ list, tuple ]:
                normalInput = OpenMaya.MVector(*inputVector).normal()
            else:
                normalInput = OpenMaya.MVector(inputVector).normal()
            
            xVector = OpenMaya.MVector( 1,0,0 )
            yVector = OpenMaya.MVector( 0,1,0 )
            zVector = OpenMaya.MVector( 0,0,1 )
            
            xdot = xVector * normalInput
            ydot = yVector * normalInput
            zdot = zVector * normalInput
            
            xabs = math.fabs( xdot )
            yabs = math.fabs( ydot )
            zabs = math.fabs( zdot )
            
            dotList = [xdot, ydot, zdot]
            
            dotIndex = 0
            if xabs < yabs:
                dotIndex = 1
                if yabs < zabs:
                    dotIndex = 2
            elif xabs < zabs:
                dotIndex = 2
                
            if dotList[ dotIndex ] < 0:
                dotIndex += 3
            
            return dotIndex
        
        
        def listToMatrix( mtxList ):
            if type( mtxList ) == OpenMaya.MMatrix:
                return mtxList
            matrix = OpenMaya.MMatrix()
            if type( mtxList ) == list:
                resultMtxList = mtxList
            else:
                resultMtxList = []
                for i in range( 4 ):
                    for j in range( 4 ):
                        resultMtxList.append( mtxList[i][j] )
            
            OpenMaya.MScriptUtil.createMatrixFromList( resultMtxList, matrix )
            return matrix
        
        
        def lookAtConnect( inputLookTarget, inputRotTarget, **options ):
    
            if options.has_key( 'direction' ) and options['direction']:
                direction = options['direction']
            else:
                direction = None
            
            lookTarget = pymel.core.ls( inputLookTarget )[0]
            rotTarget  = pymel.core.ls( inputRotTarget )[0]
            
            if inputRotTarget:
                wim = listToMatrix( rotTarget.wim.get() )
                pos = OpenMaya.MPoint( *pymel.core.xform( lookTarget, q=1, ws=1, t=1 ) )
                directionIndex = getDirectionIndex( pos*wim )
                direction = [[1,0,0], [0,1,0], [0,0,1],[-1,0,0], [0,-1,0], [0,0,-1]][directionIndex]
            
            node = getLookAtAngleNode( lookTarget, rotTarget, direction=direction )
            cmds.connectAttr( node + '.euler', rotTarget + '.r' )
        
        def makeLookAtChild( inputLookTarget, inputLookBase, **options ):
    
            lookTarget = pymel.core.ls( inputLookTarget )[0]
            lookBase   = pymel.core.ls( inputLookBase )[0]
            
            lookAtChild = pymel.core.createNode( 'transform' )
            lookAtChild.setParent( lookBase )
            setTransformDefault( lookAtChild )
            lookAtConnect( lookTarget, lookAtChild, **options )
            lookAtChild.t.set( 0,0,0 )
            return lookAtChild
        
        def setTransformDefault( inputTarget ):
            target = pymel.core.ls( inputTarget )[0]
            attrs = ['tx','ty','tz','rx','ry','rz','sx','sy','sz']
            values = [0,0,0,0,0,0,1,1,1]
            for i in range( len( attrs ) ):
                try:cmds.setAttr( target + '.' + attrs[i], values[i] )
                except:pass
        
        
        
        def getTangentAtParam( inputCurve, param ):
    
            curve = pymel.core.ls( inputCurve )[0]
            curveShape = curve.getShape()
            
            fnCurve = OpenMaya.MFnNurbsCurve( getDagPath( curveShape ) )
            return fnCurve.tangent( param )
        
        translatorBases = []
        currentParent = curveBase
        for ctl in ctls:
            translatorBase = pymel.core.createNode( 'transform', n='trBase_' + ctl.nodeName() )
            pymel.core.xform( translatorBase, ws=1, matrix=ctl.wm.get() )
            curveInfo = attachToCurve( translatorBase, curve )
            translatorBases.append( translatorBase )
            translatorBase.setParent( currentParent )
            currentParent = translatorBase
            vectorNode = pymel.core.createNode( 'vectorProduct' ); vectorNode.op.set( 3 )
            curveInfo.tangent >> vectorNode.input1
            translatorBase.pim >> vectorNode.matrix
            angleNode = pymel.core.createNode( 'angleBetween' )
            angleNode.vector1.set( vectorNode.output.get() )
            vectorNode.output >> angleNode.vector2
            angleNode.euler >>  translatorBase.rotate
        
        translators = []
        for i in range( len( ctls ) ):
            ctl = ctls[i]
            translatorBase = translatorBases[i]
            translator = pymel.core.createNode( 'transform', n='tr_' + ctl.nodeName() )
            translator.addAttr( BaseValues.translatorMessageName, at='message' )
            ctl.message >> translator.attr( BaseValues.translatorMessageName )
            translator.setParent( translatorBase )
            pymel.core.xform( translator, ws=1, matrix= ctl.wm.get() )
            translators.append( translator )
            translator.dh.set( 1 )
            translator.dla.set( 1 )
        return translators
    
    
    @staticmethod
    def getExpressionString( mainCtl, ctlsGroup, translatorsGroup ):
        
        expressionString = """
        string $controllers[] = { @CONTROLLERLIST@ };
        string $translators[] = { @TRANSLATORLIST@ };
        int $currentTime = `currentTime -q`;
        
        int $simulationStartTime = `getAttr @STARTTIMEATTR@`;
        
        if( $simulationStartTime <= $currentTime )
        {
            int $i=0;
            for( $i=0; $i < size($controllers); $i++ )
            {
                float $trans[] = `xform -q -ws -t $translators[$i]`;
                float $rot[] = `xform -q -ws -ro $translators[$i]`;
                move -ws $trans[0] $trans[1] $trans[2] $controllers[$i];
                rotate -ws $rot[0] $rot[1] $rot[2] $controllers[$i];
            }
        }
        """
        
        mainCtl = pymel.core.ls( mainCtl )[0]
        
        controllerListString = ''
        translatorListString = ''
        for i in range( len(ctlsGroup) ):
            ctls = ctlsGroup[i]
            translators = translatorsGroup[i]
            for j in range( len( ctls ) ):
                ctl = pymel.core.ls( ctls[j] )[0]
                translator = pymel.core.ls( translators[j] )[0]
                controllerListString += '"%s"' % ctl
                translatorListString += '"%s"' % translator
        
        controllerListString = controllerListString.replace( '""', '","' )
        translatorListString = translatorListString.replace( '""', '","' )
        
        expressionString = expressionString.replace( '@CONTROLLERLIST@', controllerListString ).replace( '@TRANSLATORLIST@', translatorListString )\
        .replace( '@STARTTIMEATTR@', mainCtl.attr( 'startFrame' ).name() )
        
        return expressionString
        

    
    @staticmethod
    def createSimulationSystemByCtlsGroup( inputMainCtl, ctlsGroup ):
        
        mainCtl = pymel.core.ls( inputMainCtl )[0]
        
        if pymel.core.objExists( BaseValues.expressionname ): pymel.core.delete( BaseValues.expressionname )
        if pymel.core.objExists( BaseValues.allgroupname ):   pymel.core.delete( BaseValues.allgroupname )
        
        newCurves  = []
        curveBases = []
        follicles  = []
        cmds.undoInfo( ock=1 )
        for ctlGroup in ctlsGroup:
            curve, curveBase = BaseCommands.createBaseCurve( ctlGroup )
            newCurve, follicle = BaseCommands.makeDynamicCurve( curve, curveBase )
            follicles.append( follicle )
            newCurves.append( newCurve )
            curveBases.append( curveBase )
        hairSystemTransform, nucleus = BaseCommands.createSymmnulationSystem( follicles )
        pymel.core.currentTime( pymel.core.playbackOptions( q=1, min=1 ) )
        pymel.core.refresh()
        translatorsGroup = []
        for i in range( len( ctlsGroup ) ):
            translators = BaseCommands.createCtlsTranslators( ctlsGroup[i], newCurves[i], curveBases[i] )
            translatorsGroup.append( translators )
        allGrp = pymel.core.group( em=1, n=BaseValues.allgroupname )
        pymel.core.parent( hairSystemTransform, nucleus, curveBases, allGrp )
        allGrp.v.set( 0 )
        
        hairSystemShape = hairSystemTransform.getShape()
        BaseCommands.addAttr( mainCtl, ln="________", at='enum', en="hairSimulationValues:", cb=1 )
        BaseCommands.addAttr( mainCtl, ln='stiffness', k=1, min=0.1, max=1, dv=0.4 )
        BaseCommands.addAttr( mainCtl, ln='stiffness_end', k=1, min=0.1, max=1, dv=0.4 )
        BaseCommands.addAttr( mainCtl, ln='damp', k=1, min=0, max=1, dv=0.15 )
        BaseCommands.addAttr( mainCtl, ln='drag', k=1, min=0, max=1, dv=0.15 )
        
        mainCtl.attr( 'stiffness' ) >> hairSystemShape.attr( 'startCurveAttract' )
        mainCtl.attr( 'stiffness_end' ) >> hairSystemShape.attr( 'stiffnessScale[0].stiffnessScale_FloatValue' )
        mainCtl.attr( 'stiffness_end' ) >> hairSystemShape.attr( 'stiffnessScale[1].stiffnessScale_FloatValue' )
        mainCtl.attr( 'drag' ) >> hairSystemShape.attr( 'drag' )
        mainCtl.attr( 'drag' ) >> hairSystemShape.attr( 'motionDrag' )
        mainCtl.attr( 'damp' ) >> hairSystemShape.attr( 'attractionDamp' )
        mainCtl.attr( 'damp' ) >> hairSystemShape.attr( 'damp' )
        
        BaseCommands.addAttr( mainCtl, ln="________", at='enum', en="hairSimulationStartFrame:", cb=1 )
        BaseCommands.addAttr( mainCtl, ln='startFrame', cb=1, at='long', dv=1 )
        mainCtl.attr( 'startFrame' ) >> nucleus.attr( 'startFrame' )
  
        hairSystemShape.attr( 'active' ).set( 1 )
        hairSystemShape.attr( 'stretchResistance' ).set( 40 )
        hairSystemShape.attr( 'compressionResistance' ).set( 40 )
        hairSystemShape.attr( 'bendResistance' ).set( 15 )
        
        mel.eval( 'autoKeyframe -e -state 0' )
        
        expressionString = BaseCommands.getExpressionString( mainCtl, ctlsGroup, translatorsGroup )
        
        pymel.core.expression( s=expressionString,  o="", n=BaseValues.expressionname, ae=1, uc=all )
        cmds.undoInfo( cck=1 )
    
    
    @staticmethod
    def deleteSimulationSystem():
        if pymel.core.objExists( BaseValues.expressionname ): pymel.core.delete( BaseValues.expressionname )
        if pymel.core.objExists( BaseValues.allgroupname ):   pymel.core.delete( BaseValues.allgroupname )
    
    
    @staticmethod
    def getTranslatorsGroup( ctlsGroup ):
        
        translatorsGroup = []
        for ctls in ctlsGroup:
            translators = []
            for ctl in ctls:
                ctl = pymel.core.ls( ctl )[0]
                cons = ctl.attr( 'message' ).listConnections( s=0, d=1, p=1 )
                targetNode = None
                for con in cons:
                    attrName = con.longName()
                    if attrName != BaseValues.translatorMessageName: continue
                    targetNode = con.node()
                    break
                translators.append( targetNode )
            translatorsGroup.append( translators )
        return translatorsGroup


    @staticmethod
    def bake( mainCtl, ctlsGroup, minFrame, maxFrame ):
        
        translatorsGroup = BaseCommands.getTranslatorsGroup( ctlsGroup )
        expressionString = BaseCommands.getExpressionString( mainCtl, ctlsGroup, translatorsGroup )
        
        keyTargets = []
        for ctls in ctlsGroup:
            keyTargets += ctls
        pymel.core.select( keyTargets )
        
        for i in range( minFrame, maxFrame + 1 ):
            pymel.core.currentTime( i )
            mel.eval( expressionString )
            pymel.core.setKeyframe( keyTargets )
        BaseCommands.deleteSimulationSystem()
        




class Widget_mainController( QWidget ):
    
    def __init__(self, *args, **kwargs ):
        
        self.uiInfoPath = Window.infoBaseDir + '/Widget_mainController.json'
        
        QWidget.__init__( self, *args, **kwargs )
        mainLayout = QHBoxLayout( self ); mainLayout.setContentsMargins(0,0,0,0)
        mainLayout.setSpacing( 5 )
        
        label = QLabel( "Main Ctl : " )
        lineEdit = QLineEdit()
        button = QPushButton( "Load" )
        
        mainLayout.addWidget( label )
        mainLayout.addWidget( lineEdit )
        mainLayout.addWidget( button )
        
        QtCore.QObject.connect( button, QtCore.SIGNAL("clicked()"), self.loadCtl )

        self.lineEdit = lineEdit
        
        data = BaseCommands.readData( self.uiInfoPath )
        if data.has_key( 'lineEdit' ):
            self.lineEdit.setText( data['lineEdit'] )


    def loadCtl(self):
        
        sels = pymel.core.ls( sl=1 )
        self.lineEdit.setText( sels[-1].name() )
        BaseCommands.writeData( {"lineEdit":self.lineEdit.text()}, self.uiInfoPath )
        
        




class Widget_ctlList( QWidget ):


    def __init__(self, *args, **kwargs ):
        
        self.index = 0
        if kwargs.has_key( 'index' ):
            self.index = kwargs.pop( 'index' )
        
        QWidget.__init__( self, *args, **kwargs )
        mainLayout = QVBoxLayout( self ); mainLayout.setContentsMargins(0,0,0,0)
        mainLayout.setSpacing(0)
        
        treeWidget = QTreeWidget()
        treeWidget.setColumnCount(1)
        headerItem = treeWidget.headerItem()
        headerItem.setText( 0, 'Controller list'.decode('utf-8') )
        button = QPushButton( 'Load Controllers'.decode('utf-8') )
        mainLayout.addWidget( treeWidget )
        mainLayout.addWidget( button )

        self.treeWidget = treeWidget
        QtCore.QObject.connect( button, QtCore.SIGNAL("clicked()"), self.loadControllers )
        
        self.uiInfoPath = Window.infoBaseDir + '/Widget_ctlList_%d.json' % self.index
        self.loadInfo()
    

    def loadControllers(self):
        
        self.treeWidget.clear()
        sels = pymel.core.ls( sl=1 )

        currentParent = self.treeWidget
        self.items = []
        
        for sel in sels:
            widgetItem = QTreeWidgetItem( currentParent )
            widgetItem.realObject = sel
            widgetItem.setText( 0, sel.name() )
            if isinstance( currentParent, QTreeWidgetItem ):
                currentParent.setExpanded( True )
            currentParent = widgetItem
            self.items.append( sel.name() )
        self.saveInfo()


    def loadInfo(self):
        
        data = BaseCommands.readData( self.uiInfoPath )
        if not data.has_key( 'controllers' ): return None
        controllerList = data[ 'controllers' ]
        
        controllers = []
        for controller in controllerList:
            if not pymel.core.ls( controller ): continue
            controllers.append( pymel.core.ls( controller )[0] )
        self.treeWidget.clear()

        currentParent = self.treeWidget
        self.items = []
        
        for sel in controllers:
            widgetItem = QTreeWidgetItem( currentParent )
            widgetItem.realObject = sel
            widgetItem.setText( 0, sel.name() )
            if isinstance( currentParent, QTreeWidgetItem ):
                currentParent.setExpanded( True )
            currentParent = widgetItem
            self.items.append( sel.name() )
        
    
    def saveInfo(self):
        
        BaseCommands.writeData( {'controllers':self.items }, self.uiInfoPath )
            
    




class Widget_ctlListGroup( QWidget ):

    def __init__(self, *args, **kwargs ):
        
        self.uiInfoPath = Window.infoBaseDir + '/Widget_ctlListGroup.json'
        
        QWidget.__init__( self, *args, **kwargs )
        mainLayout = QVBoxLayout( self )
        buttonLayout = QHBoxLayout()
        gridLayout = QGridLayout()
        mainLayout.addLayout( buttonLayout )
        mainLayout.addLayout( gridLayout )
        
        gridLayout.setSpacing(5)
        gridLayout.setVerticalSpacing(5)
        
        b_addList = QPushButton( "Add List" )
        b_removeList = QPushButton( "Remove List" )
        buttonLayout.addWidget( b_addList )
        buttonLayout.addWidget( b_removeList )
        
        w_ctlList = Widget_ctlList()
        gridLayout.addWidget( w_ctlList )
    
        self.__gridLayout = gridLayout
        
        QtCore.QObject.connect( b_addList,    QtCore.SIGNAL( "clicked()" ), self.addList )
        QtCore.QObject.connect( b_removeList, QtCore.SIGNAL( "clicked()" ), self.removeList )
        
        self.loadInfo()


    def loadInfo(self):
        data = BaseCommands.readData( self.uiInfoPath )
        if data.has_key( 'numWidget' ):
            numWidget = data[ 'numWidget' ]
            for i in range( numWidget-1 ): self.addList()
        

    def addList(self):
        widgets = []
        for row in range(self.__gridLayout.rowCount()):
            for column in range(self.__gridLayout.columnCount()):
                item = self.__gridLayout.itemAtPosition(row, column)
                if not item: continue
                widget = item.widget()
                if not isinstance(widget, Widget_ctlList): continue
                widgets.append( widget )
                widget.setParent( None )
        widgets.append( Widget_ctlList( index = len(widgets) ) )

        divValue =  (len(widgets)+1) / 2
        
        for i in range( len( widgets ) ):
            if divValue < 2:
                column, row = divmod( i, divValue )
            else:
                row, column = divmod( i, divValue )
            self.__gridLayout.addWidget( widgets[i], row, column )
        BaseCommands.writeData( {'numWidget':len( widgets )}, self.uiInfoPath )


    def removeList(self):
        widgets = []
        for row in range(self.__gridLayout.rowCount()):
            for column in range(self.__gridLayout.columnCount()):
                item = self.__gridLayout.itemAtPosition(row, column)
                if not item: continue
                widget = item.widget()
                if not isinstance(widget, Widget_ctlList): continue
                widgets.append( widget )
                widget.setParent( None )
        loopValue = len( widgets )-1
        if len( widgets ) == 1: loopValue = 1
        
        divValue =  len(widgets) / 2
        for i in range( loopValue ):
            if divValue < 2:
                column, row = divmod( i, divValue )
            else:
                row, column = divmod( i, divValue )
            self.__gridLayout.addWidget( widgets[i], row, column )
        BaseCommands.writeData( {'numWidget':loopValue}, self.uiInfoPath )
    
    
    def getChildrenWidgets(self):
        widgets = []
        for row in range(self.__gridLayout.rowCount()):
            for column in range(self.__gridLayout.columnCount()):
                item = self.__gridLayout.itemAtPosition(row, column)
                if not item: continue
                widget = item.widget()
                if not isinstance(widget, Widget_ctlList): continue
                widgets.append( widget )
        return widgets




class Widget_buttons( QWidget ):
    
    def __init__(self, *args, **kwargs ):
        
        self.mainWindow = args[0]
        
        QWidget.__init__( self, *args, **kwargs )
        mainLayout = QVBoxLayout( self )
        
        layout_expression = QHBoxLayout()
        b_create = QPushButton( "Create Expression" )
        b_delete = QPushButton( "Delete Expression" )
        layout_expression.addWidget( b_create )
        layout_expression.addWidget( b_delete )
        b_bake = QPushButton( "Bake" )
        
        mainLayout.addLayout( layout_expression )
        mainLayout.addWidget( b_bake )
        
        QtCore.QObject.connect( b_create, QtCore.SIGNAL( "clicked()" ), self.createExpression )
        QtCore.QObject.connect( b_delete, QtCore.SIGNAL( "clicked()" ), self.deleteExpression )
        QtCore.QObject.connect( b_bake,   QtCore.SIGNAL( "clicked()" ), self.bake )
    
    
    def createExpression(self):
        
        ctlsGroup = []
        for widget in self.mainWindow.w_ctlListGroup.getChildrenWidgets():
            ctls = widget.items
            allExists=True
            for ctl in ctls:
                if not pymel.core.objExists( ctl ): 
                    allExists=False
                    break
            if not allExists: continue
            ctlsGroup.append( ctls )
        
        mainCtl = self.mainWindow.w_mainCtl.lineEdit.text()
        BaseCommands.createSimulationSystemByCtlsGroup( mainCtl, ctlsGroup )
    
    
    def deleteExpression(self):
        
        BaseCommands.deleteSimulationSystem()
    
    
    def bake(self):
        
        self.bakeWidget = QDialog( self )
        
        def doCommand():
            ctlsGroup = []
            for widget in self.mainWindow.w_ctlListGroup.getChildrenWidgets():
                ctls = widget.items
                allExists=True
                for ctl in ctls:
                    if not pymel.core.objExists( ctl ): 
                        allExists=False
                        break
                if not allExists: continue
                ctlsGroup.append( ctls )
            mainCtl = self.mainWindow.w_mainCtl.lineEdit.text()
            minFrame = int( self.bakeWidget.le_minFrame.text() )
            maxFrame = int( self.bakeWidget.le_maxFrame.text() )
            BaseCommands.bake( mainCtl, ctlsGroup, minFrame, maxFrame )

        
        def closeCommand():
            self.bakeWidget.close()


        validator = QIntValidator( self )
        
        minFrame = pymel.core.playbackOptions( q=1, min=0 )
        maxFrame = pymel.core.playbackOptions( q=1, max=1 )
        
        mainLayout = QVBoxLayout( self.bakeWidget )
        
        timeRangeLayout = QHBoxLayout()
        l_minFrame = QLabel( "Min Frame : " )
        le_minFrame = QLineEdit(); le_minFrame.setValidator( validator )
        l_maxFrame = QLabel( "Max Frame : " )
        le_maxFrame = QLineEdit(); le_maxFrame.setValidator( validator )
        timeRangeLayout.addWidget( l_minFrame )
        timeRangeLayout.addWidget( le_minFrame )
        timeRangeLayout.addWidget( l_maxFrame )
        timeRangeLayout.addWidget( le_maxFrame )
        
        le_minFrame.setText( str( int(minFrame) ) )
        le_maxFrame.setText( str( int(maxFrame) ) )
        
        buttonsLayout = QHBoxLayout()
        b_bake = QPushButton( "Bake" )
        b_close = QPushButton( "Close" )
        buttonsLayout.addWidget( b_bake )
        buttonsLayout.addWidget( b_close )
        
        mainLayout.addLayout( timeRangeLayout )
        mainLayout.addLayout( buttonsLayout )
        
        QtCore.QObject.connect( b_bake,  QtCore.SIGNAL( "clicked()" ), doCommand )
        QtCore.QObject.connect( b_close, QtCore.SIGNAL( "clicked()" ), closeCommand )
        self.bakeWidget.show()

        self.bakeWidget.le_minFrame = le_minFrame
        self.bakeWidget.le_maxFrame = le_maxFrame



class Window( QDialog ):

    mayawin = shiboken.wrapInstance( long( OpenMayaUI.MQtUtil.mainWindow() ), QWidget )
    objectName = "sgWidget_hairSimulationCreator"
    title = "Hair Simulation Creator"
    defaultWidth = 400
    defaultHeight = 400
    
    infoBaseDir = cmds.about( pd=1 ) + "/sg/widget_hairSimulationCreator"
    uiInfoPath = infoBaseDir + '/uiInfo.json'


    def __init__(self, *args, **kwargs ):
        
        super( Window, self ).__init__( *args, **kwargs )
        self.installEventFilter( self )
        self.setWindowTitle( Window.title )
        
        mainLayout = QVBoxLayout( self )
        w_mainCtl = Widget_mainController()
        w_ctlListGroup = Widget_ctlListGroup()
        w_buttons = Widget_buttons( self )
        mainLayout.addWidget( w_mainCtl )
        mainLayout.addWidget( w_ctlListGroup )
        mainLayout.addWidget( w_buttons )
        self.loadUIInfo()
        
        self.w_mainCtl = w_mainCtl
        self.w_ctlListGroup = w_ctlListGroup
            
    
    
    def eventFilter(self, *args, **kwargs ):
        event = args[1]
        if event.type() in [ QtCore.QEvent.Resize, QtCore.QEvent.Move ]:
            self.saveUIInfo()



    def saveUIInfo( self ):
        
        BaseCommands.makeFile( Window.uiInfoPath )
        data = {}
        data['position'] = [ self.x(), self.y() ]
        data['size'] = [ self.width(), self.height() ]
        
        f = open( Window.uiInfoPath, 'w' )
        json.dump( data, f )
        f.close()



    def loadUIInfo( self ):
        
        try:
            BaseCommands.makeFile( Window.uiInfoPath )
            f = open( Window.uiInfoPath, 'r' )
            data = json.load( f )
            f.close()
            
            posX, posY    = data['position']
            width, height = data['size']
            
            desktop = QApplication.desktop()
            desktopWidth  = desktop.width()
            desktopHeight = desktop.height()
            
            if posX + width > desktopWidth:  posX = desktopWidth - width
            if posY + height > desktopWidth: posY = desktopHeight - height
            if posX < 0 : posX = 0
            
            self.move( posX, posY )
            self.resize( width, height )
        except:
            self.resize( self.defaultWidth, self.defaultHeight )




def show( evt=0 ):
    
    mainUI = Window.mayawin.findChild( QDialog, Window.objectName )
    if mainUI: mainUI.deleteLater()
    
    mainUI = Window(Window.mayawin)
    mainUI.setObjectName( Window.objectName )
    mainUI.show()


if __name__ == '__main__':
    show()
   
        
        
        
        
        