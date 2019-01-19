import os
import sys
from metrics.lib.utils import BBFormat
import argparse
import glob
import os
import shutil
from metrics.lib.BoundingBox import BoundingBox
from metrics.lib.BoundingBoxes import BoundingBoxes
from metrics.lib.Evaluator import *
from metrics.lib.utils import BBFormat


class Metrics:

    def __init__(self, currentPath, gtFormat, detFormat, gtFolder, gtCoordinates, detCoordinates, imgSize, detFolder,
                 iouThreshold):
        self.currentPath = currentPath
        self.iouThreshold = iouThreshold

        # Arguments validation
        errors = []

        # Validate formats
        self.gtFormat = self._ValidateFormats(gtFormat, '-gtformat', errors)
        self.detFormat = self._ValidateFormats(detFormat, '-detformat', errors)

        if self._ValidateMandatoryArgs(gtFolder, '-gt/--gtfolder', errors):
            self.gtFolder = self._ValidatePaths(gtFolder, '-gt/--gtfolder', errors)
        else:
            # errors.pop()
            self.gtFolder = os.path.join(self.currentPath, 'groundtruths')
            if os.path.isdir(gtFolder) is False:
                errors.append('folder %s not found' % gtFolder)

        # Coordinates types
        self.gtCoordType = self._ValidateCoordinatesTypes(gtCoordinates, '-gtCoordinates', errors)
        self.detCoordType = self._ValidateCoordinatesTypes(detCoordinates, '-detCoordinates', errors)
        self.imgSize = (0, 0)
        if self.gtCoordType == CoordinatesType.Relative:  # Image size is required
            self.imgSize = self._ValidateImageSize(imgSize, '-imgsize', '-gtCoordinates', errors)
        if self.detCoordType == CoordinatesType.Relative:  # Image size is required
            self.imgSize = self._ValidateImageSize(imgSize, '-imgsize', '-detCoordinates', errors)

        # Detection folder
        if self._ValidateMandatoryArgs(detFolder, '-det/--detfolder', errors):
            self.detFolder = self._ValidatePaths(detFolder, '-det/--detfolder', errors)
        else:
            # errors.pop()
            self.detFolder = os.path.join(self.currentPath, 'detections')
            if os.path.isdir(self.detFolder) is False:
                errors.append('folder %s not found' % detFolder)

        if len(errors) is not 0:
            print("""usage: Object Detection Metrics [-h] [-v] [-gt] [-det] [-t] [-gtformat]
                                        [-detformat] [-save]""")
            print('Object Detection Metrics: error(s): ')
            [print(e) for e in errors]
            sys.exit()

    @staticmethod
    def _ValidateFormats(argFormat, argName, errors):
        """ Validate formats"""
        if argFormat == 'xywh':
            return BBFormat.XYWH
        elif argFormat == 'xyrb':
            return BBFormat.XYX2Y2
        elif argFormat is None:
            return BBFormat.XYWH  # default when nothing is passed
        else:
            errors.append(
                'argument %s: invalid value. It must be either \'xywh\' or \'xyrb\'' % argName)

    @staticmethod
    def _ValidateMandatoryArgs(arg, argName, errors):
        """Validate mandatory args"""
        if arg is None:
            errors.append('argument %s: required argument' % argName)
        else:
            return True

    @staticmethod
    def _ValidateImageSize(arg, argName, argInformed, errors):
        errorMsg = 'argument %s: required argument if %s is relative' % (argName, argInformed)
        ret = None
        if arg is None:
            errors.append(errorMsg)
        else:
            arg = arg.replace('(', '').replace(')', '')
            args = arg.split(',')
            if len(args) != 2:
                errors.append(
                    '%s. It must be in the format \'width,height\' (e.g. \'600,400\')' % errorMsg)
            else:
                if not args[0].isdigit() or not args[1].isdigit():
                    errors.append(
                        '%s. It must be in INdiaTEGER the format \'width,height\' (e.g. \'600,400\')' %
                        errorMsg)
                else:
                    ret = (int(args[0]), int(args[1]))
        return ret

    @staticmethod
    def _ValidateCoordinatesTypes(arg, argName, errors):
        """
        # Validate coordinate types
        """
        if arg == 'abs':
            return CoordinatesType.Absolute
        elif arg == 'rel':
            return CoordinatesType.Relative
        elif arg is None:
            return CoordinatesType.Absolute  # default when nothing is passed
        errors.append('argument %s: invalid value. It must be either \'rel\' or \'abs\'' % argName)

    def _ValidatePaths(self, arg, nameArg, errors):
        if arg is None:
            errors.append('argument %s: invalid directory' % nameArg)
        elif os.path.isdir(arg) is False and os.path.isdir(os.path.join(self.currentPath, arg)) is False:
            errors.append('argument %s: directory does not exist \'%s\'' % (nameArg, arg))
        # elif os.path.isdir(os.path.join(currentPath, arg)) is True:
        #     arg = os.path.join(currentPath, arg)
        else:
            arg = os.path.join(self.currentPath, arg)
        return arg

    @staticmethod
    def _getBoundingBoxes(directory,
                          isGT,
                          bbFormat,
                          coordType,
                          allBoundingBoxes=None,
                          allClasses=None,
                          imgSize=(0, 0)):
        """Read txt files containing bounding boxes (ground truth and detections)."""
        if allBoundingBoxes is None:
            allBoundingBoxes = BoundingBoxes()
        if allClasses is None:
            allClasses = []
        # Read ground truths
        os.chdir(directory)
        files = glob.glob("*.txt")
        files.sort()
        # Read GT detections from txt file
        # Each line of the files in the groundtruths folder represents a ground truth bounding box
        # (bounding boxes that a detector should detect)
        # Each value of each line is  "class_id, x, y, width, height" respectively
        # Class_id represents the class of the bounding box
        # x, y represents the most top-left coordinates of the bounding box
        # x2, y2 represents the most bottom-right coordinates of the bounding box
        for f in files:
            nameOfImage = f.replace(".txt", "")
            fh1 = open(f, "r")
            for line in fh1:
                line = line.replace("\n", "")
                if line.replace(' ', '') == '':
                    continue
                splitLine = line.split(" ")
                if isGT:
                    # idClass = int(splitLine[0]) #class
                    idClass = (splitLine[0])  # class
                    x = float(splitLine[1])
                    y = float(splitLine[2])
                    w = float(splitLine[3])
                    h = float(splitLine[4])
                    bb = BoundingBox(
                        nameOfImage,
                        idClass,
                        x,
                        y,
                        w,
                        h,
                        coordType,
                        imgSize,
                        BBType.GroundTruth,
                        format=bbFormat)
                else:
                    # idClass = int(splitLine[0]) #class
                    idClass = (splitLine[0])  # class
                    confidence = float(splitLine[1])
                    x = float(splitLine[2])
                    y = float(splitLine[3])
                    w = float(splitLine[4])
                    h = float(splitLine[5])
                    bb = BoundingBox(
                        nameOfImage,
                        idClass,
                        x,
                        y,
                        w,
                        h,
                        coordType,
                        imgSize,
                        BBType.Detected,
                        confidence,
                        format=bbFormat)
                allBoundingBoxes.addBoundingBox(bb)
                if idClass not in allClasses:
                    allClasses.append(idClass)
            fh1.close()
        return allBoundingBoxes, allClasses

    def run(self):
        # Get groundtruth boxes
        allBoundingBoxes, allClasses = self._getBoundingBoxes(
            self.gtFolder, True, self.gtFormat, self.gtCoordType, imgSize=self.imgSize)
        # Get detected boxes
        allBoundingBoxes, allClasses = self._getBoundingBoxes(
            self.detFolder, False, self.detFormat, self.detCoordType, allBoundingBoxes, allClasses, imgSize=self.imgSize)
        allClasses.sort()

        evaluator = Evaluator()
        acc_AP = 0
        validClasses = 0

        # Plot Precision x Recall curve
        detections = evaluator.PlotPrecisionRecallCurve(
            allBoundingBoxes,  # Object containing all bounding boxes (ground truths and detections)
            IOUThreshold=self.iouThreshold,  # IOU threshold
            method=MethodAveragePrecision.EveryPointInterpolation,
            showAP=True,  # Show Average Precision in the title of the plot
            showInterpolatedPrecision=False,  # Don't plot the interpolated precision curve
            savePath=None,#savePath,
            showGraphic=True)#showPlot)

        # each detection is a class
        for metricsPerClass in detections:

            # Get metric values per each class
            cl = metricsPerClass['class']
            ap = metricsPerClass['AP']
            precision = metricsPerClass['precision']
            recall = metricsPerClass['recall']
            totalPositives = metricsPerClass['total positives']
            total_TP = metricsPerClass['total TP']
            total_FP = metricsPerClass['total FP']

            if totalPositives > 0:
                validClasses = validClasses + 1
                acc_AP = acc_AP + ap
                prec = ['%.2f' % p for p in precision]
                rec = ['%.2f' % r for r in recall]
                ap_str = "{0:.2f}%".format(ap * 100)
                # ap_str = "{0:.4f}%".format(ap * 100)
                print('AP: %s (%s)' % (ap_str, cl))
                #f.write('\n\nClass: %s' % cl)
                #f.write('\nAP: %s' % ap_str)
                #f.write('\nPrecision: %s' % prec)
                #f.write('\nRecall: %s' % rec)

        mAP = acc_AP / validClasses
        mAP_str = "{0:.2f}%".format(mAP * 100)
        print('mAP: %s' % mAP_str)
        #f.write('\n\n\nmAP: %s' % mAP_str)
        os.chdir(self.currentPath)
