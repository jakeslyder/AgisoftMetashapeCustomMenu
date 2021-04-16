#BLM NOC Tools custom menu assembled by Jake Slyder
#All scripts have been tested for compatability in version 1.4.2 and 1.4.4
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
import PhotoScan, pprint
import math, time, sys
from PySide2 import QtGui, QtCore, QtWidgets
import textwrap

def processRegularDataset():
#Goes through the regular procesing workflow, from image alignment through error reduction (on Reconstruction Uncertainty
# and projection accuracy) through to the point where you'd need to enter control.  Optionally includes the ability to
# add detect markers option.


    global doc
    doc = PhotoScan.app.document
    proceed = PhotoScan.app.getBool("This tool is intended to run everything from image alignment to the point where you enter control, including reconstruction uncertanty and projection accuarcy error reduction.  It automatically starts on the active chunk and will save the open project.  \n \nContinue?")
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
        self.chkUseMask = QtWidgets.QCheckBox("Filter points by image masks?")
        self.chkUseMask.setToolTip("Only check if masks applied to input images.")

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



        layout = QtWidgets.QGridLayout()
        layout.addWidget(self.label1,0,0,5)
        layout.addWidget(self.accuracyChoice,1,0)
        layout.addWidget(self.chkGenPreSel,2,0)
        layout.addWidget(self.chkRefPreSel,2,1)
        layout.addWidget(self.chkUseMask,1,1)
        layout.addWidget(self.spinKeyLab,3,0)
        layout.addWidget(self.spinKey,3,1)
        layout.addWidget(self.spinTieLab,4,0)
        layout.addWidget(self.spinTie,4,1)
        layout.addWidget(self.label2,5,0,2,0)
        #Add camera equation parameter selection
        layout.addWidget(self.f,7,0)
        layout.addWidget(self.b1,7,1)
        layout.addWidget(self.c,8,0)
        layout.addWidget(self.b2,8,1)
        layout.addWidget(self.k1,9,0)
        layout.addWidget(self.p1,9,1)
        layout.addWidget(self.k2,10,0)
        layout.addWidget(self.p2,10,1)
        layout.addWidget(self.k3,11,0)
        layout.addWidget(self.p3,11,1)
        layout.addWidget(self.k4,12,0)
        layout.addWidget(self.p4,12,1)
        layout.addWidget(self.label3,14,0)
        layout.addWidget(self.reconUncSpn,15,1)
        layout.addWidget(self.spinReconLab,15,0)
        layout.addWidget(self.projAccSpn,16,1)
        layout.addWidget(self.spinProjLab,16,0)
        layout.addWidget(self.spinMaxIter,17,1)
        layout.addWidget(self.spinIterLab,17,0)
        layout.addWidget(self.label4,18,0,5,3)
        layout.addWidget(self.aggYes,25,0)
        layout.addWidget(self.label5,25,0)
        layout.addWidget(self.detectMarkersChk,28,0)
        layout.addWidget(self.markersInvertedChk,28,1)
        layout.addWidget(self.markersParityChk,28,2)
        layout.addWidget(self.detectMarkersChoice,29,0)
        layout.addWidget(self.tolLabel,29,1)
        layout.addWidget(self.markerTolSpin,29,2)
        #layout.addWidget(self.label5,30,0)
        layout.addWidget(self.btnStart,31,0)
        layout.addWidget(self.btnQuit,31,1)


        self.setLayout(layout)

        #By default, start with the detect markers optoins all being hidden
        self.markersInvertedChk.hide()
        self.markersParityChk.hide()
        self.detectMarkersChoice.hide()
        self.tolLabel.hide()
        self.markerTolSpin.hide()


        proc_output = lambda : self.processImagery()
        proc_detMark = lambda : self.addDetectMarkers()


        self.detectMarkersChk.stateChanged.connect(proc_detMark)
        QtCore.QObject.connect(self.btnStart, QtCore.SIGNAL("clicked()"), self, QtCore.SLOT("accept()"))
        QtCore.QObject.connect(self.btnStart, QtCore.SIGNAL("clicked()"), proc_output)
        QtCore.QObject.connect(self.btnQuit, QtCore.SIGNAL("clicked()"), self, QtCore.SLOT("reject()"))


        self.exec()

    def addDetectMarkers(self):
        vis = self.detectMarkersChk.checkState()
        self.markersInvertedChk.setVisible(vis)
        self.markersParityChk.setVisible(vis)
        self.detectMarkersChoice.setVisible(vis)
        self.tolLabel.setVisible(vis)
        self.markerTolSpin.setVisible(vis)

    def processImagery(self):
        #Get start time for calculating runtime
        startTime = time.time()
        #Round up the user input into a more reasonable framework
        if self.accuracyChoice.currentText() == "Highest Accuracy":
            acc = PhotoScan.HighestAccuracy
            print("Highest Accuracy")
        elif self.accuracyChoice.currentText() == "High Accuracy":
            acc = PhotoScan.HighAccuracy
            print("High Accuracy")
        elif self.accuracyChoice.currentText() == "Medium Accuracy":
            acc = PhotoScan.MediumAccuracy
            print("Medium Accuracy")
        elif self.accuracyChoice.currentText() == "Low Accuracy":
            acc = PhotoScan.LowAccuracy
            print("Low Accuracy")
        else:
            acc = PhotoScan.LowestAccuracy
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

        keyLimit = int(self.spinKey.value()) #Keypoint limit
        print("Keypoint limit %s" %keyLimit)
        tieLimit = int(self.spinTie.value()) #Tiepoint limit
        print("Tiepoint limit %s" %tieLimit)

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
        p3_1=self.p3.isChecked()
        if p3_1 == True:
            print("p3")
        p4_1=self.p4.isChecked()
        if p4_1 == True:
            print("p4")

        reconThreshold = float(self.reconUncSpn.value())
        print("Reconstruction uncertainty %s" %reconThreshold)
        projThreshold = float(self.projAccSpn.value())
        print("Projection Accuracy %s" %projThreshold)
        maxIter = int(self.spinMaxIter.value())
        print("Maximum nubmer of iterations: %s" %maxIter)

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
                markerType = PhotoScan.TargetType.CrossTarget
                print("Using Cross target")
            elif self.detectMarkersChoice.currentText() == 'Circular non-coded':
                markerType = PhotoScan.TargetType.CircularTarget
                print("Using Uncoded circle target")
            elif self.detectMarkersChoice.currentText() == 'Circular 12 bit':
                markerType = PhotoScan.TargetType.CircularTarget12bit
                print("Using 12b circ target")
            elif self.detectMarkersChoice.currentText() == 'Circular 14 bit':
                markerType = PhotoScan.TargetType.CircularTarget14bit
                print("Using 14b circ target")
            elif self.detectMarkersChoice.currentText() == 'Circular 16 bit':
                markerType = PhotoScan.TargetType.CircularTarget16bit
                print("Using 16b circ target")
            elif self.detectMarkersChoice.currentText() == 'Circular 20 bit':
                markerType = PhotoScan.TargetType.CircularTarget20bit
                print("Using 20b circ target")


        #Run the script

        #Define a doc item and then open a project with that item.
        #Must start with one chunk where the camera groups are set
        doc = PhotoScan.app.document
        chunk = doc.chunk
        if chunk.label == "Chunk 1":
            chunk.label = "Align Photos"

        #Run the match and alignment, then optimize at the end using the initial parameters
        chunk.matchPhotos(accuracy = acc,generic_preselection=genPreSel,reference_preselection=refPreSel,filter_mask=maskFilter,keypoint_limit=keyLimit, tiepoint_limit=tieLimit)
        print("Match Photos Successful!")
        chunk.alignCameras(adaptive_fitting=False)
        print("Align Photos Successful!")
        chunk.optimizeCameras(fit_f=f_1, fit_cx=cx_1, fit_cy=cy_1, fit_b1=b1_1, fit_b2=b2_1, fit_k1=k1_1, fit_k2=k2_1, fit_k3=k3_1, fit_k4=k4_1, fit_p1=p1_1, fit_p2=p2_1, fit_p3=p3_1, fit_p4=p4_1)
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
            f = PhotoScan.PointCloud.Filter()
            f.init(c2, criterion = PhotoScan.PointCloud.Filter.ReconstructionUncertainty)
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
                    c2.optimizeCameras(fit_f=f_1, fit_cx=cx_1, fit_cy=cy_1, fit_b1=b1_1, fit_b2=b2_1, fit_k1=k1_1, fit_k2=k2_1, fit_k3=k3_1, fit_k4=k4_1, fit_p1=p1_1, fit_p2=p2_1, fit_p3=p3_1, fit_p4=p4_1)
                    f = PhotoScan.PointCloud.Filter()
                    #For some reason, the program freeezes at the line below at certain values
                    f.init(c2, criterion = PhotoScan.PointCloud.Filter.ReconstructionUncertainty)
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
            f = PhotoScan.PointCloud.Filter()
            f.init(c2, criterion = PhotoScan.PointCloud.Filter.ReconstructionUncertainty)


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
                    c2.optimizeCameras(fit_f=f_1, fit_cx=cx_1, fit_cy=cy_1, fit_b1=b1_1, fit_b2=b2_1, fit_k1=k1_1, fit_k2=k2_1, fit_k3=k3_1, fit_k4=k4_1, fit_p1=p1_1, fit_p2=p2_1, fit_p3=p3_1, fit_p4=p4_1)
                    f = PhotoScan.PointCloud.Filter()
                    f.init(c2, criterion = PhotoScan.PointCloud.Filter.ReconstructionUncertainty)
                    count += 1

        elif aggressive == False:
            ## First address reconstruction uncertainty, aim to get a level of 10.
            ##First determine the starting level.  Start at 10 and increment up if necessary
            PntCnt = len(c2.point_cloud.points)
            print("Sparse cloud point count after first step: %s" %PntCnt)
            targetPntCnt = int(PntCnt/2)
            print("New Target Point Count: %s" %targetPntCnt)



            ## Initiate a filter, first for recon uncert at default level
            f = PhotoScan.PointCloud.Filter()
            f.init(c2, criterion = PhotoScan.PointCloud.Filter.ReconstructionUncertainty)
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
                c2.optimizeCameras(fit_f=f_1, fit_cx=cx_1, fit_cy=cy_1, fit_b1=b1_1, fit_b2=b2_1, fit_k1=k1_1, fit_k2=k2_1, fit_k3=k3_1, fit_k4=k4_1, fit_p1=p1_1, fit_p2=p2_1, fit_p3=p3_1, fit_p4=p4_1)
                ## This distn't help like I thoguht it might## f.resetSelection()
                f = PhotoScan.PointCloud.Filter()
                f.init(c2, criterion = PhotoScan.PointCloud.Filter.ReconstructionUncertainty)
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
        f.init(c2, criterion = PhotoScan.PointCloud.Filter.ProjectionAccuracy)
        f.selectPoints(projThreshold)
        nselected = len([p for p in c2.point_cloud.points if p.selected])
        ##Set up variable for while loop if raising threshold is necessary.  Can remove the points here sine this is Proj Acc is not an interative process
        solved = 0
        #Start an if else while loop to check on starting parameter
        if nselected <= targetPntCnt:
            c2.point_cloud.removeSelectedPoints()
            print("Projecion Accuracy Attained: %s" %projThreshold)
            c2.optimizeCameras(fit_f=f_1, fit_cx=cx_1, fit_cy=cy_1, fit_b1=b1_1, fit_b2=b2_1, fit_k1=k1_1, fit_k2=k2_1, fit_k3=k3_1, fit_k4=k4_1, fit_p1=p1_1, fit_p2=p2_1, fit_p3=p3_1, fit_p4=p4_1)
        else:
            while solved == 0:
                projThreshold += 0.5
                f.selectPoints(projThreshold)
                nselected = len([p for p in c2.point_cloud.points if p.selected])
                if nselected <= targetPntCnt:
                    c2.point_cloud.removeSelectedPoints()
                    print("Projecion Accuracy Attained:")
                    c2.optimizeCameras(fit_f=f_1, fit_cx=cx_1, fit_cy=cy_1, fit_b1=b1_1, fit_b2=b2_1, fit_k1=k1_1, fit_k2=k2_1, fit_k3=k3_1, fit_k4=k4_1, fit_p1=p1_1, fit_p2=p2_1, fit_p3=p3_1, fit_p4=p4_1)
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
            c2.detectMarkers(markerType,markersTolerance,markersInverted,markersDisableParity)
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
            PhotoScan.app.messageBox(textwrap.fill(message,65))

        endTime = time.time()
        processTime = str((endTime-startTime)/60)
        print("Script took %s minutes to run!" %processTime)
        print("Script complete!")



#Modified the regular processing workflow above with a few changes for historic imagery...
def processHistoricDataset():

    global doc
    doc = PhotoScan.app.document
    proceed = PhotoScan.app.getBool("This tool is intended to run everything from image alignment to the point where you enter control, including reconstruction uncertanty and projection accuarcy error reduction.  It automatically starts on the active chunk and will save the open project.  \n \nContinue?")
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
        self.fixCalibChk = QtWidgets.QCheckBox("Fix Calibration for Initial Alignment?")
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
        self.p3 = QtWidgets.QCheckBox("Fit p3")
        self.p4 = QtWidgets.QCheckBox("Fit p4")

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
        layout.addWidget(self.chkGenPreSel,2,0)
        layout.addWidget(self.chkRefPreSel,2,1)
        layout.addWidget(self.chkUseMask,1,1)
        #Add fix calibration on one line right here
        layout.addWidget(self.fixCalibChk,3,0)
        layout.addWidget(self.spinKeyLab,4,0)
        layout.addWidget(self.spinKey,4,1)
        layout.addWidget(self.spinTieLab,5,0)
        layout.addWidget(self.spinTie,5,1)
        layout.addWidget(self.label2,6,0,2,0)
        #Add camera equation parameter selection
        layout.addWidget(self.f,8,0)
        layout.addWidget(self.b1,8,1)
        layout.addWidget(self.c,9,0)
        layout.addWidget(self.b2,9,1)
        layout.addWidget(self.k1,10,0)
        layout.addWidget(self.p1,10,1)
        layout.addWidget(self.k2,11,0)
        layout.addWidget(self.p2,11,1)
        layout.addWidget(self.k3,12,0)
        layout.addWidget(self.p3,12,1)
        layout.addWidget(self.k4,13,0)
        layout.addWidget(self.p4,13,1)
        layout.addWidget(self.label3,14,0)
        layout.addWidget(self.reconUncSpn,15,1)
        layout.addWidget(self.spinReconLab,15,0)
        layout.addWidget(self.projAccSpn,16,1)
        layout.addWidget(self.spinProjLab,16,0)
        layout.addWidget(self.spinMaxIter,17,1)
        layout.addWidget(self.spinIterLab,17,0)
        layout.addWidget(self.label4,18,0,5,3)
        layout.addWidget(self.aggYes,24,0)
        layout.addWidget(self.btnStart,26,0)
        layout.addWidget(self.btnQuit,26,1)


        self.setLayout(layout)

        proc_hist = lambda : self.processHistImagery()


        QtCore.QObject.connect(self.btnStart, QtCore.SIGNAL("clicked()"), self, QtCore.SLOT("accept()"))
        QtCore.QObject.connect(self.btnStart, QtCore.SIGNAL("clicked()"), proc_hist)
        QtCore.QObject.connect(self.btnQuit, QtCore.SIGNAL("clicked()"), self, QtCore.SLOT("reject()"))


        self.exec()


    def processHistImagery(self):
        #Record start time to calculate process run time
        startTime = time.time()
        #Round up the user input into a more reasonable framework
        if self.accuracyChoice.currentText() == "Highest Accuracy":
            acc = PhotoScan.HighestAccuracy
            print("Highest Accuracy")
        elif self.accuracyChoice.currentText() == "High Accuracy":
            acc = PhotoScan.HighAccuracy
            print("High Accuracy")
        elif self.accuracyChoice.currentText() == "Medium Accuracy":
            acc = PhotoScan.MediumAccuracy
            print("Medium Accuracy")
        elif self.accuracyChoice.currentText() == "Low Accuracy":
            acc = PhotoScan.LowAccuracy
            print("Low Accuracy")
        else:
            acc = PhotoScan.LowestAccuracy
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


        fixCal = self.fixCalibChk.isChecked()


        keyLimit = int(self.spinKey.value()) #Keypoint limit
        print("Keypoint limit %s" %keyLimit)
        tieLimit = int(self.spinTie.value()) #Tiepoint limit
        print("Tiepoint limit %s" %tieLimit)

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
        p3_1=self.p3.isChecked()
        if p3_1 == True:
            print("p3")
        p4_1=self.p4.isChecked()
        if p4_1 == True:
            print("p4")

        reconThreshold = float(self.reconUncSpn.value())
        print("Reconstruction uncertainty %s" %reconThreshold)
        projThreshold = float(self.projAccSpn.value())
        print("Projection Accuracy %s" %projThreshold)
        maxIter = int(self.spinMaxIter.value())
        print("Maximum nubmer of iterations: %s" %maxIter)

        aggressive = self.aggYes.isChecked()
        if aggressive == True:
            print("Using aggressive error reduction")


        #Start running the actual process
        #Define a doc item and then open a project with that item.
        #Must start with one chunk where the camera groups are set
        doc = PhotoScan.app.document
        chunk = doc.chunk
        if chunk.label == "Chunk 1":
            chunk.label = "Align Photos"

        #Create a sensor variable to access sensor properties
        s = chunk.sensors
        #By default, make all calibrations fixed for initial alignment unless otherwise specified by user
        if fixCal == True:
            for i in s:
                i.fixed_calibration = True
            print("Set camera calibraitons to fixed for initial alginment!")


        #Run the match and alignment, then optimize at the end using the initial parameters
        chunk.matchPhotos(accuracy = acc,generic_preselection=genPreSel,reference_preselection=refPreSel,filter_mask=maskFilter,keypoint_limit=keyLimit, tiepoint_limit=tieLimit)
        print("Match Photos Successful!")
        chunk.alignCameras(adaptive_fitting=False)
        print("Align Photos Successful!")

        doc.save()

        #Dublicate the chunk, unfix the calibration, and optimzie with the given parameters
        c2 = chunk.copy()
        c2.label = "Unfix Calibration and Optimize Cameras"
        #update the sensor varaible to reflect this copied chunk
        s2 = c2.sensors
        for i in s2:
            i.fixed_calibration = False
        c2.optimizeCameras(fit_f=f_1, fit_cx=cx_1, fit_cy=cy_1, fit_b1=b1_1, fit_b2=b2_1, fit_k1=k1_1, fit_k2=k2_1, fit_k3=k3_1, fit_k4=k4_1, fit_p1=p1_1, fit_p2=p2_1, fit_p3=p3_1, fit_p4=p4_1)
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
            f = PhotoScan.PointCloud.Filter()
            f.init(c3, criterion = PhotoScan.PointCloud.Filter.ReconstructionUncertainty)
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
                    c3.optimizeCameras(fit_f=f_1, fit_cx=cx_1, fit_cy=cy_1, fit_b1=b1_1, fit_b2=b2_1, fit_k1=k1_1, fit_k2=k2_1, fit_k3=k3_1, fit_k4=k4_1, fit_p1=p1_1, fit_p2=p2_1, fit_p3=p3_1, fit_p4=p4_1)
                    f = PhotoScan.PointCloud.Filter()
                    #For some reason, the program freeezes at the line below at certain values
                    f.init(c3, criterion = PhotoScan.PointCloud.Filter.ReconstructionUncertainty)
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
            f = PhotoScan.PointCloud.Filter()
            f.init(c3, criterion = PhotoScan.PointCloud.Filter.ReconstructionUncertainty)


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
                    c3.optimizeCameras(fit_f=f_1, fit_cx=cx_1, fit_cy=cy_1, fit_b1=b1_1, fit_b2=b2_1, fit_k1=k1_1, fit_k2=k2_1, fit_k3=k3_1, fit_k4=k4_1, fit_p1=p1_1, fit_p2=p2_1, fit_p3=p3_1, fit_p4=p4_1)
                    f = PhotoScan.PointCloud.Filter()
                    f.init(c3, criterion = PhotoScan.PointCloud.Filter.ReconstructionUncertainty)
                    count += 1

        elif aggressive == False:
            # First address reconstruction uncertainty, aim to get a level of 10.
            #First determine the starting level.  Start at 10 and increment up if necessary
            PntCnt = len(c3.point_cloud.points)
            print("Sparse cloud point count after first step: %s" %PntCnt)
            targetPntCnt = int(PntCnt/2)
            print("New Target Point Count: %s" %targetPntCnt)



            # Initiate a filter, first for recon uncert at default level
            f = PhotoScan.PointCloud.Filter()
            f.init(c3, criterion = PhotoScan.PointCloud.Filter.ReconstructionUncertainty)
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
                c3.optimizeCameras(fit_f=f_1, fit_cx=cx_1, fit_cy=cy_1, fit_b1=b1_1, fit_b2=b2_1, fit_k1=k1_1, fit_k2=k2_1, fit_k3=k3_1, fit_k4=k4_1, fit_p1=p1_1, fit_p2=p2_1, fit_p3=p3_1, fit_p4=p4_1)
                ## This distn't help like I thoguht it might## f.resetSelection()
                f = PhotoScan.PointCloud.Filter()
                f.init(c3, criterion = PhotoScan.PointCloud.Filter.ReconstructionUncertainty)
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
        f.init(c4, criterion = PhotoScan.PointCloud.Filter.ProjectionAccuracy)
        f.selectPoints(projThreshold)
        nselected = len([p for p in c4.point_cloud.points if p.selected])
        #Set up variable for while loop if raising threshold is necessary.  Can remove the points here sine this is Proj Acc is not an interative process
        solved = 0
        #Start an if else while loop to check on starting parameter
        if nselected <= targetPntCnt:
            c4.point_cloud.removeSelectedPoints()
            print("Projecion Accuracy Attained: %s" %projThreshold)
            c4.optimizeCameras(fit_f=f_1, fit_cx=cx_1, fit_cy=cy_1, fit_b1=b1_1, fit_b2=b2_1, fit_k1=k1_1, fit_k2=k2_1, fit_k3=k3_1, fit_k4=k4_1, fit_p1=p1_1, fit_p2=p2_1, fit_p3=p3_1, fit_p4=p4_1)
        else:
            while solved == 0:
                projThreshold += 0.5
                f.selectPoints(projThreshold)
                nselected = len([p for p in c4.point_cloud.points if p.selected])
                if nselected <= targetPntCnt:
                    c4.point_cloud.removeSelectedPoints()
                    print("Projecion Accuracy Attained:")
                    c4.optimizeCameras(fit_f=f_1, fit_cx=cx_1, fit_cy=cy_1, fit_b1=b1_1, fit_b2=b2_1, fit_k1=k1_1, fit_k2=k2_1, fit_k3=k3_1, fit_k4=k4_1, fit_p1=p1_1, fit_p2=p2_1, fit_p3=p3_1, fit_p4=p4_1)
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
            PhotoScan.app.messageBox(textwrap.fill(message,65))

        print("Script complete!")









#Define the  tool and UI to Run just the recon uncertainty/proj acc error reduction.
def erReconProj():
    global doc
    doc = PhotoScan.app.document
    proceed = PhotoScan.app.getBool("This tool will perform error reduction for reconstruction uncertanty and projection accuarcy before adding control/scale.  Continue?")
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
        self.p3 = QtWidgets.QCheckBox("Fit p3")
        self.p4 = QtWidgets.QCheckBox("Fit p4")

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
        layout.addWidget(self.f,7,0)
        layout.addWidget(self.b1,7,1)
        layout.addWidget(self.c,8,0)
        layout.addWidget(self.b2,8,1)
        layout.addWidget(self.k1,9,0)
        layout.addWidget(self.p1,9,1)
        layout.addWidget(self.k2,10,0)
        layout.addWidget(self.p2,10,1)
        layout.addWidget(self.k3,11,0)
        layout.addWidget(self.p3,11,1)
        layout.addWidget(self.k4,12,0)
        layout.addWidget(self.p4,12,1)
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
        p3_1=self.p3.isChecked()
        if p3_1 == True:
            print("p3")
        p4_1=self.p4.isChecked()
        if p4_1 == True:
            print("p4")

        reconThreshold = float(self.reconUncSpn.value())
        print("Reconstruction uncertainty %s" %reconThreshold)
        projThreshold = float(self.projAccSpn.value())
        print("Projection Accuracy %s" %projThreshold)
        maxIter = int(self.spinMaxIter.value())
        print("Maximum nubmer of iterations: %s" %maxIter)

        aggressive = self.aggYes.isChecked()
        if aggressive == True:
            print("Using aggressive error reduction")

        chunk = PhotoScan.app.document.chunk # active chunk
        doc = PhotoScan.app.document
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
            f = PhotoScan.PointCloud.Filter()
            f.init(chunk, criterion = PhotoScan.PointCloud.Filter.ReconstructionUncertainty)
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
                    chunk.optimizeCameras(fit_f=f_1, fit_cx=cx_1, fit_cy=cy_1, fit_b1=b1_1, fit_b2=b2_1, fit_k1=k1_1, fit_k2=k2_1, fit_k3=k3_1, fit_k4=k4_1, fit_p1=p1_1, fit_p2=p2_1, fit_p3=p3_1, fit_p4=p4_1)
                    f = PhotoScan.PointCloud.Filter()
                    #For some reason, the program freeezes at the line below at certain values
                    f.init(chunk, criterion = PhotoScan.PointCloud.Filter.ReconstructionUncertainty)
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
            f = PhotoScan.PointCloud.Filter()
            f.init(chunk, criterion = PhotoScan.PointCloud.Filter.ReconstructionUncertainty)


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
                    chunk.optimizeCameras(fit_f=f_1, fit_cx=cx_1, fit_cy=cy_1, fit_b1=b1_1, fit_b2=b2_1, fit_k1=k1_1, fit_k2=k2_1, fit_k3=k3_1, fit_k4=k4_1, fit_p1=p1_1, fit_p2=p2_1, fit_p3=p3_1, fit_p4=p4_1)
                    f = PhotoScan.PointCloud.Filter()
                    f.init(chunk, criterion = PhotoScan.PointCloud.Filter.ReconstructionUncertainty)
                    count += 1

        elif aggressive == False:
            ## First address reconstruction uncertainty, aim to get a level of 10.
            ##First determine the starting level.  Start at 10 and increment up if necessary
            PntCnt = len(chunk.point_cloud.points)
            print("Sparse cloud point count after first step: %s" %PntCnt)
            targetPntCnt = int(PntCnt/2)
            print("New Target Point Count: %s" %targetPntCnt)



            ## Initiate a filter, first for recon uncert at default level
            f = PhotoScan.PointCloud.Filter()
            f.init(chunk, criterion = PhotoScan.PointCloud.Filter.ReconstructionUncertainty)
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
                chunk.optimizeCameras(fit_f=f_1, fit_cx=cx_1, fit_cy=cy_1, fit_b1=b1_1, fit_b2=b2_1, fit_k1=k1_1, fit_k2=k2_1, fit_k3=k3_1, fit_k4=k4_1, fit_p1=p1_1, fit_p2=p2_1, fit_p3=p3_1, fit_p4=p4_1)
                ## This distn't help like I thoguht it might## f.resetSelection()
                f = PhotoScan.PointCloud.Filter()
                f.init(chunk, criterion = PhotoScan.PointCloud.Filter.ReconstructionUncertainty)
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
        f.init(chunk, criterion = PhotoScan.PointCloud.Filter.ProjectionAccuracy)
        f.selectPoints(projThreshold)
        nselected = len([p for p in chunk.point_cloud.points if p.selected])
        ##Set up variable for while loop if raising threshold is necessary.  Can remove the points here sine this is Proj Acc is not an interative process
        solved = 0
        #Start an if else while loop to check on starting parameter
        if nselected <= targetPntCnt:
            chunk.point_cloud.removeSelectedPoints()
            print("Projecion Accuracy Attained: %s" %projThreshold)
            chunk.optimizeCameras(fit_f=f_1, fit_cx=cx_1, fit_cy=cy_1, fit_b1=b1_1, fit_b2=b2_1, fit_k1=k1_1, fit_k2=k2_1, fit_k3=k3_1, fit_k4=k4_1, fit_p1=p1_1, fit_p2=p2_1, fit_p3=p3_1, fit_p4=p4_1)
        else:
            while solved == 0:
                projThreshold += 0.5
                f.selectPoints(projThreshold)
                nselected = len([p for p in chunk.point_cloud.points if p.selected])
                if nselected <= targetPntCnt:
                    chunk.point_cloud.removeSelectedPoints()
                    print("Projecion Accuracy Attained:")
                    chunk.optimizeCameras(fit_f=f_1, fit_cx=cx_1, fit_cy=cy_1, fit_b1=b1_1, fit_b2=b2_1, fit_k1=k1_1, fit_k2=k2_1, fit_k3=k3_1, fit_k4=k4_1, fit_p1=p1_1, fit_p2=p2_1, fit_p3=p3_1, fit_p4=p4_1)
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
            PhotoScan.app.messageBox(textwrap.fill(message,65))

        print("Script complete!")


#Implement the process for running just reprojection error reduction
def erReprojectionError():
    global doc
    doc = PhotoScan.app.document
    proceed = PhotoScan.app.getBool("Make sure that you've adjusted GCP/Scale/Tie Point Accuracy.  This tool alters and saves the active chunk.  Continue?")
    if proceed == True:
        app = QtWidgets.QApplication.instance()
        parent = app.activeWindow()
        dlg = ReconUncDlg(parent)


class ReconUncDlg(QtWidgets.QDialog):

    def __init__(self, parent):
        QtWidgets.QDialog.__init__(self, parent)
        self.setWindowTitle("Reprojection Error Reduction and Product Creation")


        #Add a label in order to add some distance
        self.label2 = QtWidgets.QLabel()
        self.label2.setText("\n Choose the Model Parameters for Optimizing Cameras")

        #Add button to Fix calibraiton for initial alignment
        self.fixCalibChk = QtWidgets.QCheckBox("Fix Calibration for Initial Alignment?")
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
        self.p1.setChecked(True)
        self.p2 = QtWidgets.QCheckBox("Fit p2")
        self.p2.setChecked(True)
        self.p3 = QtWidgets.QCheckBox("Fit p3")
        self.p4 = QtWidgets.QCheckBox("Fit p4")

        #Add another label to get reconstruction uncertainty.
        self.label3 = QtWidgets.QLabel()
        self.label3.setText("\nTarget Error Reduction Values.")

        #Create widget for reprojection error
        self.reprojErrSpn = QtWidgets.QDoubleSpinBox()
        self.reprojErrSpn.setDecimals(1)
        self.reprojErrSpn.setValue(.3)
        self.reprojErrSpn.setRange(0.1,5.0)
        self.reprojErrSpn.setToolTip("WARNING: Photoscan periodically freezes and crashes with values less than 0.3")
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



        layout = QtWidgets.QGridLayout()

        layout.addWidget(self.label2,4,0,2,0)
        #Add camera equation parameter selection
        layout.addWidget(self.label3,0,0,2,0)
        layout.addWidget(self.reprojErrSpn,2,1)
        layout.addWidget(self.spinReprojLab,2,0)
        layout.addWidget(self.spinMaxIter,3,1)
        layout.addWidget(self.spinIterLab,3,0)
        layout.addWidget(self.f,6,0)
        layout.addWidget(self.b1,6,1)
        layout.addWidget(self.c,7,0)
        layout.addWidget(self.b2,7,1)
        layout.addWidget(self.k1,8,0)
        layout.addWidget(self.p1,8,1)
        layout.addWidget(self.k2,9,0)
        layout.addWidget(self.p2,9,1)
        layout.addWidget(self.k3,10,0)
        layout.addWidget(self.p3,10,1)
        layout.addWidget(self.k4,11,0)
        layout.addWidget(self.p4,11,1)
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

    def addOrthoOptions(self):
        vis3 = self.processOrtho.checkState()
        self.blendingChoice.setVisible(vis3)
        self.blendingLab.setVisible(vis3)
        self.fillHoles.setVisible(vis3)


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
        p3_1=self.p3.isChecked()
        if p3_1 == True:
            print("p3")
        p4_1=self.p4.isChecked()
        if p4_1 == True:
            print("p4")

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
                dpcQuality = PhotoScan.Quality.UltraQuality
                print("Ultra DPC Quality")
            elif self.qualityChoice.currentText() == "High":
                dpcQuality = PhotoScan.Quality.HighQuality
                print("High DPC Quality")
            elif self.qualityChoice.currentText() == "Medium":
                dpcQuality = PhotoScan.Quality.MediumQuality
                print("Medium DPC Quality")
            elif self.qualityChoice.currentText() == "Low":
                dpcQuality = PhotoScan.Quality.LowQuality
                print("Low DPC Quality")
            else:
                dpcQuality = PhotoScan.Quality.LowQuality
                print("Lowest DPC Quality")
            #Filtering options
            if self.depthFilteringChoice.currentText() == "Disabled":
                depthFilt = PhotoScan.FilterMode.NoFiltering
                print("Filtering Disabled")
            elif self.depthFilteringChoice.currentText() == "Mild":
                depthFilt = PhotoScan.FilterMode.MildFiltering
                print("Mild Filtering")
            elif self.depthFilteringChoice.currentText() == "Moderate":
                depthFilt = PhotoScan.FilterMode.ModerateFiltering
                print("Moderate Filtering")
            else:
                depthFilt = PhotoScan.FilterMode.AggressiveFiltering
                print("Aggressive Filtering")

        #Get the DEM stuff
        buildDEM = self.processDEM.isChecked()
        if buildDEM == True:
            if self.interpolationChoice.currentText() == "Enabled-default":
                interp = PhotoScan.Interpolation.EnabledInterpolation
                print("DEM Interpolation enabled")
            elif self.interpolationChoice.currentText() == "Disabled":
                interp = PhotoScan.Interpolation.DisapledInterpolation
                print("DEM Interpolation DISABLED")
            else:
                interp = PhotoScan.Interpolation.Extrapolated
                print("DEM Extrapolated")

        #Get the Ortho stuff
        buildOrtho = self.processOrtho.isChecked()
        if buildOrtho == True:
            fillOrthoHoles = self.fillHoles.isChecked()
            if self.blendingChoice.currentText() == "Mosaic-Default":
                blendMethod = PhotoScan.BlendingMode.MosaicBlending
                print("Mosaic Ortho Blending")
            elif self.blendingChoice.currentText() == "Disabled":
                blendMethod = PhotoScan.BlendingMode.DisabledBlending
                print("Ortho blending disabled")
            else:
                blendMethod = PhotoScan.BlendingMode.AverageBlending
                print("Average Ortho Blending")

        #Get the start time
        startTime = time.time()
        doc = PhotoScan.app.document
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
        chunk.optimizeCameras(fit_f=f_1, fit_cx=cx_1, fit_cy=cy_1, fit_b1=b1_1, fit_b2=b2_1, fit_k1=k1_1, fit_k2=k2_1, fit_k3=k3_1, fit_k4=k4_1, fit_p1=p1_1, fit_p2=p2_1, fit_p3=p3_1, fit_p4=p4_1)

        if minVal > startVal:
            startVal = minVal

        #Iniitate a filter for tie point gradual selection
        f = PhotoScan.PointCloud.Filter()
        f.init(chunk, criterion = PhotoScan.PointCloud.Filter.ReprojectionError)
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
                chunk.optimizeCameras(fit_f=f_1, fit_cx=cx_1, fit_cy=cy_1, fit_b1=b1_1, fit_b2=b2_1, fit_k1=k1_1, fit_k2=k2_1, fit_k3=k3_1, fit_k4=k4_1, fit_p1=p1_1, fit_p2=p2_1, fit_p3=p3_1, fit_p4=p4_1)
                #print("test1")
                f = PhotoScan.PointCloud.Filter()
                #print("test2")
                #For some reason, the program freeezes at the line below at certain values
                f.init(chunk, criterion = PhotoScan.PointCloud.Filter.ReprojectionError)
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
        f = PhotoScan.PointCloud.Filter()
        f.init(chunk, criterion = PhotoScan.PointCloud.Filter.ReprojectionError)


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
                chunk.optimizeCameras(fit_f=f_1, fit_cx=cx_1, fit_cy=cy_1, fit_b1=b1_1, fit_b2=b2_1, fit_k1=k1_1, fit_k2=k2_1, fit_k3=k3_1, fit_k4=k4_1, fit_p1=p1_1, fit_p2=p2_1, fit_p3=p3_1, fit_p4=p4_1)
                f = PhotoScan.PointCloud.Filter()
                f.init(chunk, criterion = PhotoScan.PointCloud.Filter.ReprojectionError)
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
            c2.buildDepthMaps(quality = dpcQuality, filter = depthFilt, reuse_depth = False)
            c2.buildDenseCloud(point_colors = dpcColors)
            doc.save()
            if buildDEM == True:
                c2.buildDem(source = PhotoScan.DataSource.DenseCloudData, interpolation = interp)
                doc.save()
                if buildOrtho == True:
                    c2.buildOrthomosaic(surface = PhotoScan.DataSource.ElevationData, blending = blendMethod, fill_holes = fillOrthoHoles)
                    doc.save()

        endTime = time.time()
        processTime = str((endTime-startTime)/60)
        print("Script took %s minutes to run!" %processTime)
        print("Script complete!")



def copybb():
#copy bounding region for active chunk to all other chunks in workspace
#compatibility: Checked it in PhotoScan 1.4.2 and it worked.

    doc = PhotoScan.app.document

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

        R = PhotoScan.Matrix( [[T[0,0],T[0,1],T[0,2]], [T[1,0],T[1,1],T[1,2]], [T[2,0],T[2,1],T[2,2]]])

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

        self.fitcxBox = QtWidgets.QCheckBox("Fit cx")
        self.fitcxBox.setFixedSize(150,50)
        self.fitcxBox.setChecked(1)
        self.fitcyBox = QtWidgets.QCheckBox("Fit cy")
        self.fitcyBox.setFixedSize(150,50)
        self.fitcyBox.setChecked(1)

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
        self.fitp3Box = QtWidgets.QCheckBox("Fit p3")
        self.fitp3Box.setFixedSize(150,50)
        self.fitp3Box.setChecked(1)
        self.fitp4Box = QtWidgets.QCheckBox("Fit p4")
        self.fitp4Box.setFixedSize(150,50)
        self.fitp4Box.setChecked(1)

        self.fitb1Box = QtWidgets.QCheckBox("Fit b1")
        self.fitb1Box.setFixedSize(150,50)
        self.fitb1Box.setChecked(1)

        self.fitb2Box = QtWidgets.QCheckBox("Fit b2")
        self.fitb2Box.setFixedSize(150,50)
        self.fitb2Box.setChecked(1)

        self.fitRSBox = QtWidgets.QCheckBox("Fit Rolling Shutter")
        self.fitRSBox.setFixedSize(150,50)
        self.fitRSBox.setChecked(0)

        layout = QtWidgets.QGridLayout()   #creating layout
        layout.setSpacing(1)
        layout.addWidget(self.tieerrTxt, 0, 0)
        layout.addWidget(self.tieerrEdt, 0, 1)

        layout.addWidget(self.markerrTxt, 1, 0)
        layout.addWidget(self.markerrEdt, 1, 1)

        layout.addWidget(self.fitfBox, 2, 0)
        layout.addWidget(self.fitcxBox, 3, 0)
        layout.addWidget(self.fitcyBox, 4, 0)
        layout.addWidget(self.fitk1Box, 5, 0)
        layout.addWidget(self.fitk2Box, 6, 0)
        layout.addWidget(self.fitk3Box, 7, 0)
        layout.addWidget(self.fitk4Box, 8, 0)
        layout.addWidget(self.fitb1Box, 2, 1)
        layout.addWidget(self.fitb2Box, 3, 1)
        layout.addWidget(self.fitp1Box, 4, 1)
        layout.addWidget(self.fitp2Box, 5, 1)
        layout.addWidget(self.fitp3Box, 6, 1)
        layout.addWidget(self.fitp4Box, 7, 1)
        layout.addWidget(self.fitRSBox, 8, 1)

        layout.addWidget(self.pBar, 4, 2)
        layout.addWidget(self.btnBP1, 3, 2)
        layout.addWidget(self.btnQuit, 0, 2)
        self.setLayout(layout)

#       self.widgets = [self.fitfBox, self.fitcBox, self.fitkBox, self.fitaspectBox, self.fitskewBox, self.fitpBox, self.fitk4Box, self.btnP1, self.btnQuit, self.errEdt, self.mnumEdt]
#        self.widgets = [self.fitfBox, self.fitcBox, self.fitkBox, self.fitaspectBox, self.fitskewBox, self.fitpBox, self.fitk4Box, self.fitp3p4Box, self.btnP1, self.btnQuit]
        self.widgets = [self.fitfBox, self.fitcxBox, self.fitcyBox, self.fitk1Box, self.fitk2Box, self.fitk3Box, self.fitk4Box, self.fitb1Box, self.fitb2Box, self.fitp1Box, self.fitp2Box, self.fitp3Box, self.fitp4Box, self.fitRSBox, self.btnBP1, self.btnQuit]

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

        fitf = self.fitfBox.isChecked()
        fitcx = self.fitcxBox.isChecked()
        fitcy = self.fitcyBox.isChecked()
        fitk1 = self.fitk1Box.isChecked()
        fitk2 = self.fitk2Box.isChecked()
        fitk3 = self.fitk3Box.isChecked()
        fitk4 = self.fitk4Box.isChecked()
        fitb1 = self.fitb1Box.isChecked()
        fitb2 = self.fitb2Box.isChecked()
        fitp1 = self.fitp1Box.isChecked()
        fitp2 = self.fitp2Box.isChecked()
        fitp3 = self.fitp3Box.isChecked()
        fitp4 = self.fitp4Box.isChecked()
        fitRS = self.fitRSBox.isChecked()

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
        chunk.optimizeCameras(fitf, fitcx, fitcy, fitb1, fitb2, fitk1, fitk2, fitk3, fitk4, fitp1, fitp2, fitp3, fitp4, fitRS)

        for widget in self.widgets:
            widget.setDisabled(False)
        self.pBar.setMaximum(100)
        self.pBar.setValue(100)
        print("Script finished. Total optimization steps: " + str(stage))
#        print("Tie point estimate " + str(chunk.tiepoint_accuracy))
        PhotoScan.app.update()
        return 1


def optimizecamcal():
# Compatibility - Agisoft PhotoScan Professional 1.4.2
#optimize cameras: by default all camera coeffiients are checked
#additionally the Tie point accuracy can be changed to see the effect on the adjustment unit weight

    global doc
    doc = PhotoScan.app.document

    app = QtWidgets.QApplication.instance()
    parent = app.activeWindow()

    dlg = ProcDlgAllChecked(parent)


def removeblue():
#Removes blue markers - those markers placed automatically by PhotoScan
#Leaves green, refined, or pinned markers alone.

    doc = PhotoScan.app.document
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


    doc = PhotoScan.app.document
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









#Implement Ernie's tool with a GUI
def geotag_photoscan1():

    global doc
    doc = PhotoScan.app.document
    proceed = PhotoScan.app.getBool("This tool exports image calculatoed positions from whatever chunk is active.  Please make that the final chunk is active and that non-aligned photos are removed.  Continue?")
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
        self.btnFile = QtWidgets.QPushButton("Save As")

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


        #Add summary widget
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
        doc = PhotoScan.app.document
        chunk = doc.chunk


        if self.securityChoice.currentText() == "C-Confidential":
            Security = "S"
            print("Security: %s"%Security)
        elif self.securityChoice.currentText() == "R-Restricted":
            Security = "R"
            pprint("Security: %s"%Security)
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
        for i in range(len(photos)):
            imgCount += 1
            new_crs=PhotoScan.CoordinateSystem("EPSG::4326")
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
                cam_name_new = cam_name_new + '.' + fileExt
                extCount += 1

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
        if charWarn == True and extCount > 0:
            message = "WARNING: Text fields contain special characters such as :;()<>.  Note also that %s out of %s image labels were missing file extensions. These were automatically added, but check image names and remove special characters before running step 2." %(extCount,imgCount)
            PhotoScan.app.messageBox(textwrap.fill(message,65))
        elif charWarn == True:
            message = "WARNING: Text fields contain special characters such as :;()<>.  Please remove these from output text file before running step two."
            PhotoScan.app.messageBox(textwrap.fill(message,65))
        elif extCount > 0:
            message = "Note that %s out of %s image labels were missing file extensions.  These were added automatically, but please review output text file to ensure photo names and extensions look correct."%(extCount,imgCount)
            PhotoScan.app.messageBox(textwrap.fill(message,65))
        else:
            PhotoScan.app.messageBox("Done")

def csic():
#splits the original chunk into multiple chunks with smaller bounding regions forming a grid
#building dense cloud, mesh and merging the result back is optional
#BE CAREFUL as all chunks might get merged - not just the ones created by the script

    global doc
    doc = PhotoScan.app.document

    app = QtWidgets.QApplication.instance()
    parent = app.activeWindow()

    doc = PhotoScan.app.document
    chunk = doc.chunk
    r_size = chunk.region.size
    if r_size.x > r_size.y:
        diffPer =round((r_size.x - r_size.y)/r_size.x*100,1)
        message = "Note: Region is %s percent larger in X dimension.  It is recommended you make more tiles in the X dimension (first column)." %diffPer
        PhotoScan.app.messageBox(textwrap.fill(message,65))
    else:
        diffPer =round((r_size.y - r_size.x)/r_size.y*100,1)
        message = "Note: Region is %s percent larger in Y dimension.  It is recommended you make more tiles in the Y dimension (second column)." %diffPer
        PhotoScan.app.messageBox(textwrap.fill(message,65))

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

        doc = PhotoScan.app.document
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
                new_chunk = chunk.copy(items = [PhotoScan.DataSource.DenseCloudData])
                new_chunk.label = "Chunk "+ str(i)+ "\\" + str(j)
                new_chunk.model = None

                new_region = PhotoScan.Region()
                new_rot = r_rotate
                new_center = PhotoScan.Vector([(i - 0.5) * x_scale, (j - 0.5) * y_scale, 0.5 * z_scale])
                new_center = offset + new_rot * new_center
                new_size = PhotoScan.Vector([x_scale, y_scale, z_scale])

                if self.edtOvp.text().isdigit():
                    new_region.size = new_size * (1 + float(self.edtOvp.text()) / 100)
                else:
                    new_region.size = new_size

                new_region.center = new_center
                new_region.rot = new_rot

                new_chunk.region = new_region

                PhotoScan.app.update()

                if autosave:
                    doc.save()

                if buildDense:
                    print("Processing Dense point Cloud")
                    #dpcColors = self.calcPointColors.isChecked()
                    dpcColors = True
                    if self.qualityChoice.currentText() == "Ultra High":
                        dpcQuality = PhotoScan.Quality.UltraQuality
                        print("Ultra DPC Quality")
                    elif self.qualityChoice.currentText() == "High":
                        dpcQuality = PhotoScan.Quality.HighQuality
                        print("High DPC Quality")
                    elif self.qualityChoice.currentText() == "Medium":
                        dpcQuality = PhotoScan.Quality.MediumQuality
                        print("Medium DPC Quality")
                    elif self.qualityChoice.currentText() == "Low":
                        dpcQuality = PhotoScan.Quality.LowQuality
                        print("Low DPC Quality")
                    else:
                        dpcQuality = PhotoScan.Quality.LowQuality
                        print("Lowest DPC Quality")
                    #Filtering options
                    if self.depthFilteringChoice.currentText() == "Disabled":
                        depthFilt = PhotoScan.FilterMode.NoFiltering
                        print("Filtering Disabled")
                    elif self.depthFilteringChoice.currentText() == "Mild":
                        depthFilt = PhotoScan.FilterMode.MildFiltering
                        print("Mild Filtering")
                    elif self.depthFilteringChoice.currentText() == "Moderate":
                        depthFilt = PhotoScan.FilterMode.ModerateFiltering
                        print("Moderate Filtering")
                    else:
                        depthFilt = PhotoScan.FilterMode.AggressiveFiltering
                        print("Aggressive Filtering")


                    try:
                        new_chunk.buildDepthMaps(quality = dpcQuality, filter = depthFilt, reuse_depth = False)
                        new_chunk.buildDenseCloud(point_colors = dpcColors)
                    except RuntimeError:
                        print("Can't build dense cloud for " + chunk.label)

                    if autosave:
                        doc.save()

                    #Now build a mesh if chosen
                    if buildMesh:
                        meshFaceCount = int(self.faceCount.value())
                        if self.meshInterpolationChoice.currentText() == "Enabled-default":
                            interp = PhotoScan.Interpolation.EnabledInterpolation
                        else:
                            interp = PhotoScan.Interpolation.Extrapolated
                        #vertexColors = self.calcVertexColors.isChecked()
                        vertexColors = True
                        if self.surfaceType.currentText == "Arbitrary(3D)":
                            surfType = PhotoScan.SurfaceType.Arbitrary
                        else:
                            surfType = PhotoScan.SurfaceType.HeightField

                        try:
                            new_chunk.buildModel(surface = surfType, interpolation = interp, face_count = meshFaceCount, source = PhotoScan.DataSource.DenseCloudData)
                        except RuntimeError:
                            print("Can't build mesh for " + chunk.label)

                        if autosave:
                            doc.save()


        if mergeBack:
            chunkList=[]
            for i in range(chunkIndex+1, len(doc.chunks)):
                chunkList.append(doc.chunks[i])
                chunk = doc.chunks[i]
                if i > chunkIndex+1:
                    chunk.remove(chunk.cameras)
            #doc.chunks[0].model = None #removing model from original chunk, just for case
            if buildDense == True and buildMesh == False:
                doc.mergeChunks(chunkList, merge_dense_clouds = True, merge_models = False, merge_markers = True) #merging all smaller chunks into single one
            else:
                doc.mergeChunks(chunkList, merge_dense_clouds = True, merge_models = True, merge_markers = True)

            doc.mergeChunks(chunkList, merge_dense_clouds = True, merge_models = True, merge_markers = True) #merging all smaller chunks into single one

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
        doc = PhotoScan.app.document
        chunk = doc.chunk

        T = chunk.transform.matrix

        v_t = T * PhotoScan.Vector( [0,0,0,1] )
        v_t.size = 3

        if chunk.crs:
                m = chunk.crs.localframe(v_t)
        else:
                m = PhotoScan.Matrix().diag([1,1,1,1])

        m = m * T

        s = math.sqrt(m[0,0] ** 2 + m[0,1] ** 2 + m[0,2] ** 2) #scale factor

        R = PhotoScan.Matrix( [[m[0,0],m[0,1],m[0,2]], [m[1,0],m[1,1],m[1,2]], [m[2,0],m[2,1],m[2,2]]])

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

        doc = PhotoScan.app.document
        chunk = doc.chunk

        R = chunk.region.rot        #Bounding region rotation matrix
        C = chunk.region.center        #Bounding region center vector

        if chunk.transform.matrix:
                T = chunk.transform.matrix
                s = math.sqrt(T[0,0] ** 2 + T[0,1] ** 2 + T[0,2] ** 2)         #scaling
                S = PhotoScan.Matrix( [[s, 0, 0, 0], [0, s, 0, 0], [0, 0, s, 0], [0, 0, 0, 1]] ) #scale matrix
        else:
                S = PhotoScan.Matrix( [[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]] )

        T = PhotoScan.Matrix( [[R[0,0], R[0,1], R[0,2], C[0]], [R[1,0], R[1,1], R[1,2], C[1]], [R[2,0], R[2,1], R[2,2], C[2]], [0, 0, 0, 1]])

        chunk.transform.matrix = S * T.inv()        #resulting chunk transformation matrix


def footprints():

    global doc
    doc = PhotoScan.app.document
    app = QtWidgets.QApplication.instance()
    parent = app.activeWindow()
    dlg = CreateCSVFileDlg(parent)



def main():
 #adds custom menu item
        PhotoScan.app.addMenuItem("BLM NOC Tools/Automated Workflows/Align Images and Perform Initial Error Reduction", processRegularDataset)
        PhotoScan.app.addMenuItem("BLM NOC Tools/Automated Workflows/Align Images and Perform Initial ER for Historic Imagery", processHistoricDataset)
        PhotoScan.app.addMenuItem("BLM NOC Tools/Automated Workflows/Reprojection Error Reduction and optionally build products", erReprojectionError)
        PhotoScan.app.addMenuItem("BLM NOC Tools/Automated Workflows/Reconstruction Uncertainty and Projection Accuarcy Error Reduction", erReconProj)
        PhotoScan.app.addMenuItem("BLM NOC Tools/Adjust Region/Align Bounding Region to Coordinate System", bbtocs)
        PhotoScan.app.addMenuItem("BLM NOC Tools/Adjust Region/Get Coordinate System from Bounding Region", cstobb)
        PhotoScan.app.addMenuItem("BLM NOC Tools/Split chunk into smaller chunks for processing", csic)

        #PhotoScan.app.addMenuItem("Custom menu/Align Bounding Region to Coordinate System", bbtocs)
        #PhotoScan.app.addMenuItem("Custom menu/Get Coordinate System from Bounding Region", cstobb)
        PhotoScan.app.addMenuItem("BLM NOC Tools/Adjust Region/Copy current bounding region to all chunks", copybb)
        PhotoScan.app.addMenuItem("BLM NOC Tools/Adjust accuracy and optimize cameras", optimizecamcal)
        PhotoScan.app.addMenuItem("BLM NOC Tools/Remove Blue, unpinned marker(s)", removeblue)
        PhotoScan.app.addMenuItem("BLM NOC Tools/Rename markers to integers", renamemarkers)
        PhotoScan.app.addMenuItem("BLM NOC Tools/Create text file with solved coordinates and keywords to update image EXIF", geotag_photoscan1)


        print("Custom BLM Toolbar Added")



main()
