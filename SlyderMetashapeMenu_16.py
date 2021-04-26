#BLM NOC Tools custom menu assembled by Jake Slyder
#All scripts have been tested for compatability in version 1.6.x
#Toolbox assembled by Jake Slyder.
#Large job automation scripts written by Jake Slyder
#Script to generate a text file for updating image EXIF information written by Ernie Liu
#All other tools taken from Agisoft wiki via Tom Noble's custom menu
#Note that Chunk tiling tool came from Agisoft wiki with modifications by Jake Slyder
#To add the custom menu, use the run script dialog in Photoscan.  Alternatively, you can copy this script in the folder below to have it load on photoscan start.
#for Mac autoload place in  /Users/<user>/Library/Application Support/Agisoft/PhotoScan Pro/scripts/
#for linux /home/<user>/.local/share/data/Agisoft/PhotoScan Pro/scripts/
#for Windows C:/users/<user name>/AppData/Local/AgiSoft/PhotoScan Pro/scripts or C:/Program files/Agisoft/PhotoScan Pro/scripts
#NOTE, for windows you may need to show hidden items under the view tab in windows explorer.
import Metashape, pprint
import math, time, sys
from PySide2 import QtGui, QtCore, QtWidgets
import textwrap

def processRegularDataset():
#Goes through the regular procesing workflow, from image alignment through error reduction (on Reconstruction Uncertainty
# and projection accuracy) through to the point where you'd need to enter control.  Optionally includes the ability to
# add detect markers option.


    global doc
    proceed = Metashape.app.getBool("This tool is intended to run everything from image alignment to the point where you enter control, including reconstruction uncertanty and projection accuarcy error reduction.  It automatically starts on the active chunk and will save the open project.  \n \nContinue?")
    doc = Metashape.app.document
    chunk = doc.chunk
    if chunk.point_cloud:
        a = True
    else:
        a = False

    if proceed == True:

        app = QtWidgets.QApplication.instance()
        parent = app.activeWindow()
        dlg = StandardImgProcessDlg(parent)


#Define the UI and the process in the class below.
class StandardImgProcessDlg(QtWidgets.QDialog):

    def __init__(self, parent):
        QtWidgets.QDialog.__init__(self, parent)
        self.setWindowTitle("Align Images and Perform First Steps of Error Reduction")


        #FIRST, start with the alignment optoins.  Define first here the accuracy
        #Let's add a label first to make it easier to organize
        self.label1 = QtWidgets.QLabel()
        self.label1.setText("Choose Image Alignment Parameters")

        #Create a group to hold the radio buttons for accuracy
        #self.accButton = QtWidgets.QGroupBox('Select accuracy level for image alignment')
        self.accuracyChoice = QtWidgets.QComboBox()
        accuracyOptions = ["Highest Accuracy", "High Accuracy","Medium Accuracy", "Low Accuracy", "Lowest Accuracy"]
        for i in accuracyOptions:
            self.accuracyChoice.addItem(i)
        self.accuracyChoice.setCurrentText("High Accuracy")
        #Add buttons for additional alignment criteria
        self.chkGenPreSel = QtWidgets.QCheckBox("Use generic preselection?")
        self.chkRefPreSel = QtWidgets.QCheckBox("Use reference preselection?")
        self.chkRefPreSel.setChecked(True)
        self.chkResAlignment = QtWidgets.QCheckBox("Reset current alignment?")
        self.chkUseMask = QtWidgets.QCheckBox("Filter keypoints by image masks?")
        self.chkUseMask.setToolTip("Only check if masks applied to input images.")

        #self.accButton = QtWidgets.QGroupBox('Select accuracy level for image alignment')
        self.refChoice = QtWidgets.QComboBox()
        refOptions = ["Source", "Estimated", "Sequential"]
        for i in refOptions:
            self.refChoice.addItem(i)
        self.refChoice.setCurrentText("Source")

        #Add boxes to enter key/tie point limit
        self.spinKey = QtWidgets.QSpinBox()
        self.spinKey.setMinimum(0)
        self.spinKey.setMaximum(200000)
        self.spinKey.setValue(60000)

        self.spinKeyLab = QtWidgets.QLabel()
        self.spinKeyLab.setText("Keypoint Limit:")

        self.spinTie = QtWidgets.QSpinBox()
        self.spinTie.setMinimum(0)
        self.spinTie.setMaximum(200000)

        self.spinTieLab = QtWidgets.QLabel()
        self.spinTieLab.setText("Tiepoint Limit:")

        #Add a label in order to add some distance
        self.label2 = QtWidgets.QLabel()
        self.label2.setText("\n Choose the Model Parameters for Optimizing Cameras")

        #Add buttons for camera parameters.
        self.f = QtWidgets.QCheckBox("Fit f")
        self.f.setChecked(True)
        self.c = QtWidgets.QCheckBox("Fit cx,cy")
        self.c.setChecked(True)
        self.k1 = QtWidgets.QCheckBox("Fit k1")
        self.k1.setChecked(True)
        self.k2 = QtWidgets.QCheckBox("Fit k2")
        self.k2.setChecked(True)
        self.k3 = QtWidgets.QCheckBox("Fit k3")
        self.k3.setChecked(True)
        self.k4 = QtWidgets.QCheckBox("Fit k4")
        self.b1 = QtWidgets.QCheckBox("Fit b1")
        self.b2 = QtWidgets.QCheckBox("Fit b2")
        self.p1 = QtWidgets.QCheckBox("Fit p1")
        self.p1.setChecked(True)
        self.p2 = QtWidgets.QCheckBox("Fit p2")
        self.p2.setChecked(True)
        self.p3 = QtWidgets.QCheckBox("Fit p3")
        self.p4 = QtWidgets.QCheckBox("Fit p4")
        self.adlCor = QtWidgets.QCheckBox("Fit additional corrections")

        #Add another label to get reconstruction uncertainty.
        self.label3 = QtWidgets.QLabel()
        self.label3.setText("\n Target Error Reduction Values.")

        #Create widget for reconstruction uncertainty
        self.reconUncSpn = QtWidgets.QDoubleSpinBox()
        self.reconUncSpn.setDecimals(1)
        self.reconUncSpn.setValue(10.0)
        self.reconUncSpn.setRange(1.0,50.0)
        #Create an accompanying label
        self.spinReconLab = QtWidgets.QLabel()
        self.spinReconLab.setText("Reconstruction Uncertainty:")

        #Create one for projection accuracy
        self.projAccSpn = QtWidgets.QDoubleSpinBox()
        self.projAccSpn.setDecimals(1)
        self.projAccSpn.setValue(3.0)
        self.projAccSpn.setRange(1.0,50.0)
        self.spinProjLab = QtWidgets.QLabel()
        self.spinProjLab.setText("Projection Accuracy:")

        #Create widget for the maximum number of iterations for reconstructdion uncertainty
        self.spinMaxIter = QtWidgets.QSpinBox()
        self.spinMaxIter.setMinimum(0)
        self.spinMaxIter.setMaximum(50)
        self.spinMaxIter.setValue(10)
        self.spinMaxIter.setToolTip("This script iteratively removes points based on reconscruction uncertainty. \n Specifiy a maximum number of iterations greater than two.")
        self.spinIterLab = QtWidgets.QLabel()
        self.spinIterLab.setText("Maximum Iterations")

        #Add widget for aggressive or conservative error reduction
        self.label4 = QtWidgets.QLabel()
        self.label4.setText("\n \n \nWould you like a more aggressive error reduction for reconstruction uncertainty?  If Yes, script iteratively \n removes up to 50% of points until the target threshold or the maximum number of iterations is reached.  \n If no, the script raises the reconstruction uncertanty to a level where ~50% of the original cloud is removed.")
        self.aggYes = QtWidgets.QCheckBox("Use Aggressive Error Reduction")
        self.aggYes.setChecked(True)

        #Add optional parameter to detect markers
        self.label5 = QtWidgets.QLabel()
        self.label5.setText("\n \n")
        self.detectMarkersChk = QtWidgets.QCheckBox("Optional: Detect Markers?")
        #Add drop down to choose marker type (Circular 12,14,16,20 bit and non-coded circle/cross)
        self.detectMarkersChoice = QtWidgets.QComboBox()
        markerOptions = ["Cross non-coded", "Circular non-coded","Circular 12 bit", "Circular 14 bit", "Circular 16 bit", "Circular 20 bit" ]
        for i in markerOptions:
            self.detectMarkersChoice.addItem(i)
        #Add slider to choose tolerance between 0 and 100
        self.markerTolSpin = QtWidgets.QSpinBox()
        self.markerTolSpin.setRange(0,100)
        self.markerTolSpin.setValue(50)
        self.markerTolSpin.setToolTip("Higher values will create more false positives.  Lower values may lead to missed targets.")
        self.tolLabel = QtWidgets.QLabel()
        self.tolLabel.setText("Detection Tolerance")


        self.spinKey = QtWidgets.QSpinBox()
        self.spinKey.setMinimum(0)
        self.spinKey.setMaximum(200000)
        self.spinKey.setValue(60000)




        #Add button for inverted (white on black)
        self.markersInvertedChk = QtWidgets.QCheckBox("Inverted (white on black)")
        #Add button for Disable parity
        self.markersParityChk = QtWidgets.QCheckBox("Disable parity")



        #Create a start button to trigger functions when clicked
        self.btnStart = QtWidgets.QPushButton("Run")
        self.btnQuit= QtWidgets.QPushButton("Quit")

        #Add a double spinner for maximimum residucal (pix)
        self.maxResSpn = QtWidgets.QDoubleSpinBox()
        self.maxResSpn.setDecimals(1)
        self.maxResSpn.setValue(1.0)
        self.maxResSpn.setRange(0.0,10.0)
        self.maxResLab = QtWidgets.QLabel()
        self.maxResLab.setText("Maximum residual (pix):")


        #Create a layout and add widgets
        layout = QtWidgets.QGridLayout()
        layout.addWidget(self.label1,0,0,5)
        layout.addWidget(self.accuracyChoice,1,0)
        layout.addWidget(self.chkGenPreSel,1,1)
        layout.addWidget(self.chkRefPreSel,2,0)
        layout.addWidget(self.refChoice,2,1)
        layout.addWidget(self.chkResAlignment,3,0)
        layout.addWidget(self.chkUseMask,3,1)
        #layout.addWidget(self.chkResAlignment,3,0)
        layout.addWidget(self.spinKeyLab,4,0)
        layout.addWidget(self.spinKey,4,1)
        layout.addWidget(self.spinTieLab,5,0)
        layout.addWidget(self.spinTie,5,1)
        layout.addWidget(self.label2,6,0,2,0)
        #Add camera equation parameter selection
        layout.addWidget(self.f,8,0)
        layout.addWidget(self.b1,11,1)
        layout.addWidget(self.c,8,1)
        layout.addWidget(self.b2,12,1)
        layout.addWidget(self.k1,9,0)
        layout.addWidget(self.p1,9,1)
        layout.addWidget(self.k2,10,0)
        layout.addWidget(self.p2,10,1)
        layout.addWidget(self.k3,11,0)
        #layout.addWidget(self.p3,12,1)
        layout.addWidget(self.k4,12,0)
        #layout.addWidget(self.p4,13,1)
        layout.addWidget(self.adlCor,13,0)
        layout.addWidget(self.label3,15,0)
        layout.addWidget(self.reconUncSpn,16,1)
        layout.addWidget(self.spinReconLab,16,0)
        layout.addWidget(self.projAccSpn,17,1)
        layout.addWidget(self.spinProjLab,17,0)
        layout.addWidget(self.spinMaxIter,18,1)
        layout.addWidget(self.spinIterLab,18,0)
        layout.addWidget(self.label4,19,0,5,3)
        layout.addWidget(self.aggYes,26,0)
        #layout.addWidget(self.label5,27,0)
        layout.addWidget(self.detectMarkersChk,29,0)
        layout.addWidget(self.markersInvertedChk,29,1)
        layout.addWidget(self.markersParityChk,30,1)
        layout.addWidget(self.detectMarkersChoice,30,0)
        layout.addWidget(self.tolLabel,31,0)
        layout.addWidget(self.markerTolSpin,31,1)
        layout.addWidget(self.maxResSpn,32,1)
        layout.addWidget(self.maxResLab,32,0)

        #layout.addWidget(self.label5,30,0)
        layout.addWidget(self.btnStart,33,0)
        layout.addWidget(self.btnQuit,33,1)


        self.setLayout(layout)

        #By default, start with the detect markers optoins all being hidden
        self.markersInvertedChk.hide()
        self.markersParityChk.hide()
        self.detectMarkersChoice.hide()
        self.tolLabel.hide()
        self.markerTolSpin.hide()
        self.maxResSpn.hide()
        self.maxResLab.hide()


        proc_output = lambda : self.processImagery()
        proc_detMark = lambda : self.addDetectMarkers()
        proc_refChoice = lambda : self.toggleRef()


        self.detectMarkersChk.stateChanged.connect(proc_detMark)
        self.chkRefPreSel.stateChanged.connect(proc_refChoice)
        QtCore.QObject.connect(self.btnStart, QtCore.SIGNAL("clicked()"), self, QtCore.SLOT("accept()"))
        QtCore.QObject.connect(self.btnStart, QtCore.SIGNAL("clicked()"), proc_output)
        QtCore.QObject.connect(self.btnQuit, QtCore.SIGNAL("clicked()"), self, QtCore.SLOT("reject()"))


        self.exec()

    def toggleRef(self):
        vis = self.chkRefPreSel.checkState()
        self.refChoice.setEnabled(vis)

    def addDetectMarkers(self):
        vis = self.detectMarkersChk.checkState()
        self.markersInvertedChk.setVisible(vis)
        self.markersParityChk.setVisible(vis)
        self.detectMarkersChoice.setVisible(vis)
        self.tolLabel.setVisible(vis)
        self.markerTolSpin.setVisible(vis)
        self.maxResSpn.setVisible(vis)
        self.maxResLab.setVisible(vis)

    def processImagery(self):
        #Get start time for calculating runtime
        startTime = time.time()
        #Round up the user input into a more reasonable framework
        if self.accuracyChoice.currentText() == "Highest Accuracy":
            acc = 0
            print("Highest Accuracy")
        elif self.accuracyChoice.currentText() == "High Accuracy":
            acc = 1
            print("High Accuracy")
        elif self.accuracyChoice.currentText() == "Medium Accuracy":
            acc = 2
            print("Medium Accuracy")
        elif self.accuracyChoice.currentText() == "Low Accuracy":
            acc = 4
            print("Low Accuracy")
        else:
            acc = 8
            print("Lowest Accuracy")

        #Add code to accept reference preselection type
        #[, , "Sequential"]
        if self.refChoice.currentText() == "Source":
            refMode= Metashape.ReferencePreselectionMode.ReferencePreselectionSource
        elif self.refChoice.currentText() == "Estimated":
            refMode= Metashape.ReferencePreselectionMode.ReferencePreselectionEstimated
        else:
            refMode= Metashape.ReferencePreselectionMode.ReferencePreselectionSequential

        genPreSel = self.chkGenPreSel.isChecked()
        if genPreSel:
            print("Using Generic Preselection")
        refPreSel = self.chkRefPreSel.isChecked()
        if refPreSel:
            print("Using Reference Preselection")
        #resAlignment = self.chkResAlignment.isChecked()
        #if resAlignment:
        #    print("Resetting current alignment.")
        maskFilter = self.chkUseMask.isChecked()
        if maskFilter:
            print("Using Image Masks")

        keyLimit = int(self.spinKey.value()) #Keypoint limit
        print("Keypoint limit %s" %keyLimit)
        tieLimit = int(self.spinTie.value()) #Tiepoint limit
        print("Tiepoint limit %s" %tieLimit)

        resAlignment = self.chkResAlignment.isChecked()

        print("Solving for the following camera parameters")
        f_1=self.f.isChecked()
        if f_1 == True:
            print("f")
        cx_1=self.c.isChecked()
        cy_1=self.c.isChecked()
        if cx_1 == True and cy_1 == True:
            print("c")
        k1_1=self.k1.isChecked()
        if k1_1 == True:
            print("k1")
        k2_1=self.k2.isChecked()
        if k2_1 == True:
            print("k2")
        k3_1=self.k3.isChecked()
        if k3_1 == True:
            print("k3")
        k4_1=self.k4.isChecked()
        if k4_1 == True:
            print("k4")
        b1_1=self.b1.isChecked()
        if b1_1 == True:
            print("b1")
        b2_1=self.b2.isChecked()
        if b2_1 == True:
            print("b2")
        p1_1=self.p1.isChecked()
        if p1_1 == True:
            print("p1")
        p2_1=self.p2.isChecked()
        if p2_1 == True:
            print("p2")
        additCor=self.adlCor.isChecked()
        if additCor:
            print("Fitting additional corrections")


        reconThreshold = float(self.reconUncSpn.value())
        print("Reconstruction uncertainty %s" %reconThreshold)
        projThreshold = float(self.projAccSpn.value())
        print("Projection Accuracy %s" %projThreshold)
        maxIter = int(self.spinMaxIter.value())
        print("Maximum nubmer of iterations: %s" %maxIter)

        maxRes = float(self.maxResSpn.value())

        aggressive = self.aggYes.isChecked()
        if aggressive == True:
            print("Using aggressive error reduction")


        if self.detectMarkersChk.isChecked() == True:
            runDetectMarkers = True
        else:
            runDetectMarkers = False

        if runDetectMarkers == True:
            markersInverted = self.markersInvertedChk.isChecked()
            markersDisableParity = self.markersParityChk.isChecked()
            markersTolerance = self.markerTolSpin.value()
            if self.detectMarkersChoice.currentText() == 'Cross non-coded':
                markerType = Metashape.TargetType.CrossTarget
                print("Using Cross target")
            elif self.detectMarkersChoice.currentText() == 'Circular non-coded':
                markerType = Metashape.TargetType.CircularTarget
                print("Using Uncoded circle target")
            elif self.detectMarkersChoice.currentText() == 'Circular 12 bit':
                markerType = Metashape.TargetType.CircularTarget12bit
                print("Using 12b circ target")
            elif self.detectMarkersChoice.currentText() == 'Circular 14 bit':
                markerType = Metashape.TargetType.CircularTarget14bit
                print("Using 14b circ target")
            elif self.detectMarkersChoice.currentText() == 'Circular 16 bit':
                markerType = Metashape.TargetType.CircularTarget16bit
                print("Using 16b circ target")
            elif self.detectMarkersChoice.currentText() == 'Circular 20 bit':
                markerType = Metashape.TargetType.CircularTarget20bit
                print("Using 20b circ target")


        #Run the script

        #Define a doc item and then open a project with that item.
        #Must start with one chunk where the camera groups are set
        doc = Metashape.app.document
        chunk = doc.chunk
        if chunk.label == "Chunk 1":
            chunk.label = "Align Photos"

        #Run the match and alignment, then optimize at the end using the initial parameters
        chunk.matchPhotos(downscale = acc,generic_preselection=genPreSel,reference_preselection=refPreSel,reference_preselection_mode=refMode, filter_mask=maskFilter,keypoint_limit=keyLimit, tiepoint_limit=tieLimit, reset_matches=resAlignment)
        print("Match Photos Successful!")
        chunk.alignCameras(adaptive_fitting=False, reset_alignment = resAlignment)
        print("Align Photos Successful!")
        chunk.optimizeCameras(fit_f=f_1, fit_cx=cx_1, fit_cy=cy_1, fit_b1=b1_1, fit_b2=b2_1, fit_k1=k1_1, fit_k2=k2_1, fit_k3=k3_1, fit_k4=k4_1, fit_p1=p1_1, fit_p2=p2_1, fit_corrections=additCor, tiepoint_covariance=True)
        print("Optimize Successful!")

        #Save the progress
        doc.save()

        #Duplicate the chunk to start error reduction
        c2 = chunk.copy()
        print("Chunk duplication successful!")
        c2.label = "Error Reduction Steps 1,2" #Rename the chunk
        doc.save()

        #Before starting error reduction, get a count of how many active cmaeras are thre to begin with.
        cameraStart = 0
        for i in c2.cameras:
            try:
                if len(i.center) > 0:
                    cameraStart +=1
            except:
                pass

        #Start the error reduction process
        if aggressive == True:
            ##Start error reduction
            ##Iniitate a filter for tie point gradual selection
            f = Metashape.PointCloud.Filter()
            f.init(c2, criterion = Metashape.PointCloud.Filter.ReconstructionUncertainty)
            ##Start an iteritive loop to gradually select down from starting to minimuum value
            count = 1
            curVal = reconThreshold + 5
            minVal = reconThreshold
            while curVal > minVal and count < maxIter:
                pntCnt = len(c2.point_cloud.points)
                maxPnts = int(pntCnt * 0.49)
                minPnts = int(pntCnt * 0.45)
                f.selectPoints(curVal)
                nselected = len([p for p in c2.point_cloud.points if p.selected])
                if nselected > maxPnts:
                    ##If the selection value is so low that too many points are selected, increase the selection value
                    print("Too many points selected at level %s, increasing value and selecting again" %curVal)
                    curVal += 0.01
                elif nselected < maxPnts and nselected > minPnts:
                    # If 45-49% of points are selected, remove those points, optimize cameras, reset the filter and decrease the selection criteria
                    c2.point_cloud.removeSelectedPoints()
                    print("Removed %s points at a level of %s, optimizing cameras and decreasing value for next round"%(nselected,curVal))
                    c2.optimizeCameras(fit_f=f_1, fit_cx=cx_1, fit_cy=cy_1, fit_b1=b1_1, fit_b2=b2_1, fit_k1=k1_1, fit_k2=k2_1, fit_k3=k3_1, fit_k4=k4_1, fit_p1=p1_1, fit_p2=p2_1, fit_corrections=additCor, tiepoint_covariance=True)
                    f = Metashape.PointCloud.Filter()
                    #For some reason, the program freeezes at the line below at certain values
                    f.init(c2, criterion = Metashape.PointCloud.Filter.ReconstructionUncertainty)
                    curVal -= 0.05
                    count += 1
                    #Check to see if this decrement set the value below your target.
                    # If so, set current value to the target value
                    if curVal < minVal:
                        curVal = minVal
                        ## Make sure that the .05 decrement dosn't lead to more than 10% of points being selected
                        pntCnt = len(c2.point_cloud.points)
                        maxPnts = int(pntCnt * 0.49)
                        f.selectPoints(curVal)
                        nselected = len([p for p in c2.point_cloud.points if p.selected])
                        #If more than 10% selected, bump the value back up to maintain the while loop.
                        ##Otherwise let the current value equal the target value so that the decrementing loop ends.
                        if nselected > maxPnts:
                            curVal += 0.01
                elif nselected < minPnts:
                    ##Speed up getting to the mininum value by making sure at least 8% of points are selected
                    print("Too few points selected at level %s, decreasing value for quicker processing" %curVal)
                    curVal -= 0.01
                    ##Make sure that value for next step never goes below minimum value
                    if curVal < minVal:
                        curVal = minVal
                else:
                    print("This case should never happen.  If it does, check the code!")


            print("Target value achieved, iteratively selecting and removing at this level!")


            ## double check that the current value is at the min Value and that the filter is reset.
            curVal = reconThreshold
            f = Metashape.PointCloud.Filter()
            f.init(c2, criterion = Metashape.PointCloud.Filter.ReconstructionUncertainty)


            ## Set up a solved value for while loop to iteratively remove all points at target level
            solved = 0
            while solved == 0 and count < maxIter:
                pntCnt = len(c2.point_cloud.points)
                maxPnts = int(pntCnt * 0.49)
                f.selectPoints(curVal)
                nselected = len([p for p in c2.point_cloud.points if p.selected])
                if nselected == 0:
                    print("No more points selected at this level, error reduction complete to a level of %s" %curVal)
                    solved = 1
                elif nselected > maxPnts:
                    print("Too many points selected, This shouldn't happen!")
                    break
                else:
                    c2.point_cloud.removeSelectedPoints()
                    print("Removed %s points on iteration number %s" %(nselected,count))
                    c2.optimizeCameras(fit_f=f_1, fit_cx=cx_1, fit_cy=cy_1, fit_b1=b1_1, fit_b2=b2_1, fit_k1=k1_1, fit_k2=k2_1, fit_k3=k3_1, fit_k4=k4_1, fit_p1=p1_1, fit_p2=p2_1, fit_corrections=additCor, tiepoint_covariance=True)
                    f = Metashape.PointCloud.Filter()
                    f.init(c2, criterion = Metashape.PointCloud.Filter.ReconstructionUncertainty)
                    count += 1

        elif aggressive == False:
            ## First address reconstruction uncertainty, aim to get a level of 10.
            ##First determine the starting level.  Start at 10 and increment up if necessary
            PntCnt = len(c2.point_cloud.points)
            print("Sparse cloud point count after first step: %s" %PntCnt)
            targetPntCnt = int(PntCnt/2)
            print("New Target Point Count: %s" %targetPntCnt)



            ## Initiate a filter, first for recon uncert at default level
            f = Metashape.PointCloud.Filter()
            f.init(c2, criterion = Metashape.PointCloud.Filter.ReconstructionUncertainty)
            f.selectPoints(reconThreshold)
            nselected = len([p for p in c2.point_cloud.points if p.selected])
            ##Set up variable for while loop if raising threshold is necessary
            solved = 0
            #Start an if else while loop to check on starting parameter
            if nselected <= targetPntCnt:
                print("Reconstruction Uncertatiny Value will be %s" %reconThreshold)
            else:
                while solved == 0:
                    reconThreshold += 0.5
                    f.selectPoints(reconThreshold)
                    nselected = len([p for p in c2.point_cloud.points if p.selected])
                    if nselected <= targetPntCnt:
                        print("Reconstruction Uncertainty Value will be: %s" %reconThreshold)
                        solved = 1


            ## Now that the threshold is determined, start the removal process
            ## Reset solved variable to 0
            solved = 0
            count = 1
            print("Starting conservative point removal process for reconstruction uncertainty")
            ##print("just checking that recon uncertain still set at twelve: %s" %reconThreshold)
            while solved == 0 and count < maxIter:
                f.selectPoints(reconThreshold)
                nselected = len([p for p in c2.point_cloud.points if p.selected])
                print("Removing %s points on iteration number %s" %(nselected,count))
                c2.point_cloud.removeSelectedPoints()
                c2.optimizeCameras(fit_f=f_1, fit_cx=cx_1, fit_cy=cy_1, fit_b1=b1_1, fit_b2=b2_1, fit_k1=k1_1, fit_k2=k2_1, fit_k3=k3_1, fit_k4=k4_1, fit_p1=p1_1, fit_p2=p2_1, fit_corrections=additCor, tiepoint_covariance=True)
                ## This distn't help like I thoguht it might## f.resetSelection()
                f = Metashape.PointCloud.Filter()
                f.init(c2, criterion = Metashape.PointCloud.Filter.ReconstructionUncertainty)
                f.selectPoints(reconThreshold)
                nselected = len([p for p in c2.point_cloud.points if p.selected])
                if nselected == 0:
                    solved = 1
                    print("Reconstruction Uncertainty Error reduction complete")
                else:
                    solved = 0
                    count += 1
        else:
            print("Must choose whether you want an aggressive or conservative error reduction process.  Script ending!")
            raise ValueError()


        ## After Reconstruction uncertainty, do projection accuracy
        ## First resent the point count and target point count to the new level after the first step

        PntCnt = len(c2.point_cloud.points)
        print("Sparse cloud point count after first step: %s" %PntCnt)
        targetPntCnt = int(PntCnt/2)
        print("New Target Point Count: %s" %targetPntCnt)

        ## Initiate a filter, first for recon uncert at default level
        f.init(c2, criterion = Metashape.PointCloud.Filter.ProjectionAccuracy)
        f.selectPoints(projThreshold)
        nselected = len([p for p in c2.point_cloud.points if p.selected])
        ##Set up variable for while loop if raising threshold is necessary.  Can remove the points here sine this is Proj Acc is not an interative process
        solved = 0
        #Start an if else while loop to check on starting parameter
        if nselected <= targetPntCnt:
            c2.point_cloud.removeSelectedPoints()
            print("Projecion Accuracy Attained: %s" %projThreshold)
            c2.optimizeCameras(fit_f=f_1, fit_cx=cx_1, fit_cy=cy_1, fit_b1=b1_1, fit_b2=b2_1, fit_k1=k1_1, fit_k2=k2_1, fit_k3=k3_1, fit_k4=k4_1, fit_p1=p1_1, fit_p2=p2_1, fit_corrections=additCor, tiepoint_covariance=True)
        else:
            while solved == 0:
                projThreshold += 0.5
                f.selectPoints(projThreshold)
                nselected = len([p for p in c2.point_cloud.points if p.selected])
                if nselected <= targetPntCnt:
                    c2.point_cloud.removeSelectedPoints()
                    print("Projecion Accuracy Attained:")
                    c2.optimizeCameras(fit_f=f_1, fit_cx=cx_1, fit_cy=cy_1, fit_b1=b1_1, fit_b2=b2_1, fit_k1=k1_1, fit_k2=k2_1, fit_k3=k3_1, fit_k4=k4_1, fit_p1=p1_1, fit_p2=p2_1, fit_corrections=additCor, tiepoint_covariance=True)
                    print(projThreshold)
                    solved = 1

        if aggressive == True:
            c2.label = "ER Recon Unc-%s,Proj Acc-%s"%(curVal,projThreshold)
            doc.save()
            print("Error reduction steps one and two complete with the following values: \n Reconstruction uncertainty: %s \n and Projection accuracy:%s.  \n Be sure to check that all cameras still have at least 100 projections.  " %(curVal,projThreshold))
        else:
            c2.label = "ER Recon Unc-%s,Proj Acc-%s"%(reconThreshold,projThreshold)
            doc.save()
            print("Error reduction steps one and two complete with the following values: \n Reconstruction uncertainty: %s \n and Projection accuracy:%s.  \n Be sure to check that all cameras still have at least 100 projections.  " %(reconThreshold,projThreshold))

        #Run marker detection
        if runDetectMarkers == True:
            c2.detectMarkers(target_type = markerType,tolerance = markersTolerance,inverted = markersInverted,noparity = markersDisableParity, maximum_residual = maxRes)
            doc.save()


        ##Look for wehether to print a warning about cameras being removed due to too few projections
        cameraEnd = 0
        for i in c2.cameras:
            try:
                if len(i.center) > 0:
                    cameraEnd +=1
            except:
                pass

        if cameraStart > cameraEnd:
            camDiff = cameraStart - cameraEnd
            message = "WARNING! Error reduction process removed %s cameras!  Consider repeating the process with higher selection criteria"%camDiff
            Metashape.app.messageBox(textwrap.fill(message,65))

        endTime = time.time()
        processTime = str((endTime-startTime)/60)
        print("Script took %s minutes to run!" %processTime)
        print("Script complete!")



#Modified the regular processing workflow above with a few changes for historic imagery...
def processHistoricDataset():

    global doc
    doc = Metashape.app.document
    proceed = Metashape.app.getBool("This tool is intended to run everything from image alignment to the point where you enter control, including reconstruction uncertanty and projection accuarcy error reduction.  It automatically starts on the active chunk and will save the open project.  \n \nContinue?")
    if proceed == True:
        app = QtWidgets.QApplication.instance()
        parent = app.activeWindow()
        dlg = HistoricImgProcessDlg(parent)



#Below adjust the regular processing interface for historic imagery project
class HistoricImgProcessDlg(QtWidgets.QDialog):

    def __init__(self, parent):
        QtWidgets.QDialog.__init__(self, parent)
        self.setWindowTitle("Historic Imagery-Align and Perform Initial Error Reduction")


        #FIRST, start with the alignment optoins.  Define first here the accuracy
        #Let's add a label first to make it easier to organize
        self.label1 = QtWidgets.QLabel()
        self.label1.setText("Choose Image Alignment Parameters")

        #Create a group to hold the radio buttons for accuracy
        #self.accButton = QtWidgets.QGroupBox('Select accuracy level for image alignment')
        self.accuracyChoice = QtWidgets.QComboBox()
        accuracyOptions = ["Highest Accuracy", "High Accuracy","Medium Accuracy", "Low Accuracy", "Lowest Accuracy"]
        for i in accuracyOptions:
            self.accuracyChoice.addItem(i)
        self.accuracyChoice.setCurrentText("High Accuracy")
        #Add buttons for additional alignment criteria
        self.chkGenPreSel = QtWidgets.QCheckBox("Use generic preselection?")
        self.chkRefPreSel = QtWidgets.QCheckBox("Use reference preselection?")
        self.chkRefPreSel.setChecked(True)
        self.chkUseMask = QtWidgets.QCheckBox("Filter points by image masks?")
        self.chkUseMask.setToolTip("Only check if masks applied to input images.")
        self.chkResAlignment = QtWidgets.QCheckBox("Reset current alignment?")


        #self.accButton = QtWidgets.QGroupBox('Select accuracy level for image alignment')
        self.refChoice = QtWidgets.QComboBox()
        refOptions = ["Source", "Estimated", "Sequential"]
        for i in refOptions:
            self.refChoice.addItem(i)
        self.refChoice.setCurrentText("Source")

        #Add boxes to enter key/tie point limit
        self.spinKey = QtWidgets.QSpinBox()
        self.spinKey.setMinimum(0)
        self.spinKey.setMaximum(200000)
        self.spinKey.setValue(60000)

        self.spinKeyLab = QtWidgets.QLabel()
        self.spinKeyLab.setText("Keypoint Limit:")

        self.spinTie = QtWidgets.QSpinBox()
        self.spinTie.setMinimum(0)
        self.spinTie.setMaximum(200000)

        self.spinTieLab = QtWidgets.QLabel()
        self.spinTieLab.setText("Tiepoint Limit:")

        #Add a label in order to add some distance
        self.label2 = QtWidgets.QLabel()
        self.label2.setText("\n Choose the Model Parameters for Optimizing Cameras. NOTE: To process \n using only values from calibration report, uncheck all boxes below.")

        #Add button to Fix calibraiton for initial alignment
        self.fixCalibChk = QtWidgets.QCheckBox("\nFix Calibration (except f,c) for\n Initial Alignment? (Recommended)")
        self.fixCalibChk.setChecked(True)

        #Add buttons for camera parameters.
        self.f = QtWidgets.QCheckBox("Fit f")
        self.f.setChecked(True)
        self.c = QtWidgets.QCheckBox("Fit cx,cy")
        self.c.setChecked(True)
        self.k1 = QtWidgets.QCheckBox("Fit k1")
        self.k1.setChecked(True)
        self.k2 = QtWidgets.QCheckBox("Fit k2")
        self.k2.setChecked(True)
        self.k3 = QtWidgets.QCheckBox("Fit k3")
        self.k3.setChecked(True)
        self.k4 = QtWidgets.QCheckBox("Fit k4")
        self.b1 = QtWidgets.QCheckBox("Fit b1")
        self.b2 = QtWidgets.QCheckBox("Fit b2")
        self.p1 = QtWidgets.QCheckBox("Fit p1")
        self.p2 = QtWidgets.QCheckBox("Fit p2")
        self.adlCor = QtWidgets.QCheckBox("Fit additional corrections")

        #Add another label to get reconstruction uncertainty.
        self.label3 = QtWidgets.QLabel()
        self.label3.setText("\n Target Error Reduction Values.")

        #Create widget for reconstruction uncertainty
        self.reconUncSpn = QtWidgets.QDoubleSpinBox()
        self.reconUncSpn.setDecimals(1)
        self.reconUncSpn.setValue(10.0)
        self.reconUncSpn.setRange(1.0,50.0)
        #Create an accompanying label
        self.spinReconLab = QtWidgets.QLabel()
        self.spinReconLab.setText("Reconstruction Uncertainty:")

        #Create one for projection accuracy
        self.projAccSpn = QtWidgets.QDoubleSpinBox()
        self.projAccSpn.setDecimals(1)
        self.projAccSpn.setValue(3.0)
        self.projAccSpn.setRange(1.0,50.0)
        self.spinProjLab = QtWidgets.QLabel()
        self.spinProjLab.setText("Projection Accuracy:")

        #Create widget for the maximum number of iterations for reconstructdion uncertainty
        self.spinMaxIter = QtWidgets.QSpinBox()
        self.spinMaxIter.setMinimum(0)
        self.spinMaxIter.setMaximum(50)
        self.spinMaxIter.setValue(10)
        self.spinMaxIter.setToolTip("This script iteratively removes points based on reconscruction uncertainty. \n Specifiy a maximum number of iterations greater than two.")
        self.spinIterLab = QtWidgets.QLabel()
        self.spinIterLab.setText("Maximum Iterations")

        #Add widget for aggressive or conservative error reduction
        self.label4 = QtWidgets.QLabel()
        self.label4.setText("\n \nWould you like a more aggressive error reduction for reconstruction uncertainty?  If Yes, script iteratively \n removes up to 50% of points until the target threshold or the maximum number of iterations is reached.  \n If no, the script raises the reconstruction uncertanty to a level where ~50% of the original cloud is removed.")
        self.aggYes = QtWidgets.QCheckBox("Use Aggressive Error Reduction")
        self.aggYes.setChecked(True)



        #Create a start button to trigger functions when clicked
        self.btnStart = QtWidgets.QPushButton("Run")
        self.btnQuit= QtWidgets.QPushButton("Quit")



        layout = QtWidgets.QGridLayout()
        layout.addWidget(self.label1,0,0,5)
        layout.addWidget(self.accuracyChoice,1,0)
        layout.addWidget(self.chkGenPreSel,1,1)
        layout.addWidget(self.chkRefPreSel,2,0)
        layout.addWidget(self.refChoice,2,1)
        layout.addWidget(self.chkResAlignment,3,0)
        layout.addWidget(self.chkUseMask,3,1)

        layout.addWidget(self.spinKeyLab,4,0)
        layout.addWidget(self.spinKey,4,1)
        layout.addWidget(self.spinTieLab,5,0)
        layout.addWidget(self.spinTie,5,1)
        layout.addWidget(self.label2,6,0,2,0)
        #Add camera equation parameter selection
        layout.addWidget(self.f,8,0)
        layout.addWidget(self.b1,11,1)
        layout.addWidget(self.c,8,1)
        layout.addWidget(self.b2,12,1)
        layout.addWidget(self.k1,9,0)
        layout.addWidget(self.p1,9,1)
        layout.addWidget(self.k2,10,0)
        layout.addWidget(self.p2,10,1)
        layout.addWidget(self.k3,11,0)
        layout.addWidget(self.k4,12,0)
        layout.addWidget(self.adlCor,13,0)
        #Add fix calibration on one line right here
        layout.addWidget(self.fixCalibChk,14,0)
        layout.addWidget(self.label3,15,0)
        layout.addWidget(self.reconUncSpn,16,1)
        layout.addWidget(self.spinReconLab,16,0)
        layout.addWidget(self.projAccSpn,17,1)
        layout.addWidget(self.spinProjLab,17,0)
        layout.addWidget(self.spinMaxIter,18,1)
        layout.addWidget(self.spinIterLab,18,0)
        layout.addWidget(self.label4,19,0,7,2)
        layout.addWidget(self.aggYes,27,0)
        layout.addWidget(self.btnStart,30,0)
        layout.addWidget(self.btnQuit,30,1)


        self.setLayout(layout)

        proc_hist = lambda : self.processHistImagery()
        proc_refChoice = lambda : self.toggleRef()


        self.chkRefPreSel.stateChanged.connect(proc_refChoice)
        QtCore.QObject.connect(self.btnStart, QtCore.SIGNAL("clicked()"), self, QtCore.SLOT("accept()"))
        QtCore.QObject.connect(self.btnStart, QtCore.SIGNAL("clicked()"), proc_hist)
        QtCore.QObject.connect(self.btnQuit, QtCore.SIGNAL("clicked()"), self, QtCore.SLOT("reject()"))


        self.exec()

    def toggleRef(self):
        vis = self.chkRefPreSel.checkState()
        self.refChoice.setEnabled(vis)

    def processHistImagery(self):
        #Record start time to calculate process run time
        startTime = time.time()
        #Round up the user input into a more reasonable framework
        if self.accuracyChoice.currentText() == "Highest Accuracy":
            acc = 0
            print("Highest Accuracy")
        elif self.accuracyChoice.currentText() == "High Accuracy":
            acc = 1
            print("High Accuracy")
        elif self.accuracyChoice.currentText() == "Medium Accuracy":
            acc = 2
            print("Medium Accuracy")
        elif self.accuracyChoice.currentText() == "Low Accuracy":
            acc = 4
            print("Low Accuracy")
        else:
            acc = 8
            print("Lowest Accuracy")


        genPreSel = self.chkGenPreSel.isChecked()
        if genPreSel == True:
            print("Using Generic Preselection")
        refPreSel = self.chkRefPreSel.isChecked()
        if refPreSel == True:
            print("Using Reference Preselection")
        maskFilter = self.chkUseMask.isChecked()
        if maskFilter == True:
            print("Using Image Masks")

        if self.refChoice.currentText() == "Source":
            refMode= Metashape.ReferencePreselectionMode.ReferencePreselectionSource
        elif self.refChoice.currentText() == "Estimated":
            refMode= Metashape.ReferencePreselectionMode.ReferencePreselectionEstimated
        else:
            refMode= Metashape.ReferencePreselectionMode.ReferencePreselectionSequential

        fixCal = self.fixCalibChk.isChecked()


        keyLimit = int(self.spinKey.value()) #Keypoint limit
        print("Keypoint limit %s" %keyLimit)
        tieLimit = int(self.spinTie.value()) #Tiepoint limit
        print("Tiepoint limit %s" %tieLimit)

        resAlignment = self.chkResAlignment.isChecked()

        print("Solving for the following camera parameters")
        f_1=self.f.isChecked()
        if f_1 == True:
            print("f")
        cx_1=self.c.isChecked()
        cy_1=self.c.isChecked()
        if cx_1 == True and cy_1 == True:
            print("c")
        k1_1=self.k1.isChecked()
        if k1_1 == True:
            print("k1")
        k2_1=self.k2.isChecked()
        if k2_1 == True:
            print("k2")
        k3_1=self.k3.isChecked()
        if k3_1 == True:
            print("k3")
        k4_1=self.k4.isChecked()
        if k4_1 == True:
            print("k4")
        b1_1=self.b1.isChecked()
        if b1_1 == True:
            print("b1")
        b2_1=self.b2.isChecked()
        if b2_1 == True:
            print("b2")
        p1_1=self.p1.isChecked()
        if p1_1 == True:
            print("p1")
        p2_1=self.p2.isChecked()
        if p2_1 == True:
            print("p2")
        additCor=self.adlCor.isChecked()
        if additCor:
            print("Fitting additional corrections")

        reconThreshold = float(self.reconUncSpn.value())
        print("Reconstruction uncertainty %s" %reconThreshold)
        projThreshold = float(self.projAccSpn.value())
        print("Projection Accuracy %s" %projThreshold)
        maxIter = int(self.spinMaxIter.value())
        print("Maximum nubmer of iterations: %s" %maxIter)

        aggressive = self.aggYes.isChecked()
        if aggressive:
            print("Using aggressive error reduction")


        #Start running the actual process
        #Define a doc item and then open a project with that item.
        #Must start with one chunk where the camera groups are set
        doc = Metashape.app.document
        chunk = doc.chunk
        if chunk.label == "Chunk 1":
            chunk.label = "Align Photos"

        #Create a sensor variable to access sensor properties
        s = chunk.sensors
        #By default, make all calibrations fixed for initial alignment unless otherwise specified by user
        if fixCal == True:
            for i in s:
                i.fixed_params=["K1","K2","K3","K4","P1","P2", "B1","B2"]
            print("Set camera calibraitons to fixed for initial alginment!")


        #Run the match and alignment, then optimize at the end using the initial parameters
        chunk.matchPhotos(downscale = acc,generic_preselection=genPreSel,reference_preselection=refPreSel,reference_preselection_mode=refMode, filter_mask=maskFilter,keypoint_limit=keyLimit, tiepoint_limit=tieLimit, reset_matches=resAlignment,keep_keypoints=True)
        print("Match Photos Successful!")
        chunk.alignCameras(adaptive_fitting=False, reset_alignment = resAlignment)
        print("Align Photos Successful!")

        doc.save()
        
        #The next section is intended to deal with often weird results with 
        #poorer quality historic imagery.  It first resets the alingment of images
        #where the pitch of the photo is signficant, then loops through and sees 
        #if there are images that are not aligned.  Loops through this process 
        #up to five times.  

        for c in chunk.cameras:
            if c.transform:
                T = chunk.transform.matrix
                m = chunk.crs.localframe(T.mulp(c.center)) #transformation matrix to the LSE coordinates in the given point
                R = m * T * c.transform * Metashape.Matrix().Diag([1, -1, -1, 1])
        
                row = []
                for j in range (0, 3): #creating normalized rotation matrix 3x3
                    row.append(R.row(j))
                    row[j].size = 3
                    row[j].normalize()
                R = Metashape.Matrix([row[0], row[1], row[2]])
        
                yaw, pitch, roll = Metashape.utils.mat2ypr(R) #estimated orientation angles
                if roll < -5.0 or roll > 5.0 or pitch < -10.0 or pitch > 10.0:
                    c.transform = None

        #Create variables for while loop.  Starts as false but is true if all the images already aligned
        counter = 0
        solved = False
        
        NACount = 0
        for c in chunk.cameras:
            if c.transform == False or c.transform == None:
                NACount += 1
        if NACount == 0:
            solved = True
            print("Skipping while loop because all photos aligned")
        
        
        
        while counter < 5 and solved == False:
            #First check for wonky photos where the Roll is well beyond what should be the case, within 5degrees of zero
            for c in chunk.cameras:
                if c.transform:
                    T = chunk.transform.matrix
                    m = chunk.crs.localframe(T.mulp(c.center)) #transformation matrix to the LSE coordinates in the given point
                    R = m * T * c.transform * Metashape.Matrix().Diag([1, -1, -1, 1])
        
                    row = []
                    for j in range (0, 3): #creating normalized rotation matrix 3x3
                        row.append(R.row(j))
                        row[j].size = 3
                        row[j].normalize()
                    R = Metashape.Matrix([row[0], row[1], row[2]])
        
                    yaw, pitch, roll = Metashape.utils.mat2ypr(R) #estimated orientation angles
                    if roll < -5.0 or roll > 5.0 or pitch < -10.0 or pitch > 10.0:
                        c.transform = None
        
        
            print("Starting iteration %s" %counter)
            chunk.matchPhotos(generic_preselection=False, keypoint_limit = keyLimit, tiepoint_limit = tieLimit, reset_matches=False,keep_keypoints=True)
            print("Assembling list of photos with no projections")
            lst =[]
            for c in chunk.cameras:
                if c.transform == False:
                    lst.append(c)
            print("Starting alignment")
            chunk.alignCameras(lst, reset_alignment=False)
            print("Alignment complete")
        
            #Repeat process to reset photos with whyacky roll
            for c in chunk.cameras:
                if c.transform:
                    T = chunk.transform.matrix
                    m = chunk.crs.localframe(T.mulp(c.center))
                    R = m * T * c.transform * Metashape.Matrix().Diag([1, -1, -1, 1])
        
                    row = []
                    for j in range (0, 3): #creating normalized rotation matrix 3x3
                        row.append(R.row(j))
                        row[j].size = 3
                        row[j].normalize()
                    R = Metashape.Matrix([row[0], row[1], row[2]])
        
                    yaw, pitch, roll = Metashape.utils.mat2ypr(R) #estimated orientation angles
                    if roll < -5.0 or roll > 5.0 or pitch < -10.0 or pitch > 10.0:
                        c.transform = None
        
            NACount = 0
            for c in chunk.cameras:
                if c.transform == False or c.transform == None:
                    NACount += 1
            if NACount == 0:
                solved = True
                print("Ending loop because all photos aligned")
            counter += 1


        doc.save()

        #Dublicate the chunk, unfix the calibration, and optimzie with the given parameters
        c2 = chunk.copy()
        c2.label = "Unfix Calibration and Optimize Cameras"
        #update the sensor varaible to reflect this copied chunk
        s2 = c2.sensors
        for i in s2:
            i.fixed_params = []
        c2.optimizeCameras(fit_f=f_1, fit_cx=cx_1, fit_cy=cy_1, fit_b1=b1_1, fit_b2=b2_1, fit_k1=k1_1, fit_k2=k2_1, fit_k3=k3_1, fit_k4=k4_1, fit_p1=p1_1, fit_p2=p2_1, fit_corrections=additCor, tiepoint_covariance=True)
        print("Optimize Successful!")
        doc.save()

        #Duplicate the chunk yet again and start the error reduction
        c3 = c2.copy()
        c3.label = "ER Recon Unc"


        #Before starting error reduction, get a count of how many active cmaeras are thre to begin with.
        cameraStart = 0
        for i in c3.cameras:
            try:
                if len(i.center) > 0:
                    cameraStart +=1
            except:
                pass

        #Start the error reduction process
        if aggressive == True:
            #Start error reduction
            #Iniitate a filter for tie point gradual selection
            f = Metashape.PointCloud.Filter()
            f.init(c3, criterion = Metashape.PointCloud.Filter.ReconstructionUncertainty)
            #Start an iteritive loop to gradually select down from starting to minimuum value
            count = 1
            curVal = reconThreshold + 5
            minVal = reconThreshold
            while curVal > minVal and count < maxIter:
                pntCnt = len(c3.point_cloud.points)
                maxPnts = int(pntCnt * 0.49)
                minPnts = int(pntCnt * 0.45)
                f.selectPoints(curVal)
                nselected = len([p for p in c3.point_cloud.points if p.selected])
                if nselected > maxPnts:
                    #If the selection value is so low that too many points are selected, increase the selection value
                    print("Too many points selected at level %s, increasing value and selecting again" %curVal)
                    curVal += 0.01
                elif nselected < maxPnts and nselected > minPnts:
                    # If 45-49% of points are selected, remove those points, optimize cameras, reset the filter and decrease the selection criteria
                    c3.point_cloud.removeSelectedPoints()
                    print("Removed %s points at a level of %s, optimizing cameras and decreasing value for next round"%(nselected,curVal))
                    c3.optimizeCameras(fit_f=f_1, fit_cx=cx_1, fit_cy=cy_1, fit_b1=b1_1, fit_b2=b2_1, fit_k1=k1_1, fit_k2=k2_1, fit_k3=k3_1, fit_k4=k4_1, fit_p1=p1_1, fit_p2=p2_1, fit_corrections=additCor, tiepoint_covariance=True)
                    f = Metashape.PointCloud.Filter()
                    #For some reason, the program freeezes at the line below at certain values
                    f.init(c3, criterion = Metashape.PointCloud.Filter.ReconstructionUncertainty)
                    curVal -= 0.05
                    count += 1
                    #Check to see if this decrement set the value below your target.
                    # If so, set current value to the target value
                    if curVal < minVal:
                        curVal = minVal
                    # Make sure that the .05 decrement dosn't lead to more than 10% of points being selected
                        pntCnt = len(c3.point_cloud.points)
                        maxPnts = int(pntCnt * 0.49)
                        f.selectPoints(curVal)
                        nselected = len([p for p in c3.point_cloud.points if p.selected])
                        #If more than 10% selected, bump the value back up to maintain the while loop.
                        ##Otherwise let the current value equal the target value so that the decrementing loop ends.
                        if nselected > maxPnts:
                            curVal += 0.01
                elif nselected < minPnts:
                    #Speed up getting to the mininum value by making sure at least 8% of points are selected
                    print("Too few points selected at level %s, decreasing value for quicker processing" %curVal)
                    curVal -= 0.01
                    #Make sure that value for next step never goes below minimum value
                    if curVal < minVal:
                        curVal = minVal
                else:
                    print("This case should never happen.  If it does, check the code!")


            print("Target value achieved, iteratively selecting and removing at this level!")


            # double check that the current value is at the min Value and that the filter is reset.
            curVal = reconThreshold
            f = Metashape.PointCloud.Filter()
            f.init(c3, criterion = Metashape.PointCloud.Filter.ReconstructionUncertainty)


            # Set up a solved value for while loop to iteratively remove all points at target level
            solved = 0
            while solved == 0 and count < maxIter:
                pntCnt = len(c3.point_cloud.points)
                maxPnts = int(pntCnt * 0.49)
                f.selectPoints(curVal)
                nselected = len([p for p in c3.point_cloud.points if p.selected])
                if nselected == 0:
                    print("No more points selected at this level, error reduction complete to a level of %s" %curVal)
                    solved = 1
                elif nselected > maxPnts:
                    print("Too many points selected, This shouldn't happen!")
                    break
                else:
                    c3.point_cloud.removeSelectedPoints()
                    print("Removed %s points on iteration number %s" %(nselected,count))
                    c3.optimizeCameras(fit_f=f_1, fit_cx=cx_1, fit_cy=cy_1, fit_b1=b1_1, fit_b2=b2_1, fit_k1=k1_1, fit_k2=k2_1, fit_k3=k3_1, fit_k4=k4_1, fit_p1=p1_1, fit_p2=p2_1, fit_corrections=additCor, tiepoint_covariance=True)
                    f = Metashape.PointCloud.Filter()
                    f.init(c3, criterion = Metashape.PointCloud.Filter.ReconstructionUncertainty)
                    count += 1

        elif aggressive == False:
            # First address reconstruction uncertainty, aim to get a level of 10.
            #First determine the starting level.  Start at 10 and increment up if necessary
            PntCnt = len(c3.point_cloud.points)
            print("Sparse cloud point count after first step: %s" %PntCnt)
            targetPntCnt = int(PntCnt/2)
            print("New Target Point Count: %s" %targetPntCnt)



            # Initiate a filter, first for recon uncert at default level
            f = Metashape.PointCloud.Filter()
            f.init(c3, criterion = Metashape.PointCloud.Filter.ReconstructionUncertainty)
            f.selectPoints(reconThreshold)
            nselected = len([p for p in c3.point_cloud.points if p.selected])
            #Set up variable for while loop if raising threshold is necessary
            solved = 0
            #Start an if else while loop to check on starting parameter
            if nselected <= targetPntCnt:
                print("Reconstruction Uncertatiny Value will be %s" %reconThreshold)
            else:
                while solved == 0:
                    reconThreshold += 0.5
                    f.selectPoints(reconThreshold)
                    nselected = len([p for p in c3.point_cloud.points if p.selected])
                    if nselected <= targetPntCnt:
                        print("Reconstruction Uncertainty Value will be: %s" %reconThreshold)
                        solved = 1


            # Now that the threshold is determined, start the removal process
            # Reset solved variable to 0
            solved = 0
            count = 1
            print("Starting conservative point removal process for reconstruction uncertainty")
            ##print("just checking that recon uncertain still set at twelve: %s" %reconThreshold)
            while solved == 0 and count < maxIter:
                f.selectPoints(reconThreshold)
                nselected = len([p for p in c3.point_cloud.points if p.selected])
                print("Removing %s points on iteration number %s" %(nselected,count))
                c3.point_cloud.removeSelectedPoints()
                c3.optimizeCameras(fit_f=f_1, fit_cx=cx_1, fit_cy=cy_1, fit_b1=b1_1, fit_b2=b2_1, fit_k1=k1_1, fit_k2=k2_1, fit_k3=k3_1, fit_k4=k4_1, fit_p1=p1_1, fit_p2=p2_1, fit_corrections=additCor, tiepoint_covariance=True)
                ## This distn't help like I thoguht it might## f.resetSelection()
                f = Metashape.PointCloud.Filter()
                f.init(c3, criterion = Metashape.PointCloud.Filter.ReconstructionUncertainty)
                f.selectPoints(reconThreshold)
                nselected = len([p for p in c3.point_cloud.points if p.selected])
                if nselected == 0:
                    solved = 1
                    print("Reconstruction Uncertainty Error reduction complete")
                else:
                    solved = 0
                    count += 1
        else:
            print("Must choose whether you want an aggressive or conservative error reduction process.  Script ending!")
            raise ValueError()


        if aggressive == True:
            c3.label = "ER Recon Unc-%s"%(curVal)
        else:
            c3.label = "ER Recon Unc-%s"%(reconThreshold)

        doc.save()

        #Dublicate the chunk, unfix the calibration, and optimzie with the given parameters
        c4 = c3.copy()

        # After Reconstruction uncertainty, do projection accuracy
        # First resent the point count and target point count to the new level after the first step

        PntCnt = len(c4.point_cloud.points)
        print("Sparse cloud point count after first step: %s" %PntCnt)
        targetPntCnt = int(PntCnt/2)
        print("New Target Point Count: %s" %targetPntCnt)

        # Initiate a filter, first for recon uncert at default level
        f.init(c4, criterion = Metashape.PointCloud.Filter.ProjectionAccuracy)
        f.selectPoints(projThreshold)
        nselected = len([p for p in c4.point_cloud.points if p.selected])
        #Set up variable for while loop if raising threshold is necessary.  Can remove the points here sine this is Proj Acc is not an interative process
        solved = 0
        #Start an if else while loop to check on starting parameter
        if nselected <= targetPntCnt:
            c4.point_cloud.removeSelectedPoints()
            print("Projecion Accuracy Attained: %s" %projThreshold)
            c4.optimizeCameras(fit_f=f_1, fit_cx=cx_1, fit_cy=cy_1, fit_b1=b1_1, fit_b2=b2_1, fit_k1=k1_1, fit_k2=k2_1, fit_k3=k3_1, fit_k4=k4_1, fit_p1=p1_1, fit_p2=p2_1, fit_corrections=additCor, tiepoint_covariance=True)
        else:
            while solved == 0:
                projThreshold += 0.5
                f.selectPoints(projThreshold)
                nselected = len([p for p in c4.point_cloud.points if p.selected])
                if nselected <= targetPntCnt:
                    c4.point_cloud.removeSelectedPoints()
                    print("Projecion Accuracy Attained:")
                    c4.optimizeCameras(fit_f=f_1, fit_cx=cx_1, fit_cy=cy_1, fit_b1=b1_1, fit_b2=b2_1, fit_k1=k1_1, fit_k2=k2_1, fit_k3=k3_1, fit_k4=k4_1, fit_p1=p1_1, fit_p2=p2_1, fit_corrections=additCor, tiepoint_covariance=True)
                    print(projThreshold)
                    solved = 1

        doc.save()

        #Calculate script run time before makeing pop-up boxes
        endTime = time.time()
        processTime = str((endTime-startTime)/60)
        print("Script took %s minutes to run!" %processTime)

        #doc.save(proj)
        #Update new chuck label and add message box for completing error reduction

        if aggressive == True:
            c4.label = "ER Recon Unc-%s,Proj Acc-%s"%(curVal,projThreshold)
            print("Error reduction steps one and two complete with the following values: \n Reconstruction uncertainty: %s \n and Projection accuracy:%s.  \n Be sure to check that all cameras still have at least 100 projections.  " %(curVal,projThreshold))
        else:
            c4.label = "ER Recon Unc-%s,Proj Acc-%s"%(reconThreshold,projThreshold)
            print("Error reduction steps one and two complete with the following values: \n Reconstruction uncertainty: %s \n and Projection accuracy:%s.  \n Be sure to check that all cameras still have at least 100 projections.  " %(reconThreshold,projThreshold))







        #Look for wehether to print a warning about cameras being removed due to too few projections
        cameraEnd = 0
        for i in c3.cameras:
            try:
                if len(i.center) > 0:
                    cameraEnd +=1
            except:
                pass

        if cameraStart > cameraEnd:
            camDiff = cameraStart - cameraEnd
            message = "WARNING! Error reduction process removed %s cameras!  Consider repeating the process with higher selection criteria"%camDiff
            Metashape.app.messageBox(textwrap.fill(message,65))

        print("Script complete!")









#Define the  tool and UI to Run just the recon uncertainty/proj acc error reduction.
def erReconProj():
    global doc
    doc = Metashape.app.document
    proceed = Metashape.app.getBool("This tool will perform error reduction for reconstruction uncertanty and projection accuarcy before adding control/scale.  Continue?")
    if proceed == True:
        app = QtWidgets.QApplication.instance()
        parent = app.activeWindow()
        dlg = ErrRedReconProjDlg(parent)


class ErrRedReconProjDlg(QtWidgets.QDialog):

    def __init__(self, parent):
        QtWidgets.QDialog.__init__(self, parent)
        self.setWindowTitle("Error Reduction-Reconstruction Uncertainty and Projection Accuracy")


        #Add a label in order to add some distance
        self.label2 = QtWidgets.QLabel()
        self.label2.setText("\n Choose the Model Parameters for Optimizing Cameras")

        #Add buttons for camera parameters.
        self.f = QtWidgets.QCheckBox("Fit f")
        self.f.setChecked(True)
        self.c = QtWidgets.QCheckBox("Fit cx,cy")
        self.c.setChecked(True)
        self.k1 = QtWidgets.QCheckBox("Fit k1")
        self.k1.setChecked(True)
        self.k2 = QtWidgets.QCheckBox("Fit k2")
        self.k2.setChecked(True)
        self.k3 = QtWidgets.QCheckBox("Fit k3")
        self.k3.setChecked(True)
        self.k4 = QtWidgets.QCheckBox("Fit k4")
        self.b1 = QtWidgets.QCheckBox("Fit b1")
        self.b2 = QtWidgets.QCheckBox("Fit b2")
        self.p1 = QtWidgets.QCheckBox("Fit p1")
        self.p1.setChecked(True)
        self.p2 = QtWidgets.QCheckBox("Fit p2")
        self.p2.setChecked(True)
        self.adlCor = QtWidgets.QCheckBox("Fit additional corrections")

        #Add another label to get reconstruction uncertainty.
        self.label3 = QtWidgets.QLabel()
        self.label3.setText("\nTarget Error Reduction Values.")

        #Create widget for reconstruction uncertainty
        self.reconUncSpn = QtWidgets.QDoubleSpinBox()
        self.reconUncSpn.setDecimals(1)
        self.reconUncSpn.setValue(10.0)
        self.reconUncSpn.setRange(1.0,50.0)
        #Create an accompanying label
        self.spinReconLab = QtWidgets.QLabel()
        self.spinReconLab.setText("Reconstruction Uncertainty:")

        #Create one for projection accuracy
        self.projAccSpn = QtWidgets.QDoubleSpinBox()
        self.projAccSpn.setDecimals(1)
        self.projAccSpn.setValue(3.0)
        self.projAccSpn.setRange(1.0,50.0)
        self.spinProjLab = QtWidgets.QLabel()
        self.spinProjLab.setText("Projection Accuracy:")

        #Create widget for the maximum number of iterations for reconstructdion uncertainty
        self.spinMaxIter = QtWidgets.QSpinBox()
        self.spinMaxIter.setMinimum(0)
        self.spinMaxIter.setMaximum(50)
        self.spinMaxIter.setValue(10)
        self.spinMaxIter.setToolTip("This script iteratively removes points based on reconscruction uncertainty. \n Specifiy a maximum number of iterations greater than two.")
        self.spinIterLab = QtWidgets.QLabel()
        self.spinIterLab.setText("Maximum Iterations")

        #Add widget for aggressive or conservative error reduction
        self.label4 = QtWidgets.QLabel()
        self.label4.setText("\n \n \nWould you like a more aggressive error reduction for reconstruction uncertainty?  If Yes, script iteratively \n removes up to 50% of points until the target threshold or the maximum number of iterations is reached.  \n If no, the script raises the reconstruction uncertanty to a level where ~50% of the original cloud is removed.")
        self.aggYes = QtWidgets.QCheckBox("Use Aggressive Error Reduction")
        self.aggYes.setChecked(True)

        #Create a start button to trigger functions when clicked
        self.btnStart = QtWidgets.QPushButton("Run")
        self.btnQuit= QtWidgets.QPushButton("Quit")



        layout = QtWidgets.QGridLayout()



        layout.addWidget(self.label3,0,0,2,0)
        layout.addWidget(self.reconUncSpn,2,1)
        layout.addWidget(self.spinReconLab,2,0)
        layout.addWidget(self.projAccSpn,3,1)
        layout.addWidget(self.spinProjLab,3,0)
        layout.addWidget(self.spinMaxIter,4,1)
        layout.addWidget(self.spinIterLab,4,0)
        layout.addWidget(self.label2,5,0,2,0)
        #Add camera equation parameter selection
        layout.addWidget(self.f,8,0)
        layout.addWidget(self.b1,11,1)
        layout.addWidget(self.c,8,1)
        layout.addWidget(self.b2,12,1)
        layout.addWidget(self.k1,9,0)
        layout.addWidget(self.p1,9,1)
        layout.addWidget(self.k2,10,0)
        layout.addWidget(self.p2,10,1)
        layout.addWidget(self.k3,11,0)
        #layout.addWidget(self.p3,12,1)
        layout.addWidget(self.k4,12,0)
        #layout.addWidget(self.p4,13,1)
        layout.addWidget(self.adlCor,13,0)
        layout.addWidget(self.label4,18,0,5,3)
        layout.addWidget(self.aggYes,25,0)
        layout.addWidget(self.btnStart,40,0)
        layout.addWidget(self.btnQuit,40,1)


        self.setLayout(layout)



        proc_er12 = lambda : self.erReconProj()


        QtCore.QObject.connect(self.btnStart, QtCore.SIGNAL("clicked()"), self, QtCore.SLOT("accept()"))
        QtCore.QObject.connect(self.btnStart, QtCore.SIGNAL("clicked()"), proc_er12)
        QtCore.QObject.connect(self.btnQuit, QtCore.SIGNAL("clicked()"), self, QtCore.SLOT("reject()"))


        self.exec()


    def erReconProj(self):
        #Record start time to calculate process run time
        startTime = time.time()

        #Round up the user input into a more reasonable framework

        print("Solving for the following camera parameters")
        f_1=self.f.isChecked()
        if f_1 == True:
            print("f")
        cx_1=self.c.isChecked()
        cy_1=self.c.isChecked()
        if cx_1 == True and cy_1 == True:
            print("c")
        k1_1=self.k1.isChecked()
        if k1_1 == True:
            print("k1")
        k2_1=self.k2.isChecked()
        if k2_1 == True:
            print("k2")
        k3_1=self.k3.isChecked()
        if k3_1 == True:
            print("k3")
        k4_1=self.k4.isChecked()
        if k4_1 == True:
            print("k4")
        b1_1=self.b1.isChecked()
        if b1_1 == True:
            print("b1")
        b2_1=self.b2.isChecked()
        if b2_1 == True:
            print("b2")
        p1_1=self.p1.isChecked()
        if p1_1 == True:
            print("p1")
        p2_1=self.p2.isChecked()
        if p2_1 == True:
            print("p2")
        additCor=self.adlCor.isChecked()
        if additCor:
            print("Fitting additional corrections")


        reconThreshold = float(self.reconUncSpn.value())
        print("Reconstruction uncertainty %s" %reconThreshold)
        projThreshold = float(self.projAccSpn.value())
        print("Projection Accuracy %s" %projThreshold)
        maxIter = int(self.spinMaxIter.value())
        print("Maximum nubmer of iterations: %s" %maxIter)

        aggressive = self.aggYes.isChecked()
        if aggressive == True:
            print("Using aggressive error reduction")

        chunk = Metashape.app.document.chunk # active chunk
        doc = Metashape.app.document
        #Before starting error reduction, get a count of how many active cmaeras are thre to begin with.
        cameraStart = 0
        for i in chunk.cameras:
            try:
                if len(i.center) > 0:
                    cameraStart +=1
            except:
                pass

        #Start the error reduction process
        if aggressive == True:
            ##Start error reduction
            ##Iniitate a filter for tie point gradual selection
            f = Metashape.PointCloud.Filter()
            f.init(chunk, criterion = Metashape.PointCloud.Filter.ReconstructionUncertainty)
            ##Start an iteritive loop to gradually select down from starting to minimuum value
            count = 1
            curVal = reconThreshold + 5
            minVal = reconThreshold
            while curVal > minVal and count < maxIter:
                pntCnt = len(chunk.point_cloud.points)
                maxPnts = int(pntCnt * 0.49)
                minPnts = int(pntCnt * 0.45)
                f.selectPoints(curVal)
                nselected = len([p for p in chunk.point_cloud.points if p.selected])
                if nselected > maxPnts:
                    ##If the selection value is so low that too many points are selected, increase the selection value
                    print("Too many points selected at level %s, increasing value and selecting again" %curVal)
                    curVal += 0.01
                elif nselected < maxPnts and nselected > minPnts:
                    # If 45-49% of points are selected, remove those points, optimize cameras, reset the filter and decrease the selection criteria
                    chunk.point_cloud.removeSelectedPoints()
                    print("Removed %s points at a level of %s, optimizing cameras and decreasing value for next round"%(nselected,curVal))
                    chunk.optimizeCameras(fit_f=f_1, fit_cx=cx_1, fit_cy=cy_1, fit_b1=b1_1, fit_b2=b2_1, fit_k1=k1_1, fit_k2=k2_1, fit_k3=k3_1, fit_k4=k4_1, fit_p1=p1_1, fit_p2=p2_1, fit_corrections=additCor, tiepoint_covariance=True)
                    f = Metashape.PointCloud.Filter()
                    #For some reason, the program freeezes at the line below at certain values
                    f.init(chunk, criterion = Metashape.PointCloud.Filter.ReconstructionUncertainty)
                    curVal -= 0.05
                    count += 1
                    #Check to see if this decrement set the value below your target.
                    # If so, set current value to the target value
                    if curVal < minVal:
                        curVal = minVal
                        ## Make sure that the .05 decrement dosn't lead to more than 10% of points being selected
                        pntCnt = len(chunk.point_cloud.points)
                        maxPnts = int(pntCnt * 0.49)
                        f.selectPoints(curVal)
                        nselected = len([p for p in chunk.point_cloud.points if p.selected])
                        #If more than 10% selected, bump the value back up to maintain the while loop.
                        ##Otherwise let the current value equal the target value so that the decrementing loop ends.
                        if nselected > maxPnts:
                            curVal += 0.01
                elif nselected < minPnts:
                    ##Speed up getting to the mininum value by making sure at least 8% of points are selected
                    print("Too few points selected at level %s, decreasing value for quicker processing" %curVal)
                    curVal -= 0.01
                    ##Make sure that value for next step never goes below minimum value
                    if curVal < minVal:
                        curVal = minVal
                else:
                    print("This case should never happen.  If it does, check the code!")


            print("Target value achieved, iteratively selecting and removing at this level!")


            ## double check that the current value is at the min Value and that the filter is reset.
            curVal = reconThreshold
            f = Metashape.PointCloud.Filter()
            f.init(chunk, criterion = Metashape.PointCloud.Filter.ReconstructionUncertainty)


            ## Set up a solved value for while loop to iteratively remove all points at target level
            solved = 0
            while solved == 0 and count < maxIter:
                pntCnt = len(chunk.point_cloud.points)
                maxPnts = int(pntCnt * 0.49)
                f.selectPoints(curVal)
                nselected = len([p for p in chunk.point_cloud.points if p.selected])
                if nselected == 0:
                    print("No more points selected at this level, error reduction complete to a level of %s" %curVal)
                    solved = 1
                elif nselected > maxPnts:
                    print("Too many points selected, This shouldn't happen!")
                    break
                else:
                    chunk.point_cloud.removeSelectedPoints()
                    print("Removed %s points on iteration number %s" %(nselected,count))
                    chunk.optimizeCameras(fit_f=f_1, fit_cx=cx_1, fit_cy=cy_1, fit_b1=b1_1, fit_b2=b2_1, fit_k1=k1_1, fit_k2=k2_1, fit_k3=k3_1, fit_k4=k4_1, fit_p1=p1_1, fit_p2=p2_1, fit_corrections=additCor, tiepoint_covariance=True)
                    f = Metashape.PointCloud.Filter()
                    f.init(chunk, criterion = Metashape.PointCloud.Filter.ReconstructionUncertainty)
                    count += 1

        elif aggressive == False:
            ## First address reconstruction uncertainty, aim to get a level of 10.
            ##First determine the starting level.  Start at 10 and increment up if necessary
            PntCnt = len(chunk.point_cloud.points)
            print("Sparse cloud point count after first step: %s" %PntCnt)
            targetPntCnt = int(PntCnt/2)
            print("New Target Point Count: %s" %targetPntCnt)



            ## Initiate a filter, first for recon uncert at default level
            f = Metashape.PointCloud.Filter()
            f.init(chunk, criterion = Metashape.PointCloud.Filter.ReconstructionUncertainty)
            f.selectPoints(reconThreshold)
            nselected = len([p for p in chunk.point_cloud.points if p.selected])
            ##Set up variable for while loop if raising threshold is necessary
            solved = 0
            #Start an if else while loop to check on starting parameter
            if nselected <= targetPntCnt:
                print("Reconstruction Uncertatiny Value will be %s" %reconThreshold)
            else:
                while solved == 0:
                    reconThreshold += 0.5
                    f.selectPoints(reconThreshold)
                    nselected = len([p for p in chunk.point_cloud.points if p.selected])
                    if nselected <= targetPntCnt:
                        print("Reconstruction Uncertainty Value will be: %s" %reconThreshold)
                        solved = 1


            ## Now that the threshold is determined, start the removal process
            ## Reset solved variable to 0
            solved = 0
            count = 1
            print("Starting conservative point removal process for reconstruction uncertainty")
            ##print("just checking that recon uncertain still set at twelve: %s" %reconThreshold)
            while solved == 0 and count < maxIter:
                f.selectPoints(reconThreshold)
                nselected = len([p for p in chunk.point_cloud.points if p.selected])
                print("Removing %s points on iteration number %s" %(nselected,count))
                chunk.point_cloud.removeSelectedPoints()
                chunk.optimizeCameras(fit_f=f_1, fit_cx=cx_1, fit_cy=cy_1, fit_b1=b1_1, fit_b2=b2_1, fit_k1=k1_1, fit_k2=k2_1, fit_k3=k3_1, fit_k4=k4_1, fit_p1=p1_1, fit_p2=p2_1, fit_corrections=additCor, tiepoint_covariance=True)
                ## This distn't help like I thoguht it might## f.resetSelection()
                f = Metashape.PointCloud.Filter()
                f.init(chunk, criterion = Metashape.PointCloud.Filter.ReconstructionUncertainty)
                f.selectPoints(reconThreshold)
                nselected = len([p for p in chunk.point_cloud.points if p.selected])
                if nselected == 0:
                    solved = 1
                    print("Reconstruction Uncertainty Error reduction complete")
                else:
                    solved = 0
                    count += 1
        if aggressive == True:
            chunk.label = "ER Recon Unc-%s,Proj Acc-%s"%(curVal,projThreshold)
            doc.save()
            print("Error reduction steps one and two complete with the following values: \n Reconstruction uncertainty: %s \n and Projection accuracy:%s.  \n Be sure to check that all cameras still have at least 100 projections.  " %(curVal,projThreshold))
        else:
            chunk.label = "ER Recon Unc-%s,Proj Acc-%s"%(reconThreshold,projThreshold)
            doc.save()
            print("Error reduction steps one and two complete with the following values: \n Reconstruction uncertainty: %s \n and Projection accuracy:%s.  \n Be sure to check that all cameras still have at least 100 projections.  " %(reconThreshold,projThreshold))



        ## After Reconstruction uncertainty, do projection accuracy
        ## First resent the point count and target point count to the new level after the first step

        PntCnt = len(chunk.point_cloud.points)
        print("Sparse cloud point count after first step: %s" %PntCnt)
        targetPntCnt = int(PntCnt/2)
        print("New Target Point Count: %s" %targetPntCnt)

        ## Initiate a filter, first for recon uncert at default level
        f.init(chunk, criterion = Metashape.PointCloud.Filter.ProjectionAccuracy)
        f.selectPoints(projThreshold)
        nselected = len([p for p in chunk.point_cloud.points if p.selected])
        ##Set up variable for while loop if raising threshold is necessary.  Can remove the points here sine this is Proj Acc is not an interative process
        solved = 0
        #Start an if else while loop to check on starting parameter
        if nselected <= targetPntCnt:
            chunk.point_cloud.removeSelectedPoints()
            print("Projecion Accuracy Attained: %s" %projThreshold)
            chunk.optimizeCameras(fit_f=f_1, fit_cx=cx_1, fit_cy=cy_1, fit_b1=b1_1, fit_b2=b2_1, fit_k1=k1_1, fit_k2=k2_1, fit_k3=k3_1, fit_k4=k4_1, fit_p1=p1_1, fit_p2=p2_1, fit_corrections=additCor, tiepoint_covariance=True)
        else:
            while solved == 0:
                projThreshold += 0.5
                f.selectPoints(projThreshold)
                nselected = len([p for p in chunk.point_cloud.points if p.selected])
                if nselected <= targetPntCnt:
                    chunk.point_cloud.removeSelectedPoints()
                    print("Projecion Accuracy Attained:")
                    chunk.optimizeCameras(fit_f=f_1, fit_cx=cx_1, fit_cy=cy_1, fit_b1=b1_1, fit_b2=b2_1, fit_k1=k1_1, fit_k2=k2_1, fit_k3=k3_1, fit_k4=k4_1, fit_p1=p1_1, fit_p2=p2_1, fit_corrections=additCor, tiepoint_covariance=True)
                    print(projThreshold)
                    solved = 1

        #Print message to indicate process done

        if aggressive == True:
            chunk.label = "ER Recon Unc-%s,Proj Acc-%s"%(curVal,projThreshold)
            doc.save()
            print("Error reduction steps one and two complete with the following values: \n Reconstruction uncertainty: %s \n and Projection accuracy:%s.  \n Be sure to check that all cameras still have at least 100 projections.  " %(curVal,projThreshold))
        else:
            chunk.label = "ER Recon Unc-%s,Proj Acc-%s"%(reconThreshold,projThreshold)
            doc.save()
            print("Error reduction steps one and two complete with the following values: \n Reconstruction uncertainty: %s \n and Projection accuracy:%s.  \n Be sure to check that all cameras still have at least 100 projections.  " %(reconThreshold,projThreshold))

        #Look for wehether to print a warning about cameras being removed due to too few projections
        cameraEnd = 0
        endTime = time.time()
        processTime = str((endTime-startTime)/60)
        print("Script took %s minutes to run!" %processTime)
        for i in chunk.cameras:
            try:
                if len(i.center) > 0:
                    cameraEnd +=1
            except:
                pass

        if cameraStart > cameraEnd:
            camDiff = cameraStart - cameraEnd
            message = "WARNING! Error reduction process removed %s cameras!  Consider repeating the process with higher selection criteria"%camDiff
            Metashape.app.messageBox(textwrap.fill(message,65))

        print("Script complete!")


#Implement the process for running just reprojection error reduction
def erReprojectionError():
    global doc
    doc = Metashape.app.document
    proceed = Metashape.app.getBool("Make sure that you've adjusted GCP/Scale/Tie Point Accuracy.  This tool alters and saves the active chunk.  Continue?")
    if proceed == True:
        app = QtWidgets.QApplication.instance()
        parent = app.activeWindow()
        dlg = ReprojAccDlg(parent)


class ReprojAccDlg(QtWidgets.QDialog):

    def __init__(self, parent):
        QtWidgets.QDialog.__init__(self, parent)
        self.setWindowTitle("Reprojection Error Reduction and Product Creation")


        #Add a label in order to add some distance
        self.label2 = QtWidgets.QLabel()
        self.label2.setText("\n Choose the Model Parameters for Optimizing Cameras")

        #Add buttons for camera parameters.
        self.f = QtWidgets.QCheckBox("Fit f")
        self.f.setChecked(True)
        self.c = QtWidgets.QCheckBox("Fit cx,cy")
        self.c.setChecked(True)
        self.k1 = QtWidgets.QCheckBox("Fit k1")
        self.k1.setChecked(True)
        self.k2 = QtWidgets.QCheckBox("Fit k2")
        self.k2.setChecked(True)
        self.k3 = QtWidgets.QCheckBox("Fit k3")
        self.k3.setChecked(True)
        self.k4 = QtWidgets.QCheckBox("Fit k4")
        self.b1 = QtWidgets.QCheckBox("Fit b1")
        self.b2 = QtWidgets.QCheckBox("Fit b2")
        self.p1 = QtWidgets.QCheckBox("Fit p1")
        self.p1.setChecked(True)
        self.p2 = QtWidgets.QCheckBox("Fit p2")
        self.p2.setChecked(True)
        self.adlCor = QtWidgets.QCheckBox("Fit additional corrections")

        #Add another label to get reconstruction uncertainty.
        self.label3 = QtWidgets.QLabel()
        self.label3.setText("\nTarget Error Reduction Values.")

        #Create widget for reprojection error
        self.reprojErrSpn = QtWidgets.QDoubleSpinBox()
        self.reprojErrSpn.setDecimals(1)
        self.reprojErrSpn.setValue(.3)
        self.reprojErrSpn.setRange(0.1,5.0)
        self.reprojErrSpn.setToolTip("WARNING: Metashape periodically freezes and crashes with values less than 0.3")
        #Create an accompanying label
        self.spinReprojLab = QtWidgets.QLabel()
        self.spinReprojLab.setText("Reprojection Error")



        #Create widget for the maximum number of iterations for reconstructdion uncertainty
        self.spinMaxIter = QtWidgets.QSpinBox()
        self.spinMaxIter.setMinimum(0)
        self.spinMaxIter.setMaximum(50)
        self.spinMaxIter.setValue(10)
        self.spinMaxIter.setToolTip("This script iteratively removes points based on reconscruction uncertainty. \n Specifiy a maximum number of iterations greater than two.")
        self.spinIterLab = QtWidgets.QLabel()
        self.spinIterLab.setText("Maximum Iterations")


        #Create a start button to trigger functions when clicked
        self.btnStart = QtWidgets.QPushButton("Run")
        self.btnQuit= QtWidgets.QPushButton("Quit")

        #Add widget to process dense point cloud, should call separate class to add DPC optoins
        self.processDPCChk = QtWidgets.QCheckBox("Process Dense Point Cloud?")

        self.qualityChoice = QtWidgets.QComboBox()
        qualityOptions = ["Ultra High", "High","Medium", "Low", "Lowest"]
        for i in qualityOptions:
            self.qualityChoice.addItem(i)
        self.qualityChoice.setCurrentText("High")
        #Add label
        self.dpcLab = QtWidgets.QLabel()
        self.dpcLab.setText("Dense Point Cloud Quality")


        self.depthFilteringChoice = QtWidgets.QComboBox()
        filteringOptions = ["Disabled", "Mild","Moderate", "Aggressive"]
        for i in filteringOptions:
            self.depthFilteringChoice.addItem(i)
        self.depthFilteringChoice.setCurrentText("Aggressive")
        #Add label
        self.depthLab = QtWidgets.QLabel()
        self.depthLab.setText("Depth Filtering")

        self.calcPointColors = QtWidgets.QCheckBox("Calculate point colors?")
        self.calcPointColors.setChecked(True)

        #Then add DEM optoins
        self.processDEM = QtWidgets.QCheckBox("Build DEM?")


        #Set basic DEM Parameters
        self.interpolationChoice = QtWidgets.QComboBox()
        interpolationOptions = ["Enabled-default", "Disabled","Extrapolated"]
        for i in interpolationOptions:
            self.interpolationChoice.addItem(i)
        self.interpolationChoice.setCurrentText("Enabled-default")
        #Add label
        self.interpolationLab = QtWidgets.QLabel()
        self.interpolationLab.setText("DEM Interpolation")

        #Then add Ortho optoins
        self.processOrtho = QtWidgets.QCheckBox("Build Orthomosaic?")

        #Set basic Ortho Parameters
        self.blendingChoice = QtWidgets.QComboBox()
        blendingOptions = ["Mosaic-Default", "Disabled","Average"]
        for i in blendingOptions:
            self.blendingChoice.addItem(i)
        self.blendingChoice.setCurrentText("Mosaic-Default")
        #Add label
        self.blendingLab = QtWidgets.QLabel()
        self.blendingLab.setText("Blending mode:")

        #Enable hole filling?
        self.fillHoles = QtWidgets.QCheckBox("Enable Hole Filling?")
        self.fillHoles.setChecked(True)

        #Enable refine seamlines?
        self.refineSeamlines = QtWidgets.QCheckBox("Refine Seamlines?")
        self.refineSeamlines.setChecked(True)




        layout = QtWidgets.QGridLayout()

        layout.addWidget(self.label2,4,0,2,0)
        #Add camera equation parameter selection
        layout.addWidget(self.label3,0,0,2,0)
        layout.addWidget(self.reprojErrSpn,2,1)
        layout.addWidget(self.spinReprojLab,2,0)
        layout.addWidget(self.spinMaxIter,3,1)
        layout.addWidget(self.spinIterLab,3,0)
        layout.addWidget(self.f,6,0)
        layout.addWidget(self.b1,9,1)
        layout.addWidget(self.c,6,1)
        layout.addWidget(self.b2,10,1)
        layout.addWidget(self.k1,7,0)
        layout.addWidget(self.p1,7,1)
        layout.addWidget(self.k2,8,0)
        layout.addWidget(self.p2,8,1)
        layout.addWidget(self.k3,9,0)
        layout.addWidget(self.k4,10,0)
        layout.addWidget(self.adlCor,11,0)
        layout.addWidget(self.processDPCChk,12,0)
        layout.addWidget(self.calcPointColors,12,1)
        layout.addWidget(self.dpcLab,13,0)
        layout.addWidget(self.qualityChoice,13,1)
        layout.addWidget(self.depthLab,14,0)
        layout.addWidget(self.depthFilteringChoice,14,1)
        layout.addWidget(self.processDEM,15,0)
        layout.addWidget(self.interpolationLab,16,0)
        layout.addWidget(self.interpolationChoice,16,1)
        layout.addWidget(self.processOrtho,17,0)
        layout.addWidget(self.blendingLab,18,0)
        layout.addWidget(self.blendingChoice,18,1)
        layout.addWidget(self.fillHoles,19,0)
        layout.addWidget(self.refineSeamlines,19,1)
        layout.addWidget(self.btnStart,40,0)
        layout.addWidget(self.btnQuit,40,1)


        self.setLayout(layout)

        #Set which widgets should be invisible by default!
        self.qualityChoice.hide()
        self.dpcLab.hide()
        self.qualityChoice.hide()
        self.depthLab.hide()
        self.depthFilteringChoice.hide()
        self.calcPointColors.hide()
        self.processDEM.hide()
        self.interpolationLab.hide()
        self.interpolationChoice.hide()
        self.processOrtho.hide()
        self.blendingChoice.hide()
        self.blendingLab.hide()
        self.fillHoles.hide()
        self.refineSeamlines.hide()





        proc_er3 = lambda : self.errorReductionReprojErr()
        proc_addDPC = lambda: self.addDPCOptions()
        proc_addDEM = lambda: self.addDEMOptions()
        proc_addOrtho = lambda: self.addOrthoOptions()

        self.processDPCChk.stateChanged.connect(proc_addDPC)
        self.processDEM.stateChanged.connect(proc_addDEM)
        self.processOrtho.stateChanged.connect(proc_addOrtho)
        QtCore.QObject.connect(self.btnStart, QtCore.SIGNAL("clicked()"), self, QtCore.SLOT("accept()"))
        QtCore.QObject.connect(self.btnStart, QtCore.SIGNAL("clicked()"), proc_er3)
        QtCore.QObject.connect(self.btnQuit, QtCore.SIGNAL("clicked()"), self, QtCore.SLOT("reject()"))


        self.exec()


    def addDPCOptions(self):
        vis = self.processDPCChk.checkState()
        self.qualityChoice.setVisible(vis)
        self.dpcLab.setVisible(vis)
        self.qualityChoice.setVisible(vis)
        self.depthLab.setVisible(vis)
        self.depthFilteringChoice.setVisible(vis)
        self.calcPointColors.setVisible(vis)
        self.processDEM.setVisible(vis)
        if vis == False:
            self.interpolationLab.setVisible(False)
            self.interpolationChoice.setVisible(False)
            self.blendingChoice.setVisible(False)
            self.blendingLab.setVisible(False)
            self.processOrtho.setVisible(False)
            self.processOrtho.setChecked(False)
            self.processDEM.setVisible(False)
            self.processDEM.setChecked(False)
            self.fillHoles.setVisible(False)
            self.refineSeamlines.setVisible(False)



    def addDEMOptions(self):
        vis2= self.processDEM.checkState()
        self.interpolationLab.setVisible(vis2)
        self.interpolationChoice.setVisible(vis2)
        self.processOrtho.setVisible(vis2)
        if vis2 == False:
            self.blendingChoice.setVisible(False)
            self.blendingLab.setVisible(False)
            self.processOrtho.setVisible(False)
            self.processOrtho.setChecked(False)
            self.fillHoles.setVisible(False)
            self.refineSeamlines.setVisible(False)

    def addOrthoOptions(self):
        vis3 = self.processOrtho.checkState()
        self.blendingChoice.setVisible(vis3)
        self.blendingLab.setVisible(vis3)
        self.fillHoles.setVisible(vis3)
        self.refineSeamlines.setVisible(vis3)


    def errorReductionReprojErr(self):
        print("Solving for the following camera parameters")
        f_1=self.f.isChecked()
        if f_1 == True:
            print("f")
        cx_1=self.c.isChecked()
        cy_1=self.c.isChecked()
        if cx_1 == True and cy_1 == True:
            print("c")
        k1_1=self.k1.isChecked()
        if k1_1 == True:
            print("k1")
        k2_1=self.k2.isChecked()
        if k2_1 == True:
            print("k2")
        k3_1=self.k3.isChecked()
        if k3_1 == True:
            print("k3")
        k4_1=self.k4.isChecked()
        if k4_1 == True:
            print("k4")
        b1_1=self.b1.isChecked()
        if b1_1 == True:
            print("b1")
        b2_1=self.b2.isChecked()
        if b2_1 == True:
            print("b2")
        p1_1=self.p1.isChecked()
        if p1_1 == True:
            print("p1")
        p2_1=self.p2.isChecked()
        if p2_1 == True:
            print("p2")
        additCor=self.adlCor.isChecked()
        if additCor:
            print("Fitting additional corrections")

        minVal = float(self.reprojErrSpn.value())
        print("Target Reprojection Error Value: %s" %minVal)
        maxIter = int(self.spinMaxIter.value())
        print("Maximum nubmer of iterations: %s" %maxIter)

        #Round up input for Optional DPC generation
        processDensePC = self.processDPCChk.isChecked()
        if processDensePC == True:
            print("Processing Dense point Cloud")
            dpcColors = self.calcPointColors.isChecked()
            if self.qualityChoice.currentText() == "Ultra High":
                dpcQuality = 1
                print("Ultra DPC Quality")
            elif self.qualityChoice.currentText() == "High":
                dpcQuality = 2
                print("High DPC Quality")
            elif self.qualityChoice.currentText() == "Medium":
                dpcQuality = 4
                print("Medium DPC Quality")
            elif self.qualityChoice.currentText() == "Low":
                dpcQuality = 8
                print("Low DPC Quality")
            else:
                dpcQuality = 16
                print("Lowest DPC Quality")
            #Filtering options
            if self.depthFilteringChoice.currentText() == "Disabled":
                depthFilt = Metashape.FilterMode.NoFiltering
                print("Filtering Disabled")
            elif self.depthFilteringChoice.currentText() == "Mild":
                depthFilt = Metashape.FilterMode.MildFiltering
                print("Mild Filtering")
            elif self.depthFilteringChoice.currentText() == "Moderate":
                depthFilt = Metashape.FilterMode.ModerateFiltering
                print("Moderate Filtering")
            else:
                depthFilt = Metashape.FilterMode.AggressiveFiltering
                print("Aggressive Filtering")

        #Get the DEM stuff
        buildDEM = self.processDEM.isChecked()
        if buildDEM == True:
            if self.interpolationChoice.currentText() == "Enabled-default":
                interp = Metashape.Interpolation.EnabledInterpolation
                print("DEM Interpolation enabled")
            elif self.interpolationChoice.currentText() == "Disabled":
                interp = Metashape.Interpolation.DisapledInterpolation
                print("DEM Interpolation DISABLED")
            else:
                interp = Metashape.Interpolation.Extrapolated
                print("DEM Extrapolated")

        #Get the Ortho stuff
        buildOrtho = self.processOrtho.isChecked()
        if buildOrtho == True:
            fillOrthoHoles = self.fillHoles.isChecked()
            refineOrthoSeamlines = self.refineSeamlines.isChecked()
            if self.blendingChoice.currentText() == "Mosaic-Default":
                blendMethod = Metashape.BlendingMode.MosaicBlending
                print("Mosaic Ortho Blending")
            elif self.blendingChoice.currentText() == "Disabled":
                blendMethod = Metashape.BlendingMode.DisabledBlending
                print("Ortho blending disabled")
            else:
                blendMethod = Metashape.BlendingMode.AverageBlending
                print("Average Ortho Blending")

        #Get the start time
        startTime = time.time()
        doc = Metashape.app.document
        chunk = doc.chunk

        #Get the initial number of photos that contain projections
        cameraStart = 0
        for i in chunk.cameras:
            try:
                if len(i.center) > 0:
                    cameraStart +=1
            except:
                pass
        print("Starting with %s cameras"%cameraStart)
        startVal = 0.7
        #Make sure cameras are optimized with correct parameters
        chunk.optimizeCameras(fit_f=f_1, fit_cx=cx_1, fit_cy=cy_1, fit_b1=b1_1, fit_b2=b2_1, fit_k1=k1_1, fit_k2=k2_1, fit_k3=k3_1, fit_k4=k4_1, fit_p1=p1_1, fit_p2=p2_1, fit_corrections=additCor, tiepoint_covariance=True)

        if minVal > startVal:
            startVal = minVal

        #Iniitate a filter for tie point gradual selection
        f = Metashape.PointCloud.Filter()
        f.init(chunk, criterion = Metashape.PointCloud.Filter.ReprojectionError)
        #Start an iteritive loop to gradually select down from starting to minimuum value
        count = 1
        curVal = round(startVal,2)
        while curVal > minVal and count < maxIter:
            pntCnt = len(chunk.point_cloud.points)
            maxPnts = int(pntCnt * 0.1)
            minPnts = int(pntCnt * 0.08)
            f.selectPoints(curVal)
            nselected = len([p for p in chunk.point_cloud.points if p.selected])
            if nselected > maxPnts:
                #If the selection value is so low that too many points are selected, increase the selection value
                print("Too many points selected at level %s, increasing value and selecting again" %curVal)
                curVal += 0.01
            elif nselected < maxPnts and nselected > minPnts:
                # If 8-10% of points are selected, remove those points, optimize cameras, reset the filter and decrease the selection criteria
                chunk.point_cloud.removeSelectedPoints()
                print("Removed %s points at a level of %s, optimizing cameras and decreasing value for next round"%(nselected,curVal))
                chunk.optimizeCameras(fit_f=f_1, fit_cx=cx_1, fit_cy=cy_1, fit_b1=b1_1, fit_b2=b2_1, fit_k1=k1_1, fit_k2=k2_1, fit_k3=k3_1, fit_k4=k4_1, fit_p1=p1_1, fit_p2=p2_1, fit_corrections=additCor, tiepoint_covariance=True)
                #print("test1")
                f = Metashape.PointCloud.Filter()
                #print("test2")
                #For some reason, the program freeezes at the line below at certain values
                f.init(chunk, criterion = Metashape.PointCloud.Filter.ReprojectionError)
                #print("test3")
                curVal -= 0.05
                curVal = round(curVal,2)
                count += 1
                #Check to see if this decrement set the value below your target.
                # If so, set current value to the target value
                #print("test4")
                if curVal < minVal:
                    curVal = minVal
                    # Make sure that the .05 decrement dosn't lead to more than 10% of points being selected
                    pntCnt = len(chunk.point_cloud.points)
                    maxPnts = int(pntCnt * 0.1)
                    f.selectPoints(curVal)
                    nselected = len([p for p in chunk.point_cloud.points if p.selected])
                    #If more than 10% selected, bump the value back up to maintain the while loop.
                    #Otherwise let the current value equal the target value so that the decrementing loop ends.
                    if nselected > maxPnts:
                        curVal += 0.01
                #print("test5")
            elif nselected < minPnts:
                #Speed up getting to the mininum value by making sure at least 8% of points are selected
                print("Too few points selected at level %s, decreasing value for quicker processing" %curVal)
                curVal -= 0.01
                #Make sure that value for next step never goes below minimum value
                if curVal < minVal:
                    curVal = minVal
            else:
                print("This case should never happen.  If it does, check the code!")

        #print("Min value achieved, iteratively selecting and removing at this level!")

        # double check that the current value is at the min Value and that the filter is reset.
        if count < maxIter:
            curVal = minVal
        f = Metashape.PointCloud.Filter()
        f.init(chunk, criterion = Metashape.PointCloud.Filter.ReprojectionError)


        # Set up a solved value for while loop to iteratively remove all points at target level
        solved = 0
        while solved == 0 and count < maxIter:
            pntCnt = len(chunk.point_cloud.points)
            maxPnts = int(pntCnt * 0.1)
            f.selectPoints(curVal)
            nselected = len([p for p in chunk.point_cloud.points if p.selected])
            if nselected == 0:
                print("No more points selected at this level, error reduction complete to a level of %s" %curVal)
                solved = 1
            elif nselected > maxPnts:
                print("Too many points selected, This shouldn't happen!")
                break
            else:
                chunk.point_cloud.removeSelectedPoints()
                print("Removed %s points on iteration number %s" %(nselected,count))
                chunk.optimizeCameras(fit_f=f_1, fit_cx=cx_1, fit_cy=cy_1, fit_b1=b1_1, fit_b2=b2_1, fit_k1=k1_1, fit_k2=k2_1, fit_k3=k3_1, fit_k4=k4_1, fit_p1=p1_1, fit_p2=p2_1, fit_corrections=additCor, tiepoint_covariance=True)
                f = Metashape.PointCloud.Filter()
                f.init(chunk, criterion = Metashape.PointCloud.Filter.ReprojectionError)
                count += 1

        #Print message to indicate process done
        label = chunk.label
        suff =",Reproj Error-%s"%curVal
        newLabel = label + suff
        chunk.label = newLabel
        doc.save()
        #If process stops here use a message box.  If not, print to console.
        if processDensePC == False:
            if count >= maxIter:
                print("Process complete: loop broken because maximum number of iterations reached.  Be sure to check that all cameras still have at least 100 projections and that RMS has been lowered from original chunk.")
            else:
                print("Error reduction for projection reprojection error complete! Be sure to check that all cameras still have at least 100 projections and that RMS has been lowered from original chunk.")
        else:
            if count >= maxIter:
                print("Process complete: loop broken because maximum number of iterations reached.  Be sure to check that all cameras still have at least 100 projections and that RMS has been lowered from original chunk.")
            else:
                print("Error reduction for projection reprojection error complete! Be sure to check that all cameras still have at least 100 projections and that RMS has been lowered from original chunk.")




        #Look for wehether to print a warning about cameras being removed due to too few projections
        cameraEnd = 0
        for i in chunk.cameras:
            try:
                if len(i.center) > 0:
                    cameraEnd +=1
            except:
                pass

        if cameraStart > cameraEnd:
            camDiff = cameraStart - cameraEnd
            print("WARNING! Error reduction process removed %s cameras!  Consider repeating the process with higher selection criteria"%camDiff)




        #If processing products, duplicate chunk, rename, and run those processes

        if processDensePC == True:
            c2 = chunk.copy()
            print("Chunk duplication successful!")
            c2.label = "Process Products" #Rename the chunk
            doc.save()
            c2.buildDepthMaps(downscale = dpcQuality, filter_mode = depthFilt, reuse_depth = False)
            c2.buildDenseCloud(point_colors = dpcColors, point_confidence=True)
            doc.save()
            if buildDEM == True:
                c2.buildDem(source_data = Metashape.DataSource.DenseCloudData, interpolation = interp)
                doc.save()
                if buildOrtho == True:
                    c2.buildOrthomosaic(surface_data = Metashape.DataSource.ElevationData, blending_mode = blendMethod, fill_holes = fillOrthoHoles, refine_seamlines=refineOrthoSeamlines)
                    doc.save()

        endTime = time.time()
        processTime = str((endTime-startTime)/60)
        print("Script took %s minutes to run!" %processTime)
        print("Script complete!")



def copybb():
#copy bounding region for active chunk to all other chunks in workspace
#compatibility: Checked it in PhotoScan 1.4.2 and it worked.

    doc = Metashape.app.document

    chunk = doc.chunk
    T0 = chunk.transform.matrix

    region = chunk.region
    R0 = region.rot
    C0 = region.center
    s0 = region.size

    for chunk in doc.chunks:

        if chunk == doc.chunk:
            continue

        T = chunk.transform.matrix.inv() * T0

        R = Metashape.Matrix( [[T[0,0],T[0,1],T[0,2]], [T[1,0],T[1,1],T[1,2]], [T[2,0],T[2,1],T[2,2]]])

        scale = R.row(0).norm()
        R = R * (1/scale)

        region.rot = R * R0
        c = T.mulp(C0)
        region.center = c
        region.size = s0 * scale / 1.

        chunk.region = region

    print("Script finished. Bounding Region copied.\n")


class ProcDlgAllChecked(QtWidgets.QDialog):
#used by optimizecamcal

    def __init__ (self, parent):
        QtWidgets.QDialog.__init__(self, parent)

        chunk = doc.chunk

        self.setWindowTitle("Optimize All")

        self.btnQuit = QtWidgets.QPushButton("&Exit")
        self.btnQuit.setFixedSize(150,50)

        self.btnBP1 = QtWidgets.QPushButton("&Process")
        self.btnBP1.setFixedSize(150,50)

        self.pBar = QtWidgets.QProgressBar()
        #self.pBar.setTextVisible(False)
        self.pBar.setFixedSize(150, 50)

        self.tieerrTxt = QtWidgets.QLabel()
        self.tieerrTxt.setText("Tie point accuracy (pix): ")
        self.tieerrTxt.setFixedSize(200, 30)

        self.tieerrEdt = QtWidgets.QLineEdit()
        self.tieerrEdt.setPlaceholderText("Tie point error estimate e.g. 0.1")
        self.tieerrEdt.setFixedSize(125, 25)
        self.tieerrEdt.setText(str(chunk.tiepoint_accuracy))

        self.markerrTxt = QtWidgets.QLabel()
        self.markerrTxt.setText("Marker (control) accuracy (m): ")
        self.markerrTxt.setFixedSize(200, 30)

        self.markerrEdt = QtWidgets.QLineEdit()
        self.markerrEdt.setPlaceholderText("Marker (control) estimate e.g. 0.02")
        self.markerrEdt.setFixedSize(125, 35)
        self.markerrEdt.setText((str(chunk.marker_location_accuracy[0])) + "/"  + (str(chunk.marker_location_accuracy[1])) + "/"  + (str(chunk.marker_location_accuracy[2])))

        self.fitfBox = QtWidgets.QCheckBox("Fit f")
        self.fitfBox.setFixedSize(150,50)
        self.fitfBox.setChecked(1)

        self.fitcBox = QtWidgets.QCheckBox("Fit cx,cy")
        self.fitcBox.setFixedSize(150,50)
        self.fitcBox.setChecked(1)

        self.fitk1Box = QtWidgets.QCheckBox("Fit k1")
        self.fitk1Box.setFixedSize(150,50)
        self.fitk1Box.setChecked(1)
        self.fitk2Box = QtWidgets.QCheckBox("Fit k2")
        self.fitk2Box.setFixedSize(150,50)
        self.fitk2Box.setChecked(1)
        self.fitk3Box = QtWidgets.QCheckBox("Fit k3")
        self.fitk3Box.setFixedSize(150,50)
        self.fitk3Box.setChecked(1)

        self.fitk4Box = QtWidgets.QCheckBox("Fit k4")
        self.fitk4Box.setFixedSize(150,50)
        self.fitk4Box.setChecked(1)

        self.fitp1Box = QtWidgets.QCheckBox("Fit p1")
        self.fitp1Box.setFixedSize(150,50)
        self.fitp1Box.setChecked(1)
        self.fitp2Box = QtWidgets.QCheckBox("Fit p2")
        self.fitp2Box.setFixedSize(150,50)
        self.fitp2Box.setChecked(1)

        self.fitAddCorBox = QtWidgets.QCheckBox("Fit Additional Correctsion")
        self.fitAddCorBox.setFixedSize(150,50)
        self.fitAddCorBox.setChecked(1)

        self.fitb1Box = QtWidgets.QCheckBox("Fit b1")
        self.fitb1Box.setFixedSize(150,50)
        self.fitb1Box.setChecked(1)

        self.fitb2Box = QtWidgets.QCheckBox("Fit b2")
        self.fitb2Box.setFixedSize(150,50)
        self.fitb2Box.setChecked(1)

        layout = QtWidgets.QGridLayout()   #creating layout
        layout.setSpacing(1)
        layout.addWidget(self.tieerrTxt, 0, 0)
        layout.addWidget(self.tieerrEdt, 0, 1)

        layout.addWidget(self.markerrTxt, 1, 0)
        layout.addWidget(self.markerrEdt, 1, 1)

        layout.addWidget(self.fitfBox, 2, 0)
        layout.addWidget(self.fitcBox, 2, 1)
        layout.addWidget(self.fitk1Box, 3, 0)
        layout.addWidget(self.fitk2Box, 4, 0)
        layout.addWidget(self.fitk3Box, 5, 0)
        layout.addWidget(self.fitk4Box, 6, 0)
        layout.addWidget(self.fitb1Box, 5, 1)
        layout.addWidget(self.fitb2Box, 6, 1)
        layout.addWidget(self.fitp1Box, 3, 1)
        layout.addWidget(self.fitp2Box, 4, 1)
        layout.addWidget(self.fitAddCorBox,7,0)

        layout.addWidget(self.pBar, 4, 2)
        layout.addWidget(self.btnBP1, 3, 2)
        layout.addWidget(self.btnQuit, 0, 2)
        self.setLayout(layout)

#       self.widgets = [self.fitfBox, self.fitcBox, self.fitkBox, self.fitaspectBox, self.fitskewBox, self.fitpBox, self.fitk4Box, self.btnP1, self.btnQuit, self.errEdt, self.mnumEdt]
#        self.widgets = [self.fitfBox, self.fitcBox, self.fitkBox, self.fitaspectBox, self.fitskewBox, self.fitpBox, self.fitk4Box, self.fitp3p4Box, self.btnP1, self.btnQuit]
        self.widgets = [self.fitfBox, self.fitcBox, self.fitk1Box, self.fitk2Box, self.fitk3Box, self.fitk4Box, self.fitb1Box, self.fitb2Box, self.fitp1Box, self.fitp2Box, self.fitAddCorBox, self.btnBP1, self.btnQuit]

        proc_optimize = lambda : self.procOptimizeAllChecked()

        QtCore.QObject.connect(self.btnBP1, QtCore.SIGNAL("clicked()"), proc_optimize)
        QtCore.QObject.connect(self.btnQuit, QtCore.SIGNAL("clicked()"), self, QtCore.SLOT("reject()"))

        self.exec()

    def procOptimizeAllChecked(self):

        print("Script started")

        self.pBar.setMinimum(0)
        self.pBar.setMaximum(0)
        for widget in self.widgets:
            widget.setDisabled(True)

        f_1 = self.fitfBox.isChecked()
        cx_1 = self.fitcBox.isChecked()
        cy_1 = self.fitcBox.isChecked()
        k1_1 = self.fitk1Box.isChecked()
        k2_1 = self.fitk2Box.isChecked()
        k3_1 = self.fitk3Box.isChecked()
        k4_1 = self.fitk4Box.isChecked()
        b1_1 = self.fitb1Box.isChecked()
        b2_1 = self.fitb2Box.isChecked()
        p1_1 = self.fitp1Box.isChecked()
        p2_1 = self.fitp2Box.isChecked()
        additCor = self.fitAddCorBox.isChecked()


        QtWidgets.qApp.processEvents()

        stage = 0
        chunk = doc.chunk
        point_cloud = chunk.point_cloud
        projections = point_cloud.projections
        points = point_cloud.points
        QtWidgets.qApp.processEvents()
        chunk.tiepoint_accuracy = (float(self.tieerrEdt.text()))
        markEdtstr = self.markerrEdt.text()
#        print(markEdtstr)
        markEdtvec = markEdtstr.split("/")
#        print(markEdtvec)
#        print(len(markEdtvec))
        if markEdtvec == [""] or markEdtvec == [" "]:
            markEdtvec = chunk.marker_location_accuracy
        elif len(markEdtvec) == 1:
            markEdtvec = [float(markEdtstr), float(markEdtstr), float(markEdtstr)]
        elif len(markEdtvec) == 2:
            markEdtvec = [float(markEdtvec[0]), float(markEdtvec[0]), float(markEdtvec[1])]
        elif len(markEdtvec) == 3:
            markEdtvec = map(float, markEdtvec)
        elif len(markEdtvec) == 0:
            markEdtvec = chunk.marker_location_accuracy
        chunk.marker_location_accuracy = markEdtvec

#        focal_length = chunk.sensors[0].calibration.f    #each sensor has f, cx, cy, b1, b2, k1, k2, k3, k4, p1, p2, p3, p4
#would like to zero out unchecked parameters and then optimize but can't seem to set them.
#        for camera in chunk.sensors:
#            print (camera.calibration.b1)
#            camera.calibration.b1 = 0.0
#            print (camera.calibration.b1)
#            print (camera.fixed)

#        chunk.marker_location_accuracy = map(float, markEdtstr.split("/"))
#        chunk.optimizeCameras(fitf, fitc, fitaspect, fitskew, fitk, fitp, fitk4, fitp3, fitp4)
#optimizeCameras(fit_f=True, fit_cxcy=True, fit_b1=True, fit_b2=True, fit_k1k2k3=True, fit_p1p2=True, fit_k4=False, fit_p3=False, fit_p4=False[, progress ])
        chunk.optimizeCameras(fit_f=f_1, fit_cx=cx_1, fit_cy=cy_1, fit_b1=b1_1, fit_b2=b2_1, fit_k1=k1_1, fit_k2=k2_1, fit_k3=k3_1, fit_k4=k4_1, fit_p1=p1_1, fit_p2=p2_1, fit_corrections=additCor, tiepoint_covariance=True)

        for widget in self.widgets:
            widget.setDisabled(False)
        self.pBar.setMaximum(100)
        self.pBar.setValue(100)
        print("Script finished. Total optimization steps: " + str(stage))
#        print("Tie point estimate " + str(chunk.tiepoint_accuracy))
        Metashape.app.update()
        return 1


def optimizecamcal():
# Compatibility - Agisoft PhotoScan Professional 1.4.2
#optimize cameras: by default all camera coeffiients are checked
#additionally the Tie point accuracy can be changed to see the effect on the adjustment unit weight

    global doc
    doc = Metashape.app.document

    app = QtWidgets.QApplication.instance()
    parent = app.activeWindow()

    dlg = ProcDlgAllChecked(parent)


def removeblue():
#Removes blue markers - those markers placed automatically by PhotoScan
#Leaves green, refined, or pinned markers alone.

    doc = Metashape.app.document
    chunk = doc.chunk

    for marker in chunk.markers:
        for photo in list(marker.projections.keys()):
            if not marker.projections[photo].pinned:
                marker.projections[photo] = None
                print("Projection for "+marker.label + " removed on " + photo.label)

    print("Blue Marker Removal Script finished")

def renamemarkers():
#Renames markers to numbers only

#compatibility PhotoScan Pro 1.3


    doc = Metashape.app.document
    chunk = doc.chunk
    print("Rename markers script started...")

    processed = 0

    for marker in chunk.markers:
        oldmarker = marker.label
        if "target " == marker.label[0:7]:
            marker.label = marker.label[7:]
            marker.label = marker.label.replace (" ","")
            print(oldmarker + " is now " + marker.label)
            processed += 1
        if "point " == marker.label[0:6]:
            marker.label = marker.label[6:]
            marker.label = marker.label.replace (" ","")
            print(oldmarker + " is now " + marker.label)
            processed += 1



    if processed:
        print(str(processed) + " markers renamed")
    else:
        print("No matching markers")

    print("Rename markers finished")



#Calculate pooled horozontal error

def calculateHorizontalRMSE():

    global doc
    doc = Metashape.app.document
    proceed = Metashape.app.getBool("This tool calculateds RMSE in the units of the coorinate system.  If using WGS84/NAD83, then units are in meters.  Continue?")
    if proceed == True:

        import math
        chunk = Metashape.app.document.chunk
        
        checks = []
        control = []
        # tuple of epsg codes for geographic coordinates systems, to expand, add the values as strings
        gcs = ('4326','4269')
        for marker in chunk.markers:
            try:
                if chunk.crs.authority.split(":")[-1] in gcs: #make this check if using nad83/wgs84
                    #print('geog coord sys')    
                    #est = chunk.transform.matrix.mulp(marker.position)
                    #ref = chunk.crs.unproject(marker.reference.location)
                    source = chunk.crs.unproject(marker.reference.location) #measured values in geocentric coordinates
                    estim = chunk.transform.matrix.mulp(marker.position) #estimated coordinates in geocentric coordinates
                    local = chunk.crs.localframe(chunk.transform.matrix.mulp(marker.position)) #local LSE coordinates
                    error = local.mulv(estim - source)
                    xy_error = math.sqrt((error[0])**2 + (error[1])**2)
                    z_error = error[2]
                    t = (xy_error,z_error)
                else:
                    #print('proj coord sys')
                    est = chunk.crs.project(chunk.transform.matrix.mulp(marker.position))
                    ref = marker.reference.location
                    xy_error = math.sqrt((est[0] - ref[0])**2 + (est[1] - ref[1])**2)
                    #print(xy_error)
                    #x_error = est[0] - ref[0]
                    #y_error = est[1] - ref[1]
                    z_error = est[2] - ref[2]
                    t = (xy_error,z_error)
                if marker.reference.enabled:
                    control.append(t)
                    #print("control")
                else:
                    #print("check")
                    checks.append(t)
            except:
                pass
        #print(checks)
        #print("\n\n\n")
        #print(control)
            
        if len(control) > 0:
            xy_resid = 0.0
            z_resid = 0.0
            for i in control:
                xy_resid += i[0]**2
                z_resid += i[1]**2
            xy_rmse = math.sqrt(xy_resid/len(control))
            z_rmse = math.sqrt(z_resid/len(control))
            xy = "Control XY Error: {}".format(xy_rmse)
            z = "Control Z Error: {}".format(z_rmse)
            print(xy)
            print(z)
            
        if len(checks) > 0:
            xy_resid = 0.0
            z_resid = 0.0
            for i in checks:
                xy_resid += i[0]**2
                z_resid += i[1]**2
            xy_rmse = math.sqrt(xy_resid/len(checks))
            z_rmse = math.sqrt(z_resid/len(checks))
            xy = "Check Point XY Error: {}".format(xy_rmse)
            z = "Check Point Z Error: {}".format(z_rmse)
            print(xy)
            print(z)






#Implement Ernie's tool with a GUI
def geotag_photoscan1():

    global doc
    doc = Metashape.app.document
    proceed = Metashape.app.getBool("This tool exports image calculated positions from whatever chunk is active.  Continue?")
    if proceed == True:

        app = QtWidgets.QApplication.instance()
        parent = app.activeWindow()
        dlg = CreateTextFileDlg(parent)



#Use a get bool to ask if the working chunk is active and proceed?

#Define the UI and the process in the class below.
class CreateTextFileDlg(QtWidgets.QDialog):

    def __init__(self, parent):
        QtWidgets.QDialog.__init__(self, parent)
        self.setWindowTitle("Create text file with solved coordinates and keywords to update image EXIF")

        #FIRST, start with creating the text file by having them specify
        self.label1 = QtWidgets.QLabel()
        self.label1.setText("Specify output text file")
        self.outputFile = QtWidgets.QLineEdit()
        self.outputFile.setPlaceholderText('U:/Desktop/EXIFTags.txt')
        self.btnFile = QtWidgets.QPushButton("Browse")

        #Create a group to hold the choices
        self.securityChoice = QtWidgets.QComboBox()
        securityOptions = ["C-Confidential", "R-Restricted", "S-Secret","T-Top Secret", "U-Unclassified"]
        for i in securityOptions:
            self.securityChoice.addItem(i)
        self.securityChoice.setCurrentText("U-Unclassified")

        self.secLabel = QtWidgets.QLabel()
        self.secLabel.setText("Choose Image Security Classification.")

        #Add extra instructions
        self.label2 = QtWidgets.QLabel()
        self.label2.setText("\nIn the text boxes below, do not use special characters, eg :;()<> \n")

        #Add Project Name Widget
        self.projectName = QtWidgets.QLineEdit()
        #Add label
        self.projectNameLabel = QtWidgets.QLabel()
        self.projectNameLabel.setText("Project Name:")
        self.projectNameLabel.setAlignment(QtCore.Qt.AlignRight)


        #Add summary widget and label
        self.projectSummaryLabel = QtWidgets.QLabel()
        self.projectSummaryLabel.setText("Enter Project Summary Below")
        self.projectSummary = QtWidgets.QPlainTextEdit()
        self.projectSummary.setPlaceholderText("Enter project summary here!")

        #Add access and use constraints widget

        #Create a group to hold the choices
        self.accUseConst = QtWidgets.QComboBox()
        accUseOptions = ["None, public domain", "Non-BLM Data-Internal Use Only", "Non-BLM Data-Not for Distribution", "Generally Releasable", "Non-public, not for distribution", "Non-public, Internal, Autorized Persons", "Non-public draft data"]
        for i in accUseOptions:
            self.accUseConst.addItem(i)
        self.accUseConst.setCurrentText("None")
        self.accUseConst.setToolTip("Your choice from the list will autopopulate text from Standardized Disclaimer Statements for BLM Attachment 1-1")


        #Add label
        self.accUseConstLabel = QtWidgets.QLabel()
        self.accUseConstLabel.setText("Access and Use Constrains:")
        self.accUseConstLabel.setAlignment(QtCore.Qt.AlignRight)

        #Add Credits Widget
        self.creditsTxt = QtWidgets.QLineEdit()
        #Add label
        self.creditsLabel = QtWidgets.QLabel()
        self.creditsLabel.setText("Credits:")
        self.creditsLabel.setAlignment(QtCore.Qt.AlignRight)

        #Add keywords widget
        self.keyTxt = QtWidgets.QLineEdit()
        self.keyTxt.setPlaceholderText('e.g., Geospatial, Photogrammetry')
        #Add label
        self.keyLabel = QtWidgets.QLabel()
        self.keyLabel.setText("Keywords:")
        self.keyLabel.setAlignment(QtCore.Qt.AlignRight)



        #Create a start button to trigger functions when clicked
        self.btnStart = QtWidgets.QPushButton("Run")
        self.btnQuit= QtWidgets.QPushButton("Quit")


        layout = QtWidgets.QGridLayout()
        layout.addWidget(self.label1,0,0,5)
        layout.addWidget(self.outputFile,1,0,1,2)
        layout.addWidget(self.btnFile,1,2)


        layout.addWidget(self.secLabel,2,0)
        layout.addWidget(self.securityChoice,2,1,1,-1)
        layout.addWidget(self.label2,3,0,1,-1)
        layout.addWidget(self.projectNameLabel,4,0)
        layout.addWidget(self.projectName,4,1,1,-1)
        layout.addWidget(self.projectSummary,11,0,2,3)

        layout.addWidget(self.accUseConstLabel,5,0)
        layout.addWidget(self.accUseConst,5,1,1,-1)
        layout.addWidget(self.creditsLabel,6,0)
        layout.addWidget(self.creditsTxt,6,1,1,-1)
        layout.addWidget(self.keyLabel,7,0)
        layout.addWidget(self.keyTxt,7,1,1,-1)

        layout.addWidget(self.btnStart,20,0)
        layout.addWidget(self.btnQuit,20,1)

        self.setLayout(layout)

        proc_createTxt = lambda : self.createGeotagTxtFile()
        proc_chooseFile = lambda : self.chooseFileDialog()

        QtCore.QObject.connect(self.btnFile, QtCore.SIGNAL("clicked()"), proc_chooseFile)
        QtCore.QObject.connect(self.btnStart, QtCore.SIGNAL("clicked()"), self, QtCore.SLOT("accept()"))
        QtCore.QObject.connect(self.btnStart, QtCore.SIGNAL("clicked()"), proc_createTxt)
        QtCore.QObject.connect(self.btnQuit, QtCore.SIGNAL("clicked()"), self, QtCore.SLOT("reject()"))


        self.exec()

#Define the function to choose file name
    def chooseFileDialog(self):
        filename = QtWidgets.QFileDialog.getSaveFileName(parent=self, caption='Save File', dir='U:/Desktop', filter='TXT Files (*.txt)')
        if len(filename[0]) > 3:
            #print(filename)
            self.outputFile.setText(filename[0])
#Below is the regular process that should be implemented
    def createGeotagTxtFile(self):
        doc = Metashape.app.document
        chunk = doc.chunk


        if self.securityChoice.currentText() == "C-Confidential":
            Security = "S"
            print("Security: %s"%Security)
        elif self.securityChoice.currentText() == "R-Restricted":
            Security = "R"
            print("Security: %s"%Security)
        elif self.securityChoice.currentText() == "S-Secret":
            Security = "R"
            print("Security: %s"%Security)
        elif self.securityChoice.currentText() == "T-Top Secret":
            Security = "R"
            print("Security: %s"%Security)
        else:
            Security = "U"
            print("Security: %s"%Security)

        pos_file= self.outputFile.text()
        print(pos_file)
        outf = open(pos_file,'w')

        Prj_name = self.projectName.text()
        print("Project Name: %s" %Prj_name)
        Keyword = self.keyTxt.text()
        print("Keywords %s"%Keyword)

        if self.accUseConst.currentText() =="None, public domain":
            Usage_term = "None, these data are considered public domain."
            print(Usage_term)
        elif self.accUseConst.currentText() =="Non-BLM Data-Internal Use Only":
            Usage_term = "These data are available to internal Bureau of Land Management staff, contractors and partners. All other requests for this data will be referred to the source agency."
            print(Usage_term)
        elif self.accUseConst.currentText() =="Non-BLM Data-Not for Distribution":
            Usage_term = "These data are available to appropriate Bureau of Land Management staff, contractors, and partners. All other requests for this data will be referred to the source agency. This data might contain sensitive information and can be released by the source agency, subject to FOIA limitations."
            print(Usage_term)
        elif self.accUseConst.currentText() =="Generally Releasable":
            Usage_term = "Generally releasable. However, the data must be reviewed prior to release to assure that no protected data is contained within the dataset."
            print(Usage_term)
        elif self.accUseConst.currentText() =="Non-public, not for distribution":
            Usage_term = "Although these data might be available to internal Bureau of Land Management staff, contractors and partners, they should not be released. These data might contain sensitive information, and can only be accessed by the public through a FOIA request."
            print(Usage_term)
        elif self.accUseConst.currentText() =="Non-public, Internal, Autorized Persons":
            Usage_term = "These data might contain sensitive information, and may not be releasable under the Privacy Act. Access to these records is limited to AUTHORIZED PERSONS ONLY."
            print(Usage_term)
        else:
            Usage_term = "Unverified Dataset. These data will be restricted to internal BLM staff, contractors and partners directly involved with developing the associated planning documents. These data might contain sensitive information, and may only be accessed by the public by filing a FOIA request, which may or may not be granted depending on the applicable FOIA exemptions."
            print(Usage_term)


        print("Access and use constraints: %s" %Usage_term)

        Summary = self.projectSummary.toPlainText()
        Summary = Summary.replace("\r"," ")
        Summary = Summary.replace("\n"," ")
        Summary = Summary.replace("\t"," ")
        print("Summary: %s"%Summary)


        Credit = self.creditsTxt.text()


        outf.write("Project name: %s \n" % Prj_name) ### EXIF:UserComment
        outf.write("Summary: %s \n" % Summary) ### EXIF:ImageDescription
        outf.write("Keywords: %s \n" % Keyword) ### EXIF:UserComment
        outf.write("Access and Use Constrains: %s \n" % Usage_term) ### EXIF:Copyright
        outf.write("Security Classification: %s \n" % Security) ### EXIF:SecurityClassification
        outf.write("Credits: %s \n" % Credit) ### EXIF:Artist

        photos=chunk.cameras
        imgCount = 0
        extCount = 0
        naCount = 0
        for i in range(len(photos)):
            imgCount += 1
            new_crs=Metashape.CoordinateSystem("EPSG::4326")
            camera = photos[i]
            str_camera = str(camera)
            split_cam = str_camera.split(" ")
            cam_name = split_cam[-1].split(">")
            cam_name_new = cam_name[0].replace("'","")

            #Add The file extension if missing
            path = camera.frames[0].photo.path
            fileExt = path.split('.')[-1].lower()
            imgExt = cam_name_new.split('.')[-1]
            imgExt = imgExt.lower()
            if fileExt != imgExt:
                cam_name_new = cam_name_new + '.' + str(path.split('.')[-1])
                extCount += 1

            if camera.center is None:
                naCount += 1
            else:
                est_pos = new_crs.project(chunk.transform.matrix.mulp(camera.center))
                x_pos = round(est_pos[0],8)
                y_pos = round(est_pos[1],8)
                z_pos = round(est_pos[2],4)
                out_string = cam_name_new+' '+str(x_pos)+' '+str(y_pos)+' '+str(z_pos)+"\n"
                outf.write(out_string)

        outf.close()
        badChars = [':', ';', '(', ')', '<', '>']
        charWarn = False
        for i in badChars:
            if i in Summary:
                charWarn = True
            if i in Credit:
                charWarn = True
            if i in Keyword:
                charWarn = True
            if i in Prj_name:
                charWarn = True
        #Set up statement to handle three possible error messages
        if charWarn:
            #char warn == true
            if extCount > 0:
                #No warnings needed here
                if naCount > 0:
                    #char warn == true, extension count warning needed, and non-aligned warning needed
                    message = "Completed with 3 warnings: (1) Text fields contain special characters such as :;()<>.  (2) %s out of %s image labels were missing file extensions. These were automatically added, but check image names before running step 2.(3) Note that %s out of %s images were not aligned.  Step two deletes all images not included in the final product, including those not aligned.  Secure a copy of these non-aligned photos before proceeding to step two if you want to keep them." %(extCount,imgCount,naCount,imgCount)
                    Metashape.app.messageBox(textwrap.fill(message,65))
                else:
                    #Character and extension warning needed, but nothing needed about alingment
                    message = "Completed with 2 warnings:(1) Text fields contain special characters such as :;()<>.    (2) %s out of %s image labels were missing file extensions. These were automatically added, but check image names and remove special characters before running step 2." %(extCount,imgCount)
                    Metashape.app.messageBox(textwrap.fill(message,65))
            else:
                #char warn == true but ext warning not needed
                if naCount > 0:
                    #char warn == true, non-aligned warning needed, but extension count warning NOT needed,
                    message = "Completed with 2 warnings:(1) Text fields contain special characters such as :;()<>.(2) %s out of %s images were not aligned.  Step two deletes all images not included in the final product, including those not aligned.  Secure a copy of these non-aligned photos before proceeding to step two if you want to keep them." %(naCount,imgCount)
                    Metashape.app.messageBox(textwrap.fill(message,65))
                else:
                    #only character warning is needed
                    message = "WARNING: Text fields contain special characters such as :;()<>.  Please remove these from output text file before running step two."
                    Metashape.app.messageBox(textwrap.fill(message,65))

        else:
            #char warn == false
            if extCount > 0:
                #No message needed at this level
                if naCount > 0:
                    #extension count and non-aligned warnings needed
                    message = "Completed with 2 warnings: (1) %s out of %s image labels were missing file extensions. These were automatically added, but check image names before running step two.(2) Note that %s out of %s images were not aligned.  Step two deletes all images not included in the final product, including those not aligned.  Secure a copy of these non-aligned photos before proceeding to step two if you want to keep them." %(extCount,imgCount,naCount,imgCount)
                    Metashape.app.messageBox(textwrap.fill(message,65))
                else:
                    #Only Extension count warning is needed
                    message = "Note that %s out of %s image labels were missing file extensions.  These were added automatically, but please review output text file to ensure photo names and extensions look correct."%(extCount,imgCount)
                    Metashape.app.messageBox(textwrap.fill(message,65))
            else:
                #No message needed at this level
                if naCount > 0:
                    #non-aligned warning needed
                    message = "Note that %s out of %s images were not aligned.  Step two deletes all images not included in the final product, including those not aligned.  Secure a copy of these non-aligned photos before proceeding to step two if you want to keep them."%(naCount,imgCount)
                    Metashape.app.messageBox(textwrap.fill(message,65))
                else:
                    #No warnins, just say done!
                    Metashape.app.messageBox("Done")


def csic():
#splits the original chunk into multiple chunks with smaller bounding regions forming a grid
#building dense cloud, mesh and merging the result back is optional
#BE CAREFUL as all chunks might get merged - not just the ones created by the script

    global doc
    doc = Metashape.app.document

    app = QtWidgets.QApplication.instance()
    parent = app.activeWindow()

    doc = Metashape.app.document
    chunk = doc.chunk
    r_size = chunk.region.size
    if r_size.x > r_size.y:
        diffPer =round((r_size.x - r_size.y)/r_size.x*100,1)
        message = "Note: Region is %s percent larger in X dimension.  It is recommended you make more tiles in the X dimension (first column)." %diffPer
        Metashape.app.messageBox(textwrap.fill(message,65))
    else:
        diffPer =round((r_size.y - r_size.x)/r_size.y*100,1)
        message = "Note: Region is %s percent larger in Y dimension.  It is recommended you make more tiles in the Y dimension (second column)." %diffPer
        Metashape.app.messageBox(textwrap.fill(message,65))

    dlg = SplitDlg(parent)


class SplitDlg(QtWidgets.QDialog):

    def __init__(self, parent):

        QtWidgets.QDialog.__init__(self, parent)
        self.setWindowTitle("Tile Chunk for Processing")

        self.gridX = 2
        self.gridY = 2
        self.gridWidth = 198
        self.gridHeight = 198

        self.spinX = QtWidgets.QSpinBox()
        self.spinX.setMinimum(1)
        self.spinX.setMaximum(20)
        self.spinX.setValue(2)
        #self.spinX.setFixedSize(75, 25)
        self.spinY = QtWidgets.QSpinBox()
        self.spinY.setMinimum(1)
        self.spinY.setMaximum(20)
        self.spinY.setValue(2)
        #self.spinY.setFixedSize(75, 25)

        self.chkMesh = QtWidgets.QCheckBox("Build Mesh")
        #self.chkMesh.setFixedSize(100,50)
        self.chkMesh.setToolTip("Generates mesh for each cell in grid")

        self.chkDense = QtWidgets.QCheckBox("Build Dense Cloud")
        #self.chkDense.setFixedSize(120,50)
        self.chkDense.setWhatsThis("Builds dense cloud for each cell in grid")

        self.chkMerge = QtWidgets.QCheckBox("Merge Back")
        #self.chkMerge.setFixedSize(90,50)
        self.chkMerge.setToolTip("Merges back the processing products formed in the individual cells")

        self.chkSave = QtWidgets.QCheckBox("Autosave")
        #self.chkSave.setFixedSize(90,50)
        self.chkSave.setToolTip("Autosaves the project after each operation")

        self.txtOvp = QtWidgets.QLabel()
        self.txtOvp.setText("Tile overlap (%):")
        #self.txtOvp.setFixedSize(90, 25)

        self.edtOvp = QtWidgets.QLineEdit()
        self.edtOvp.setPlaceholderText("0")
        #self.edtOvp.setFixedSize(100, 25)

        #Add widget to process dense point cloud, should call separate class to add DPC optoins

        self.qualityChoice = QtWidgets.QComboBox()
        qualityOptions = ["Ultra High", "High","Medium", "Low", "Lowest"]
        for i in qualityOptions:
            self.qualityChoice.addItem(i)
        self.qualityChoice.setCurrentText("High")
        #Add label
        self.dpcLab = QtWidgets.QLabel()
        self.dpcLab.setText("Dense Point Cloud Quality")

        self.depthFilteringChoice = QtWidgets.QComboBox()
        filteringOptions = ["Disabled", "Mild","Moderate", "Aggressive"]
        for i in filteringOptions:
            self.depthFilteringChoice.addItem(i)
        self.depthFilteringChoice.setCurrentText("Aggressive")
        #Add label
        self.depthLab = QtWidgets.QLabel()
        self.depthLab.setText("Depth Filtering")

        #self.calcPointColors = QtWidgets.QCheckBox("Calculate point colors?")
        #self.calcPointColors.setChecked(True)




        #Add buttons for Mesh opttions
        #surface type
        self.surfaceType = QtWidgets.QComboBox()
        surfaceOptions = ["Arbitrary(3D)", "Height Field(2.5D)"]
        for i in surfaceOptions:
            self.surfaceType.addItem(i)
        self.surfaceType.setCurrentText("Height Field(2.5D)")
        #Add label
        self.meshLab = QtWidgets.QLabel()
        self.meshLab.setText("Surface type")

        #Face Count
        self.faceCount = QtWidgets.QSpinBox()
        self.faceCount.setMinimum(0)
        self.faceCount.setMaximum(1000000)
        self.faceCount.setValue(0)
        self.faceCount.setToolTip("A value of 0 represents sets no limit for faces, not recommended for large datasets.\n PS recommended values, Low-10,000 Medium-30,000 High-90,000")
        self.faceCountLab = QtWidgets.QLabel()
        self.faceCountLab.setText("Face Count")
        self.faceCountLab.setToolTip("A value of 0 represents sets no limit for faces, not recommended for large datasets.\n PS recommended values, Low-10,000 Medium-30,000 High-90,000")

        #Interpolation
        self.meshInterpolationChoice = QtWidgets.QComboBox()
        mInterpolationOptions = ["Enabled-default", "Extrapolated"]
        for i in mInterpolationOptions:
            self.meshInterpolationChoice.addItem(i)
        self.meshInterpolationChoice.setCurrentText("Enabled-default")
        #Add label
        self.interpolationLab = QtWidgets.QLabel()
        self.interpolationLab.setText("Interpolation")
        #Calculate vertex colors
        #self.calcVertexColors = QtWidgets.QCheckBox("Calculate vertex colors?")
        #self.calcVertexColors.setChecked(True)

        self.label = QtWidgets.QLabel()
        self.label.setText("WARNING! For the merge to work properly, \nplease first move your chunk to the bottom of \nthe workspace.  Otherwise it won't merge properly.")


        #Add buttons to start or cancel the process
        self.btnQuit = QtWidgets.QPushButton("Close")
        self.btnQuit.setFixedSize(90,50)

        self.btnP1 = QtWidgets.QPushButton("Run")
        self.btnP1.setFixedSize(90,50)

        self.grid = QtWidgets.QLabel(" ")
        self.grid.resize(self.gridWidth, self.gridHeight)
        tempPixmap = QtGui.QPixmap(self.gridWidth, self.gridHeight)
        tempImage = tempPixmap.toImage()

        for y in range(self.gridHeight):
            for x in range(self.gridWidth):

                if not (x and y) or (x == self.gridWidth - 1) or (y == self.gridHeight - 1):
                    tempImage.setPixel(x, y, QtGui.qRgb(0, 0, 0))
                elif (x == self.gridWidth / 2) or (y == self.gridHeight / 2):
                    tempImage.setPixel(x, y, QtGui.qRgb(0, 0, 0))

                else:
                    tempImage.setPixel(x, y, QtGui.qRgb(255, 255, 255))

        tempPixmap = tempPixmap.fromImage(tempImage)
        self.grid.setPixmap(tempPixmap)
        self.grid.show()

        layout = QtWidgets.QGridLayout()   #creating layout
        layout.addWidget(self.spinX, 0, 0)
        layout.addWidget(self.spinY, 0, 1)




        layout.addWidget(self.txtOvp, 4, 0)
        layout.addWidget(self.edtOvp, 4, 1)


        layout.addWidget(self.grid, 1, 0, 2, 2)

        layout.addWidget(self.chkDense, 5, 0)
        #layout.addWidget(self.calcPointColors,5,1)
        layout.addWidget(self.dpcLab,6,0)
        layout.addWidget(self.qualityChoice,6,1)
        layout.addWidget(self.depthLab,7,0)
        layout.addWidget(self.depthFilteringChoice,7,1)

        layout.addWidget(self.chkMesh, 8, 0)
        #layout.addWidget(self.calcVertexColors,8,1)
        layout.addWidget(self.meshLab,9,0)
        layout.addWidget(self.surfaceType,9,1)
        layout.addWidget(self.faceCountLab,10,0)
        layout.addWidget(self.faceCount,10,1)
        layout.addWidget(self.interpolationLab,11,0)
        layout.addWidget(self.meshInterpolationChoice,11,1)


        layout.addWidget(self.chkMerge, 12, 0)
        layout.addWidget(self.chkSave, 12, 1)
        layout.addWidget(self.label,13,0,2,2)
        layout.addWidget(self.btnP1, 15, 0)
        layout.addWidget(self.btnQuit, 15, 1)

        self.setLayout(layout)


    #Set which widgets should be invisible by default!
        self.qualityChoice.hide()
        self.dpcLab.hide()
        self.qualityChoice.hide()
        self.depthLab.hide()
        self.depthFilteringChoice.hide()
        #self.calcPointColors.hide()
        #self.calcVertexColors.hide()
        self.meshLab.hide()
        self.surfaceType.hide()
        self.faceCountLab.hide()
        self.faceCount.hide()
        self.interpolationLab.hide()
        self.meshInterpolationChoice.hide()
        self.chkMesh.hide()




        proc_split = lambda : self.splitChunks()
        proc_addDPC = lambda: self.addDPCOptions()
        proc_addMesh = lambda: self.addMeshOptions()

        self.spinX.valueChanged.connect(self.updateGrid)
        self.spinY.valueChanged.connect(self.updateGrid)

        self.chkDense.stateChanged.connect(proc_addDPC)
        self.chkMesh.stateChanged.connect(proc_addMesh)
        QtCore.QObject.connect(self.btnP1, QtCore.SIGNAL("clicked()"), self, QtCore.SLOT("accept()"))
        QtCore.QObject.connect(self.btnP1, QtCore.SIGNAL("clicked()"), proc_split)
        QtCore.QObject.connect(self.btnQuit, QtCore.SIGNAL("clicked()"), self, QtCore.SLOT("reject()"))

        self.exec()

    def updateGrid(self):
        """
        Draw new grid
        """

        self.gridX = self.spinX.value()
        self.gridY = self.spinY.value()

        tempPixmap = QtGui.QPixmap(self.gridWidth, self.gridHeight)
        tempImage = tempPixmap.toImage()
        tempImage.fill(QtGui.qRgb(240, 240, 240))

        for y in range(int(self.gridHeight / self.gridY) * self.gridY):
            for x in range(int(self.gridWidth / self.gridX) * self.gridX):
                if not (x and y) or (x == self.gridWidth - 1) or (y == self.gridHeight - 1):
                    tempImage.setPixel(x, y, QtGui.qRgb(0, 0, 0))
                elif y > int(self.gridHeight / self.gridY) * self.gridY:
                    tempImage.setPixel(x, y, QtGui.qRgb(240, 240, 240))
                elif x > int(self.gridWidth / self.gridX) * self.gridX:
                    tempImage.setPixel(x, y, QtGui.qRgb(240, 240, 240))
                else:
                    tempImage.setPixel(x, y, QtGui.qRgb(255, 255, 255))

        for y in range(0, int(self.gridHeight / self.gridY + 1) * self.gridY, int(self.gridHeight / self.gridY)):
            for x in range(int(self.gridWidth / self.gridX) * self.gridX):
                tempImage.setPixel(x, y, QtGui.qRgb(0, 0, 0))

        for x in range(0, int(self.gridWidth / self.gridX + 1) * self.gridX, int(self.gridWidth / self.gridX)):
            for y in range(int(self.gridHeight / self.gridY) * self.gridY):
                tempImage.setPixel(x, y, QtGui.qRgb(0, 0, 0))

        tempPixmap = tempPixmap.fromImage(tempImage)
        self.grid.setPixmap(tempPixmap)
        self.grid.show()

        return True
    def addDPCOptions(self):
        vis = self.chkDense.checkState()
        self.qualityChoice.setVisible(vis)
        self.dpcLab.setVisible(vis)
        self.qualityChoice.setVisible(vis)
        self.depthLab.setVisible(vis)
        self.depthFilteringChoice.setVisible(vis)
        #self.calcPointColors.setVisible(vis)
        self.chkMesh.setVisible(vis)
        if vis == False:
            self.meshLab.setVisible(vis)
            self.surfaceType.setVisible(vis)
            self.faceCountLab.setVisible(vis)
            self.faceCount.setVisible(vis)
            self.interpolationLab.setVisible(vis)
            self.meshInterpolationChoice.setVisible(vis)
            #self.calcVertexColors.setVisible(vis)
            self.chkMesh.setVisible(vis)
            self.chkMesh.setChecked(False)
    def addMeshOptions(self):
        vis2 = self.chkMesh.checkState()
        self.meshLab.setVisible(vis2)
        self.surfaceType.setVisible(vis2)
        self.faceCountLab.setVisible(vis2)
        self.faceCount.setVisible(vis2)
        self.interpolationLab.setVisible(vis2)
        self.meshInterpolationChoice.setVisible(vis2)
        #self.calcVertexColors.setVisible(vis2)

    def splitChunks(self):

        self.gridX = self.spinX.value()
        self.gridY = self.spinY.value()
        partsX = self.gridX
        partsY = self.gridY

        print("Script started")

        buildMesh = self.chkMesh.isChecked()
        buildDense = self.chkDense.isChecked()
        mergeBack = self.chkMerge.isChecked()
        autosave = self.chkSave.isChecked()

        doc = Metashape.app.document
        chunk = doc.chunk

        #get index of current chunk
        for i in range(0,len(doc.chunks)):
            if doc.chunks[i].label == chunk.label:
                chunkIndex = int(i)



        if not chunk.transform.translation:
            chunk.transform.matrix = chunk.transform.matrix

        region = chunk.region
        r_center = region.center
        r_rotate = region.rot
        r_size = region.size

        x_scale = r_size.x / partsX
        y_scale = r_size.y / partsY
        z_scale = r_size.z

        offset = r_center - r_rotate * r_size /2.

        for j in range(1, partsY + 1):  #creating new chunks and adjusting bounding box
            for i in range(1, partsX + 1):
                new_chunk = chunk.copy(items = [Metashape.DataSource.DenseCloudData])
                new_chunk.label = "Chunk "+ str(i)+ "\\" + str(j)
                new_chunk.model = None

                new_region = Metashape.Region()
                new_rot = r_rotate
                new_center = Metashape.Vector([(i - 0.5) * x_scale, (j - 0.5) * y_scale, 0.5 * z_scale])
                new_center = offset + new_rot * new_center
                new_size = Metashape.Vector([x_scale, y_scale, z_scale])

                if self.edtOvp.text().isdigit():
                    new_region.size = new_size * (1 + float(self.edtOvp.text()) / 100)
                else:
                    new_region.size = new_size

                new_region.center = new_center
                new_region.rot = new_rot

                new_chunk.region = new_region

                Metashape.app.update()

                if autosave:
                    doc.save()

                if buildDense:
                    print("Processing Dense point Cloud")
                    #dpcColors = self.calcPointColors.isChecked()
                    dpcColors = True
                    if self.qualityChoice.currentText() == "Ultra High":
                        dpcQuality = 1
                        print("Ultra DPC Quality")
                    elif self.qualityChoice.currentText() == "High":
                        dpcQuality = 2
                        print("High DPC Quality")
                    elif self.qualityChoice.currentText() == "Medium":
                        dpcQuality = 4
                        print("Medium DPC Quality")
                    elif self.qualityChoice.currentText() == "Low":
                        dpcQuality = 8
                        print("Low DPC Quality")
                    else:
                        dpcQuality = 16
                        print("Lowest DPC Quality")
                    #Filtering options
                    if self.depthFilteringChoice.currentText() == "Disabled":
                        depthFilt = Metashape.FilterMode.NoFiltering
                        print("Filtering Disabled")
                    elif self.depthFilteringChoice.currentText() == "Mild":
                        depthFilt = Metashape.FilterMode.MildFiltering
                        print("Mild Filtering")
                    elif self.depthFilteringChoice.currentText() == "Moderate":
                        depthFilt = Metashape.FilterMode.ModerateFiltering
                        print("Moderate Filtering")
                    else:
                        depthFilt = Metashape.FilterMode.AggressiveFiltering
                        print("Aggressive Filtering")


                    try:
                        new_chunk.buildDepthMaps(downscale = dpcQuality, filter_mode = depthFilt, reuse_depth = False)
                        new_chunk.buildDenseCloud(point_colors = dpcColors, point_confidence=True)
                    except RuntimeError:
                        print("Can't build dense cloud for " + chunk.label)

                    if autosave:
                        doc.save()

                    #Now build a mesh if chosen
                    if buildMesh:
                        meshFaceCount = int(self.faceCount.value())
                        if self.meshInterpolationChoice.currentText() == "Enabled-default":
                            interp = Metashape.Interpolation.EnabledInterpolation
                        else:
                            interp = Metashape.Interpolation.Extrapolated
                        #vertexColors = self.calcVertexColors.isChecked()
                        vertexColors = True
                        if self.surfaceType.currentText == "Arbitrary(3D)":
                            surfType = Metashape.SurfaceType.Arbitrary
                        else:
                            surfType = Metashape.SurfaceType.HeightField

                        try:
                            new_chunk.buildModel(surface_type = surfType, interpolation = interp, face_count_custom = meshFaceCount, source_data = Metashape.DataSource.DenseCloudData)
                        except RuntimeError:
                            print("Can't build mesh for " + chunk.label)

                        if autosave:
                            doc.save()


        if mergeBack:
            chunkList=[]
            #If merging back together, remove cameras from all except one chunk so that there aren't duplicates
            for i in range(chunkIndex+1, len(doc.chunks)):
                chunkList.append(doc.chunks[i].key)
                chunk = doc.chunks[i]
                if i > chunkIndex+1:
                    chunk.remove(chunk.cameras)
            print(chunkList)
            #doc.chunks[0].model = None #removing model from original chunk, just for case
            if buildDense == True and buildMesh == False:
                doc.mergeChunks(chunks=chunkList, merge_dense_clouds = True, merge_models = False, merge_markers = True) #merging all smaller chunks into single one
            else:
                doc.mergeChunks(chunks=chunkList, merge_dense_clouds = True, merge_models = True, merge_markers = True)

            doc.remove(doc.chunks[chunkIndex+1:-1]) #removing smaller chunks.
            if autosave:
                doc.save()

        if autosave:
            doc.save()

        print("Script finished")
        return True


def bbtocs():
#rotates chunks' bounding region in accordance of coordinate system for active chunk
#bounding cube size is kept
#compatibility: Agisoft PhotoScan Professional 1.3.

#import PhotoScan
#import math

        global doc
        doc = Metashape.app.document
        chunk = doc.chunk

        T = chunk.transform.matrix

        v_t = T * Metashape.Vector( [0,0,0,1] )
        v_t.size = 3

        if chunk.crs:
                m = chunk.crs.localframe(v_t)
        else:
                m = Metashape.Matrix().diag([1,1,1,1])

        m = m * T

        s = math.sqrt(m[0,0] ** 2 + m[0,1] ** 2 + m[0,2] ** 2) #scale factor

        R = Metashape.Matrix( [[m[0,0],m[0,1],m[0,2]], [m[1,0],m[1,1],m[1,2]], [m[2,0],m[2,1],m[2,2]]])

        R = R * (1. / s)

        reg = chunk.region
        reg.rot = R.t()
        chunk.region = reg

def cstobb():
#rotates model coordinate system in accordance of bounding region for active chunk
#scale is kept
#compatibility: Agisoft PhotoScan Professional 1.3.

#import PhotoScan
#import math

        doc = Metashape.app.document
        chunk = doc.chunk

        R = chunk.region.rot        #Bounding region rotation matrix
        C = chunk.region.center        #Bounding region center vector

        if chunk.transform.matrix:
                T = chunk.transform.matrix
                s = math.sqrt(T[0,0] ** 2 + T[0,1] ** 2 + T[0,2] ** 2)         #scaling
                S = Metashape.Matrix( [[s, 0, 0, 0], [0, s, 0, 0], [0, 0, s, 0], [0, 0, 0, 1]] ) #scale matrix
        else:
                S = Metashape.Matrix( [[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]] )

        T = Metashape.Matrix( [[R[0,0], R[0,1], R[0,2], C[0]], [R[1,0], R[1,1], R[1,2], C[1]], [R[2,0], R[2,1], R[2,2], C[2]], [0, 0, 0, 1]])

        chunk.transform.matrix = S * T.inv()        #resulting chunk transformation matrix


def add_altitude():
    """
    Adds user-defined altitude for camera instances in the Reference pane
    """

    doc = Metashape.app.document
    if not len(doc.chunks):
        raise Exception("No chunks!")

    alt = Metashape.app.getFloat("Please specify the height to be added:", 100)

    print("Script started...")
    chunk = doc.chunk

    for camera in chunk.cameras:
        if camera.reference.location:
            coord = camera.reference.location
            camera.reference.location = Metashape.Vector([coord.x, coord.y, coord.z + alt])

    print("Script finished!")

def organizeCamGroups():
    chunk = Metashape.app.document.chunk

    #First go through and disable ALL cameras
    #for camera in chunk.cameras:
    #    camera.enabled = False

    #Next read the CSV and use the list of photos to enable thsoe for the project
    #txtFile = r"E:\CO67CCPC\AERIAL_COMBIN_423620.txt"
    txtFile = Metashape.app.getOpenFileName("Choose textfile from EROS with 'Acquisition Date' field")
    with open(txtFile) as f:
        content = f.read().splitlines()

    #Grab the headers first
    headers = content[0].split("\t")
    print(headers)
    for i in range(len(headers)):
        if headers[i] == 'Acquisition Date':
            dateIndex = i
        if headers[i] == 'Photo ID':
            photoIndex = i


    #Use index 1 to drop the header, though it really doesn't matter
    photoNames = content[1:]
    dateList=[]
    photoDic = {}
    for i in photoNames:
        #print(i)
        #print(i.split("\t")[1])
        if i.split("\t")[dateIndex] not in dateList:
            dateList.append(i.split("\t")[dateIndex])
        photoDic[i.split("\t")[photoIndex]] = i.split("\t")[dateIndex]

    print(dateList)

    for i in dateList:
        g = chunk.addCameraGroup()
        g.label = i

    ###Using the list of photo names, iterate through the chunk
    for camera in chunk.cameras:
        for j in photoDic.keys():
            if j.lower() in camera.label.lower():
                lab = j
        for i in chunk.camera_groups:
            #print(i.label)
            #print(camera.label)
            if i.label==photoDic[lab]:
                camera.group = i
        print("Script finished")


def organizeCalGroups():
    # Organize camera cal groups to reflect camera groups in table of contents.

    chunk = Metashape.app.document.chunk
    proceed = Metashape.app.getBool("WARNING: This tools will make changes to camera calibraiton groups and is not recommended if processing has already been started.  Continue?")
    film = Metashape.app.getBool("Are you working with aerial film with fiducials?  Note, if yes is chosen all calibration groups will be designated as film with fiducials.")
    if proceed:
        for camera in chunk.cameras:
            # Create a list of existing sensors
            sensorList = chunk.sensors
            d ={}
            for i in sensorList:
                d[i.label] = i
            # Get camera group label and see if there is already a camera group with that name; make group without name when cameras aren't in folders
            a = str(camera.group).split("'")
            if len(a)> 1:
                a = a[1]
            else:
                a = ' '
            # If the calibration group label is not in the dicionatry, d, then create a ne calib group
            if a not in d:
                sensor = chunk.addSensor()
                sensor.label = a
                sensor.type = camera.sensor.type
                if film:
                    sensor.film_camera = True
                else:
                    sensor.calibration = camera.sensor.calibration
                    sensor.width = camera.sensor.width
                    sensor.height = camera.sensor.height
                    sensor.focal_length = camera.sensor.focal_length
                    sensor.pixel_height = camera.sensor.pixel_height
                    sensor.pixel_width = camera.sensor.pixel_width
                camera.sensor = sensor
            else:
                sensor = d[a]
                camera.sensor = sensor

        del sensorList
        del d
        print("Script complete!")
        
        
def outputImageQuality():
    # Compatibility - Agisoft PhotoScan Professional 1.5 or 1.6
    # Estimates Image quality and saves to csv file
    
    # export format:
    # label, quality 
    
    import Metashape as PhotoScan
    import time
    
    print("Estimating image quality and export to CSV file") 		
    doc = PhotoScan.app.document
    chunk = doc.chunk
    
    path = PhotoScan.app.getSaveFileName("Specify export path and filename:", filter = "CSV file (*.csv);;All formats (*.*)")
    
    file = open(path, "wt")
    print("Script started")
    
    t0 = time.time()
    
    file.write(",".join(["Label","Quality\n"]))
    
    cameras = chunk.cameras
    cameras = [camera for camera in cameras
                        if camera.type != Metashape.Camera.Type.Keyframe]
    
    camerasniq = [camera for camera in cameras
                        if 'Image/Quality' not in camera.meta]
    
    if len(camerasniq) > 0:
    	chunk.analyzePhotos(camerasniq)
    	
	
    for camera in cameras:
    	
    	quality = float(camera.meta['Image/Quality'])
            	
    	file.write("{},{:.3f}\n".format(camera.label, quality))
    
    
    t1 = time.time()
    
    file.flush()
    file.close()
    print("Script finished in " + str(int(t1-t0)) + " seconds.")


def footprints():

    global doc
    doc = Metashape.app.document
    chunk = doc.chunk
    app = QtWidgets.QApplication.instance()
    parent = app.activeWindow()
    dlg = CreateCSVFileDlg(parent)

#Define the UI and the process in the class below.
class CreateCSVFileDlg(QtWidgets.QDialog):

    def __init__(self, parent):
        QtWidgets.QDialog.__init__(self, parent)
        self.setWindowTitle("Create image footprint shapes and spreadsheet")


        #FIRST, start with creating the text file by having them specify
        self.label1 = QtWidgets.QLabel()
        self.label1.setText("Specify output CSV file")
        self.outputFile = QtWidgets.QLineEdit()
        self.outputFile.setPlaceholderText('U:/Desktop/FootprintCoordinates.csv')
        self.btnFile = QtWidgets.QPushButton("Browse")


        #Create spreadsheet?
        self.erosSpreadsheet = QtWidgets.QCheckBox("Create Spreadsheet of Coordinates?")
        self.erosSpreadsheet.setChecked(True)

        #Ask about coordinate system and create box to hold choices
        self.crsChoice = QtWidgets.QComboBox()
        crsOptions = ["WGS84", "Chunk CRS"]
        for i in crsOptions:
            self.crsChoice.addItem(i)
        self.crsChoice.setCurrentText("WGS84")

        self.crsLabel = QtWidgets.QLabel()
        self.crsLabel.setText("Coordinate System for Spreadsheet.")
        self.crsLabel.setToolTip("Note that if spreadsheet will be used to deliver footprint information to EROS, \nthey must be in WGS84")


        #If creating spreadsheet, export surface elevaiton at corners?
        self.exportCornerAlts = QtWidgets.QCheckBox("Include surface elevation of corner points in spreadsheet?")

        #If creating spreadsheet, export surface elevaiton at corners?
        self.createShapes = QtWidgets.QCheckBox("Create shapes layer of footprints?")

        #Create a start button to trigger functions when clicked
        self.btnStart = QtWidgets.QPushButton("Run")
        self.btnQuit= QtWidgets.QPushButton("Quit")

        #Add the widgets created above to the layout
        layout = QtWidgets.QGridLayout()
        layout.addWidget(self.erosSpreadsheet,0,0,1,-1)
        layout.addWidget(self.crsLabel,1,0,1,2)
        layout.addWidget(self.crsChoice,1,2)
        layout.addWidget(self.exportCornerAlts,2,0,1,-1)
        layout.addWidget(self.label1,3,0,1,-1)
        layout.addWidget(self.outputFile,4,0,1,2)
        layout.addWidget(self.btnFile,4,2)

        layout.addWidget(self.createShapes,5,0,1,-1)
        #layout.addWidget(self.label1,4,0,5)
        #layout.addWidget(self.csvOutputDirectory,6,0,2,3)


        layout.addWidget(self.btnStart,9,0)
        layout.addWidget(self.btnQuit,9,1)

        self.setLayout(layout)

        proc_createCSV = lambda : self.create_footprints()
        proc_toggle = lambda : self.toggleSpreadsheet()
        proc_chooseFile = lambda : self.chooseFileDialog()

        self.erosSpreadsheet.stateChanged.connect(proc_toggle)
        QtCore.QObject.connect(self.btnFile, QtCore.SIGNAL("clicked()"), proc_chooseFile)
        QtCore.QObject.connect(self.btnStart, QtCore.SIGNAL("clicked()"), self, QtCore.SLOT("accept()"))
        QtCore.QObject.connect(self.btnStart, QtCore.SIGNAL("clicked()"), proc_createCSV)
        QtCore.QObject.connect(self.btnQuit, QtCore.SIGNAL("clicked()"), self, QtCore.SLOT("reject()"))

        self.exec()

    def chooseFileDialog(self):
        filename = QtWidgets.QFileDialog.getSaveFileName(parent=self, caption='Save File', dir='U:/Desktop', filter='CSV Files (*.csv)')
        if len(filename[0]) > 3:
            self.outputFile.setText(filename[0])


    def toggleSpreadsheet(self):
        vis = self.erosSpreadsheet.checkState()
        self.crsLabel.setVisible(vis)
        self.crsChoice.setVisible(vis)
        self.exportCornerAlts.setVisible(vis)
        self.label1.setVisible(vis)
        self.btnFile.setVisible(vis)
        self.outputFile.setVisible(vis)
        #self.label1.setVisible(vis)
        #self.csvOutputDirectory.setVisible(vis)
        if vis == False:
             self.exportCornerAlts.setChecked(False)



    def create_footprints(self):
        """
        Creates four-vertex shape for each aligned camera (footprint) in the active chunk
        and puts all these shapes to a new separate shape layer
        """
        #Declare required Metashape variables and announce start of script
        doc = Metashape.app.document
        if not len(doc.chunks):
            raise Exception("No chunks!")

        print("Script started...")
        chunk = doc.chunk

        #Round up the user input
        erosSpreadsheet = self.erosSpreadsheet.isChecked()
        if erosSpreadsheet:
            erosSpreadsheet = True
            exportCornerAlts = self.exportCornerAlts.isChecked()
            if self.crsChoice.currentText() == "WGS84":
                outCRS=Metashape.CoordinateSystem("EPSG::4326")
            else:
                outCRS=chunk.crs
            cs = str(Metashape.CoordinateSystem("EPSG::4326"))
            if str(outCRS) == cs and str(chunk.crs) != cs:
                transform = True
            else:
                transform = False

            crsInput = self.crsChoice.currentText()
            outCSV = self.outputFile.text()
        createShapes = self.createShapes.isChecked()

        #Quit the script if there is not output selected
        if erosSpreadsheet == False and createShapes == False:
            raise Exception("No output selected! Script ending.")

        #Start the actual work fo the script
        if erosSpreadsheet:
            spreadsheetCoords = list()

        #If a spreadsheet is desired, check whether coordinates must be transformed
        if createShapes:
            if not chunk.shapes:
                chunk.shapes = Metashape.Shapes()
                chunk.shapes.crs = chunk.crs
        T = chunk.transform.matrix
        if createShapes:
            footprints = chunk.shapes.addGroup()
            footprints.label = "Footprints"
            footprints.color = (30, 239, 30)

        if chunk.model:
            surface = chunk.model
        elif chunk.dense_cloud:
            surface = chunk.dense_cloud
        else:
            surface = chunk.point_cloud

        for camera in chunk.cameras:
            if camera.type != Metashape.Camera.Type.Regular or not camera.transform:
                continue  # skipping NA cameras
            sensor = camera.sensor
            corners = list()
            if erosSpreadsheet:
                infoCoords = list()
                infoCoords.append(camera.label)
                est_pos = outCRS.project(chunk.transform.matrix.mulp(camera.center))
                infoCoords.append(round(est_pos[0],8))
                infoCoords.append(round(est_pos[1],8))
                infoCoords.append(round(est_pos[2],4))

            #Create a list of corner coordinates.  Removed dealing with the fiducials, just got the corners of the images.
            if sensor.film_camera:
                cornerPixCoords = [[0, 0], [int(camera.photo.meta['File/ImageWidth']) - 1, 0], [int(camera.photo.meta['File/ImageWidth']) - 1, int(camera.photo.meta['File/ImageHeight']) - 1], [0, int(camera.photo.meta['File/ImageHeight']) - 1]]
            else:
                cornerPixCoords = [[0, 0], [sensor.width - 1, 0], [sensor.width - 1, sensor.height - 1], [0, sensor.height - 1]]
            print(cornerPixCoords)
            #First line is the regular code.  Try the bottom one instead for
            #for i in [[0, 0], [width - 1, 0], [width - 1, height - 1], [0, height - 1]]:
            for i in cornerPixCoords:
                if sensor.film_camera:
                    corners.append(surface.pickPoint(camera.center, camera.unproject(Metashape.Vector(i))))
                else:
                    corners.append(surface.pickPoint(camera.center, camera.transform.mulp(sensor.calibration.unproject(Metashape.Vector(i)))))
                if not corners[-1]:
                    if sensor.film_camera:
                        corners[-1] = chunk.point_cloud.pickPoint(camera.center, camera.unproject(Metashape.Vector(i)))
                    else:
                        corners[-1] = chunk.point_cloud.pickPoint(camera.center, camera.transform.mulp(sensor.calibration.unproject(Metashape.Vector(i))))
                if not corners[-1]:
                    break
                if erosSpreadsheet:
                    if transform:
                        infoCoords.append(outCRS.project(T.mulp(corners[-1])))
                corners[-1] = chunk.crs.project(T.mulp(corners[-1]))
                if erosSpreadsheet == True and transform == False:
                    infoCoords.append(corners[-1])
            if erosSpreadsheet:
                spreadsheetCoords.append(infoCoords)

            if not all(corners):
                print("Skipping camera " + camera.label)
                continue

            if len(corners) == 4 and createShapes == True:
                shape = chunk.shapes.addShape()
                shape.label = camera.label
                shape.attributes["Photo"] = camera.label
                shape.type = Metashape.Shape.Type.Polygon
                shape.group = footprints
                shape.vertices = corners
                shape.has_z = True

        if erosSpreadsheet:
            outf = open(outCSV,'w')
            if exportCornerAlts:
                outf.write("Label,Center_Long,Center_Lat,Sensor_Elev,NE_Long,NE_Lat,NE_Elev,NW_Long,NW_Lat,NW_Elev,SW_Long,SW_Lat,SW_Elev,SE_Long,SE_Lat,SE_Elev\n")
            else:
                outf.write("Label,Center_Long,Center_Lat,Sensor_Elev,NE_Long,NE_Lat,NW_Long,NW_Lat,SW_Long,SW_Lat,SE_Long,SE_Lat\n")

            for i in range(len(spreadsheetCoords)-1):
                #First figure out which is NW, NE, SW, SE
                #Create Lat and Long dictionaries wherein coords are keys and coner ids are values
                nsDict = {}
                ewDict = {}
                coordNameDict = {'c1':spreadsheetCoords[i][4], 'c2':spreadsheetCoords[i][5], 'c3':spreadsheetCoords[i][6], 'c4':spreadsheetCoords[i][7]}
                latDict = {spreadsheetCoords[i][4][1]:'c1', spreadsheetCoords[i][5][1]:'c2', spreadsheetCoords[i][6][1]:'c3', spreadsheetCoords[i][7][1]:'c4'}
                latList = []
                for k in latDict:
                    latList.append(k)
                latList.sort()
                #Use the indices to assign NS direction
                nsDict[latDict[latList[0]]] = 'S'
                nsDict[latDict[latList[1]]] = 'S'
                nsDict[latDict[latList[2]]] = 'N'
                nsDict[latDict[latList[3]]] = 'N'
                longDict = {spreadsheetCoords[i][4][0]:'c1', spreadsheetCoords[i][5][0]:'c2', spreadsheetCoords[i][6][0]:'c3', spreadsheetCoords[i][7][0]:'c4'}
                longList = []
                for k in longDict:
                    longList.append(k)
                longList.sort()
                ewDict[longDict[longList[0]]] = 'W'
                ewDict[longDict[longList[1]]] = 'W'
                ewDict[longDict[longList[2]]] = 'E'
                ewDict[longDict[longList[3]]] = 'E'
                dirDict = {}
                for k in nsDict:
                    dirDict[k] = str(nsDict[k]) + str(ewDict[k])
                for k in dirDict:
                    if dirDict[k] == 'NW':
                        nw = coordNameDict[k]
                    elif dirDict[k] == 'NE':
                        ne = coordNameDict[k]
                    elif dirDict[k] == 'SW':
                        sw = coordNameDict[k]
                    else:
                        se = coordNameDict[k]
                if exportCornerAlts:
                    line = "%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s\n" %(spreadsheetCoords[i][0],spreadsheetCoords[i][1],spreadsheetCoords[i][2],spreadsheetCoords[i][3],ne[0],ne[1],ne[2],nw[0],nw[1],nw[2],sw[0],sw[1],sw[2],se[0],se[1],se[2])
                else:
                    line = "%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s\n" %(spreadsheetCoords[i][0],spreadsheetCoords[i][1],spreadsheetCoords[i][2],spreadsheetCoords[i][3],ne[0],ne[1],nw[0],nw[1],sw[0],sw[1],se[0],se[1])
                outf.write(line)
            outf.close()
        Metashape.app.update()
        print("Script finished!")
        Metashape.app.update()


#Add metashape tool to mask by color.
class MaskByColor(QtWidgets.QDialog):

    def __init__(self, parent):
        QtWidgets.QDialog.__init__(self, parent)

        self.color = QtGui.QColor(0, 0, 0)
        red, green, blue = self.color.red(), self.color.green(), self.color.blue()

        self.setWindowTitle("Masking by color:")

        #FIRST, start with creating the text file by having them specify
        self.label1 = QtWidgets.QLabel()
        self.label1.setText("\nSpecify directory for temporary files.  \n*Only required if preserving masks.")
        self.outputFile = QtWidgets.QLineEdit()
        self.outputFile.setPlaceholderText('c:/tmp')
        self.btnFile = QtWidgets.QPushButton("Browse")


        self.btnQuit = QtWidgets.QPushButton("Quit")
        self.btnQuit.setFixedSize(100, 50)

        self.btnP1 = QtWidgets.QPushButton("Mask")
        self.btnP1.setFixedSize(100, 50)

        self.pBar = QtWidgets.QProgressBar()
        self.pBar.setTextVisible(False)
        self.pBar.setFixedSize(130, 50)

        self.selTxt = QtWidgets.QLabel()
        self.selTxt.setText("Apply to:")
        self.selTxt.setFixedSize(100, 25)

        self.radioBtn_all = QtWidgets.QRadioButton("all cameras")
        self.radioBtn_sel = QtWidgets.QRadioButton("selected cameras")
        self.radioBtn_all.setChecked(True)
        self.radioBtn_sel.setChecked(False)

        self.preserveMasks = QtWidgets.QCheckBox("\nPreserve existing masks? \nUncheck to replace existing masks.")
        self.preserveMasks.setChecked(True)

        self.colTxt = QtWidgets.QLabel()
        self.colTxt.setText("Select color:")
        self.colTxt.setFixedSize(100, 25)

        strColor = "{:0>2d}{:0>2d}{:0>2d}".format(int(hex(red)[2:]), int(hex(green)[2:]), int(hex(blue)[2:]))
        self.btnCol = QtWidgets.QPushButton(strColor)
        self.btnCol.setFixedSize(80, 25)
        pix = QtGui.QPixmap(10, 10)
        pix.fill(self.color)
        icon = QtGui.QIcon()
        icon.addPixmap(pix)
        self.btnCol.setIcon(icon)
        palette = QtGui.QPalette()
        palette.setColor(QtGui.QPalette.Button, self.color)
        self.btnCol.setPalette(palette)
        self.btnCol.setAutoFillBackground(True)

        self.txtTol = QtWidgets.QLabel()
        self.txtTol.setText("Tolerance:")
        self.txtTol.setFixedSize(100, 25)

        self.sldTol = QtWidgets.QSlider()
        self.sldTol.setOrientation(QtCore.Qt.Orientation.Horizontal)
        self.sldTol.setMinimum(0)
        self.sldTol.setMaximum(99)
        self.sldTol.setValue(10)

        #hbox = QtWidgets.QHBoxLayout()
        #hbox.addStretch(1)
        #hbox.addWidget(self.pBar)
        #hbox.addWidget(self.btnP1)
        #hbox.addWidget(self.btnQuit)

        layout = QtWidgets.QGridLayout()
        layout.setSpacing(5)
        layout.addWidget(self.selTxt, 0, 0)
        layout.addWidget(self.radioBtn_all, 1, 0)
        layout.addWidget(self.radioBtn_sel, 2, 0)
        layout.addWidget(self.colTxt, 0, 1)
        layout.addWidget(self.btnCol, 1, 1)
        layout.addWidget(self.txtTol, 0, 2)
        layout.addWidget(self.sldTol, 1, 2)
        layout.addWidget(self.preserveMasks,4,0)
        layout.addWidget(self.label1,5,0,rowspan=-1)
        layout.addWidget(self.outputFile,6,0)
        layout.addWidget(self.btnFile,6,1)

        layout.addWidget(self.pBar,8,0)
        layout.addWidget(self.btnP1,8,1)
        layout.addWidget(self.btnQuit,8,2)



        #layout.addLayout(hbox, 8, 0, 5, 3)
        self.setLayout(layout)

        proc_mask = lambda: self.maskColor()
        proc_color = lambda: self.changeColor()
        proc_chooseFile = lambda : self.chooseFileDialog()

        QtCore.QObject.connect(self.btnFile, QtCore.SIGNAL("clicked()"), proc_chooseFile)
        QtCore.QObject.connect(self.btnP1, QtCore.SIGNAL("clicked()"), proc_mask)
        QtCore.QObject.connect(self.btnCol, QtCore.SIGNAL("clicked()"), proc_color)
        QtCore.QObject.connect(self.btnQuit, QtCore.SIGNAL("clicked()"), self, QtCore.SLOT("reject()"))

        self.exec()


    def chooseFileDialog(self):
        filename = QtWidgets.QFileDialog.getExistingDirectory(parent=self, caption='Directory for saving temporary files', dir='C:/tmp')
        if len(filename) > 1:
            #print(filename)
            self.outputFile.setText(filename)

    def changeColor(self):

        color = QtWidgets.QColorDialog.getColor()

        self.color = color
        red, green, blue = color.red(), color.green(), color.blue()
        if red < 16:
            red = "0" + hex(red)[2:]
        else:
            red = hex(red)[2:]
        if green < 16:
            green = "0" + hex(green)[2:]
        else:
            green = hex(green)[2:]
        if blue < 16:
            blue = "0" + hex(blue)[2:]
        else:
            blue = hex(blue)[2:]

        strColor = red + green + blue
        self.btnCol.setText(strColor)

        pix = QtGui.QPixmap(10, 10)
        pix.fill(self.color)
        icon = QtGui.QIcon()
        icon.addPixmap(pix)
        self.btnCol.setIcon(icon)

        palette = self.btnCol.palette()
        palette.setColor(QtGui.QPalette.Button, self.color)
        self.btnCol.setPalette(palette)
        self.btnCol.setAutoFillBackground(True)

        return True

    def maskColor(self):
        print("Masking...")

        tolerance = 10
        tolerance = self.sldTol.value()

        self.sldTol.setDisabled(True)
        self.btnCol.setDisabled(True)
        self.btnP1.setDisabled(True)
        self.btnQuit.setDisabled(True)

        presMasks = self.preserveMasks.isChecked()

        chunk = Metashape.app.document.chunk
        mask_list = list()
        if self.radioBtn_sel.isChecked():
            for camera in chunk.cameras:
                if camera.selected and camera.type == Metashape.Camera.Type.Regular:
                    mask_list.append(camera)
        elif self.radioBtn_all.isChecked():
            mask_list = [camera for camera in chunk.cameras if camera.type == Metashape.Camera.Type.Regular]

        if not len(mask_list):
            Metashape.app.messageBox("Nothing to mask!")
            return False

        color = self.color
        red, green, blue = color.red(), color.green(), color.blue()

        processed = 0
        iterMask = False
        tmpPath = self.outputFile.text()
        tmpMaskPath = tmpPath + "\\tmpMask.png"
        #If they're looking to preserve masks, make sure there is a path to save temp files
        if presMasks==True and tmpPath=='':
            print("Warning! Path for temporary files is required if preserving masks")
            self.sldTol.setDisabled(False)
            self.btnCol.setDisabled(False)
            self.btnP1.setDisabled(False)
            self.btnQuit.setDisabled(False)

            return


        for camera in mask_list:

            for frame in camera.frames:
                print(frame)
                clist = []
                clist.append(frame)
                app.processEvents()
                if frame.mask is not None:
                    if presMasks:
                        iterMask = True
                        tmpMask = frame.mask.image().save(tmpMaskPath)
                mask = Metashape.utils.createDifferenceMask(frame.photo.image(), (red, green, blue), tolerance, False)
                m = Metashape.Mask()
                m.setImage(mask)
                frame.mask = m
                if iterMask:
                    chunk.importMasks(path=tmpMaskPath,source=Metashape.MaskSourceFile,operation=Metashape.MaskOperationUnion, cameras=clist)
                iterMask = False
                processed += 1
                self.pBar.setValue(int(processed / len(mask_list) / len(chunk.frames) * 100))

        print("Masking finished. " + str(processed) + " images masked.")

        try:
            os.remove(tmpMaskPath)
        except:
            pass

        self.sldTol.setDisabled(False)
        self.btnCol.setDisabled(False)
        self.btnP1.setDisabled(False)
        self.btnQuit.setDisabled(False)

        return True


def mask_by_color():
    global doc
    doc = Metashape.app.document

    global app
    app = QtWidgets.QApplication.instance()
    parent = app.activeWindow()

    dlg = MaskByColor(parent)

def main():
 #adds custom menu item
        Metashape.app.addMenuItem("BLM NOC Tools/Automated Workflows/Align Images and Perform Initial Error Reduction", processRegularDataset)
        Metashape.app.addMenuItem("BLM NOC Tools/Automated Workflows/Align Images and Perform Initial ER for Historic Imagery", processHistoricDataset)
        Metashape.app.addMenuItem("BLM NOC Tools/Automated Workflows/Reprojection Error Reduction and optionally build products", erReprojectionError)
        Metashape.app.addMenuItem("BLM NOC Tools/Automated Workflows/Reconstruction Uncertainty and Projection Accuarcy Error Reduction", erReconProj)
        Metashape.app.addMenuItem("BLM NOC Tools/Adjust Region/Align Bounding Region to Coordinate System", bbtocs)
        Metashape.app.addMenuItem("BLM NOC Tools/Adjust Region/Get Coordinate System from Bounding Region", cstobb)
        Metashape.app.addMenuItem("BLM NOC Tools/Split chunk into smaller chunks for processing", csic)

        #PhotoScan.app.addMenuItem("Custom menu/Align Bounding Region to Coordinate System", bbtocs)
        #PhotoScan.app.addMenuItem("Custom menu/Get Coordinate System from Bounding Region", cstobb)
        Metashape.app.addMenuItem("BLM NOC Tools/Adjust Region/Copy current bounding region to all chunks", copybb)
        Metashape.app.addMenuItem("BLM NOC Tools/Organize Cameras/Split Photos into Camera Groups based on EE Text File", organizeCamGroups)
        Metashape.app.addMenuItem("BLM NOC Tools/Organize Cameras/Reorganize calibration groups to match workspace camera groups", organizeCalGroups)
        Metashape.app.addMenuItem("BLM NOC Tools/Adjust accuracy and optimize cameras", optimizecamcal)
        Metashape.app.addMenuItem("BLM NOC Tools/Remove Blue, unpinned marker(s)", removeblue)
        Metashape.app.addMenuItem("BLM NOC Tools/Rename markers to integers", renamemarkers)
        Metashape.app.addMenuItem("BLM NOC Tools/Add offset to camera elevations", add_altitude)
        Metashape.app.addMenuItem("BLM NOC Tools/Mask Images by Color", mask_by_color)
        Metashape.app.addMenuItem("BLM NOC Tools/Calculate Horizontal RMSE for Markers", calculateHorizontalRMSE)
        Metashape.app.addMenuItem("BLM NOC Tools/Estimate Image Quality and Save to CSV", outputImageQuality)
        Metashape.app.addMenuItem("BLM NOC Tools/Create shapes or spreadsheet of image footprints", footprints)
        Metashape.app.addMenuItem("BLM NOC Tools/Create text file with solved coordinates and keywords to update image EXIF", geotag_photoscan1)


        print("Custom BLM Toolbar Added")



main()
