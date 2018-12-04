"""VTK labeling UI

Mainframe for vtk-labeling based on PyQt, vtk. 

"""
import os
import sys

import ipdb
import numpy as np
import vtk
from vtk.util import numpy_support
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (QApplication, QButtonGroup, QDesktopWidget,
                             QFileDialog, QFrame, QHBoxLayout, QLabel,
                             QLineEdit, QMainWindow, QPushButton, QRadioButton,
                             QSlider, QVBoxLayout, QWidget)
from vtk.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor

from algorithm import (addSelection, inverseSelection, minusSelection,
                       multiThresholdExpand, onSelectedExpand)
from highlightCellPick import MouseInteractorPickCell
from vtkio import readSTL, writeVTP


class ToothViewer(QFrame):
    def __init__(self):
        super(ToothViewer, self).__init__()

        interactor = QVTKRenderWindowInteractor(self)
        self.layout = QVBoxLayout()
        self.layout.addWidget(interactor)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self.layout)

        # renderer and render window
        self.renderWindow = interactor.GetRenderWindow()
        self.renderer = vtk.vtkRenderer()
        self.renderWindow.AddRenderer(self.renderer)
        self.interactor = interactor

        self.initializeWithSphere()

        # Selected Mapper and Actor
        self.pickedMapper = vtk.vtkDataSetMapper()
        self.pickedActor = vtk.vtkActor()
        self.selectedMapper = vtk.vtkDataSetMapper()
        self.selectedActor = vtk.vtkActor()

        # selection Mode
        self.selectionMode = 'PIC'
        self.selected_ids = vtk.vtkIdTypeArray()
        self.selected_ids.SetNumberOfComponents(1)
        self.selected_ids_list = list()

    def initializeWithSphere(self):
        # Create source
        source = vtk.vtkSphereSource()
        source.SetCenter(0, 0, 0)
        source.SetRadius(5.0)
        source.Update()
        self.polyData = source.GetOutput()

        # Create a mapper
        mapper = vtk.vtkPolyDataMapper()
        mapper.SetInputData(self.polyData)

        # Create an actor
        actor = vtk.vtkActor()
        actor.SetMapper(mapper)

        self.renderer.AddActor(actor)
        self.renderer.ResetCamera()

    def update(self, ids):
        self.ids = ids

        if len(self.selected_ids_list) <= 100:
            self.selected_ids_list.append(self.selected_ids)
        else:
            self.selected_ids_list = self.selected_ids_list[1:]

        if self.selectionMode == 'ADD':
            self.selected_ids = addSelection(
                self.selected_ids,
                multiThresholdExpand(self.polyData, ids,
                                     self.neighborThreshold,
                                     self.angleThreshold))
        elif self.selectionMode == 'SEL':
            self.selected_ids = multiThresholdExpand(self.polyData, ids,
                                                     self.neighborThreshold,
                                                     self.angleThreshold)
        elif self.selectionMode == 'DEL':
            self.selected_ids = minusSelection(
                self.selected_ids,
                multiThresholdExpand(self.polyData, ids,
                                     self.neighborThreshold,
                                     self.angleThreshold))
        self.highlight()

    def highlight(self):

        self.highlight_with_id(self.selected_ids, (1, 0, 0),
                               self.selectedMapper, self.selectedActor)
        self.highlight_with_id(self.ids, (0, 0, 1), self.pickedMapper,
                               self.pickedActor)

    def highlight_with_id(self, ids, color, mapper, actor):
        selectionNode = vtk.vtkSelectionNode()
        selectionNode.SetFieldType(vtk.vtkSelectionNode.CELL)
        selectionNode.SetContentType(vtk.vtkSelectionNode.INDICES)
        selectionNode.SetSelectionList(ids)

        selection = vtk.vtkSelection()
        selection.AddNode(selectionNode)

        extractSelection = vtk.vtkExtractSelection()
        extractSelection.SetInputData(0, self.polyData)
        extractSelection.SetInputData(1, selection)
        extractSelection.Update()

        selected = vtk.vtkUnstructuredGrid()
        selected.ShallowCopy(extractSelection.GetOutput())

        mapper.SetInputData(selected)
        actor.SetMapper(mapper)
        actor.GetProperty().SetColor(*color)

        self.interactor.GetRenderWindow().GetRenderers().GetFirstRenderer(
        ).AddActor(actor)

        self.interactor.GetRenderWindow().Render()

    def start(self):

        style = MouseInteractorPickCell(self.polyData, self)
        style.SetDefaultRenderer(self.renderer)
        self.interactor.SetInteractorStyle(style)
        self.interactor.Initialize()
        self.interactor.Start()


class ToothViewerApp(QMainWindow):
    def __init__(self):
        super(ToothViewerApp, self).__init__()

        self.toothViewer = None
        self.widget = QWidget()
        self.setCentralWidget(self.widget)
        self.initUI()

    def initUI(self):
        # Status Bar Initialization
        self.statusBar().showMessage('Ready')

        # VTK window Initialization
        self.toothViewer = ToothViewer()
        self.toothViewer.setGeometry(20, 20, 500, 500)

        # IO Pannel Initiliaztion
        self.loadButton = QPushButton("LOAD")
        self.saveButton = QPushButton("SAVE")
        self.loadFilePath = None
        IOPanel = QHBoxLayout()
        IOPanel.addWidget(self.loadButton)
        IOPanel.addWidget(self.saveButton)

        # Selection Mode Panel Iitialization
        self.noSelectionButton = QPushButton('PICK')
        self.selectButton = QPushButton('SELECT')
        self.addSelectionButton = QPushButton('ADD')
        self.minusSelectionButton = QPushButton('MINUS')
        self.reverseButton = QPushButton('REVERSE')

        self.noSelectionButton.setAutoExclusive(True)
        self.selectButton.setAutoExclusive(True)
        self.addSelectionButton.setAutoExclusive(True)
        self.minusSelectionButton.setAutoExclusive(True)

        self.noSelectionButton.setCheckable(True)
        self.selectButton.setCheckable(True)
        self.addSelectionButton.setCheckable(True)
        self.minusSelectionButton.setCheckable(True)
        self.noSelectionButton.setChecked(True)

        selectionModePanel = QVBoxLayout()
        selectionModePanel.addWidget(self.noSelectionButton)
        selectionModePanel.addWidget(self.selectButton)
        selectionModePanel.addWidget(self.addSelectionButton)
        selectionModePanel.addWidget(self.minusSelectionButton)
        selectionModePanel.addWidget(self.reverseButton)

        # Selection Method Panel Initalization

        self.neighborLabel = QLabel("NEIGHBOR")
        self.neighborLabel.setAlignment(Qt.AlignHCenter)
        self.neighborThresholdSlider = QSlider(Qt.Vertical)
        self.neighborThresholdSlider.setMaximum(100)
        self.neighborThresholdSlider.setMinimum(0)
        self.neighborThresholdSlider.setValue(5)
        self.neighborThresholdSlider.setInvertedAppearance(True)
        self.neighborThresholdSliderLayout = QHBoxLayout()
        self.neighborThresholdSliderLayout.addWidget(
            self.neighborThresholdSlider)
        self.neighborCount = QLabel("5")
        self.neighborCount.setAlignment(Qt.AlignHCenter)
        self.toothViewer.neighborThreshold = self.neighborThresholdSlider.value(
        )

        neighborMode = QVBoxLayout()
        neighborMode.setAlignment(Qt.AlignHCenter)
        neighborMode.addWidget(self.neighborLabel)
        neighborMode.addLayout(self.neighborThresholdSliderLayout)
        neighborMode.addWidget(self.neighborCount)

        self.angleLabel = QLabel("ANGLE")
        self.angleLabel.setAlignment(Qt.AlignHCenter)
        self.angleThresholdSlider = QSlider(Qt.Vertical)
        self.angleThresholdSlider.setMaximum(180)
        self.angleThresholdSlider.setMinimum(0)
        self.angleThresholdSlider.setValue(90)
        self.angleThresholdSlider.setInvertedAppearance(True)
        self.angleThresholdSliderLayout = QHBoxLayout()
        self.angleThresholdSliderLayout.addWidget(self.angleThresholdSlider)
        self.angleCount = QLabel("90")
        self.angleCount.setAlignment(Qt.AlignHCenter)
        self.toothViewer.angleThreshold = self.angleThresholdSlider.value()

        angleMode = QVBoxLayout()
        angleMode.addWidget(self.angleLabel)
        angleMode.addLayout(self.angleThresholdSliderLayout)
        angleMode.addWidget(self.angleCount)

        selectionMethodPanel = QHBoxLayout()
        selectionMethodPanel.addLayout(neighborMode)
        selectionMethodPanel.addLayout(angleMode)

        # Selection Algorithm Panel Initalization
        self.inverseButton = QPushButton('INVERSE')
        self.removeOutlierButton = QPushButton('CLEAN OUTLIER')

        selectionAlgorithmPanel = QVBoxLayout()
        selectionAlgorithmPanel.addWidget(self.inverseButton)
        selectionAlgorithmPanel.addWidget(self.removeOutlierButton)

        # Function Connection
        self.loadButton.clicked.connect(self.loadSTL)
        self.saveButton.clicked.connect(self.saveVTP)
        self.neighborThresholdSlider.valueChanged.connect(
            self.adjustNeighborThreshold)
        self.angleThresholdSlider.valueChanged.connect(
            self.adjustAngleThreshold)
        self.noSelectionButton.clicked.connect(self.switchSelectionMode)
        self.addSelectionButton.clicked.connect(self.switchSelectionMode)
        self.selectButton.clicked.connect(self.switchSelectionMode)
        self.minusSelectionButton.clicked.connect(self.switchSelectionMode)
        self.reverseButton.clicked.connect(self.reverseOperation)
        self.removeOutlierButton.clicked.connect(self.removeOutlier)
        self.inverseButton.clicked.connect(self.inverse)

        # Entire layout
        panel = QVBoxLayout()
        panel.addLayout(selectionModePanel)
        panel.addLayout(selectionMethodPanel)
        panel.addLayout(selectionAlgorithmPanel)
        panel.addLayout(IOPanel)

        vbox = QHBoxLayout()
        vbox.addWidget(self.toothViewer)
        vbox.addLayout(panel)
        vbox.setStretchFactor(self.toothViewer, 1)
        vbox.setStretchFactor(panel, 0)

        self.setGeometry(20, 20, 800, 600)
        self.setWindowTitle('Mesh Labeling Tool')
        self.widget.setLayout(vbox)
        self.show()
        self.toothViewer.start()

    def inverse(self):
        self.toothViewer.selected_ids = inverseSelection(
            self.toothViewer.polyData, self.toothViewer.selected_ids)
        self.toothViewer.highlight()

    def removeOutlier(self):
        if self.toothViewer.selected_ids.GetNumberOfValues() > 0:
            self.toothViewer.selected_ids = onSelectedExpand(
                self.toothViewer.polyData, self.toothViewer.ids,
                self.toothViewer.selected_ids)
            self.toothViewer.highlight()

    def reverseOperation(self):
        if len(self.toothViewer.selected_ids_list) > 0:
            self.toothViewer.selected_ids = self.toothViewer.selected_ids_list.pop(
            )
            self.toothViewer.highlight()

    def switchSelectionMode(self):
        if self.addSelectionButton.isChecked():
            self.toothViewer.selectionMode = 'ADD'
        elif self.selectButton.isChecked():
            self.toothViewer.selectionMode = 'SEL'
        elif self.minusSelectionButton.isChecked():
            self.toothViewer.selectionMode = 'DEL'
        else:
            self.toothViewer.selectionMode = 'PIC'

    def adjustNeighborThreshold(self):
        self.neighborCount.setText(str(self.neighborThresholdSlider.value()))
        self.toothViewer.neighborThreshold = self.neighborThresholdSlider.value(
        )

    def adjustAngleThreshold(self):
        self.angleCount.setText(str(self.angleThresholdSlider.value()))
        self.toothViewer.angleThreshold = self.angleThresholdSlider.value()

    def loadSTL(self):

        filename = QFileDialog.getOpenFileName(self, 'Select STL file',
                                               filter='3D Object(*.stl)')

        if filename[0] != '':
            polyData = readSTL(filename[0])
        else:
            return

        self.toothViewer.renderer.RemoveAllViewProps()
        self.toothViewer.polyData = polyData

        toothMapper = vtk.vtkPolyDataMapper()
        toothMapper.SetInputData(self.toothViewer.polyData)
        toothActor = vtk.vtkActor()
        toothActor.SetMapper(toothMapper)

        self.toothViewer.renderer.AddActor(toothActor)
        self.toothViewer.renderer.ResetCamera()
        self.toothViewer.renderWindow.Render()

        self.loadFilePath = filename

    def saveVTP(self):
        if self.loadFilePath:
            default_filename = os.path.splitext(
                self.loadFilePath[0])[0] + '.vtp'
        else:
            default_filename = '.'
        filename = QFileDialog.getSaveFileName(
            self, 'Save File', default_filename,
            filter='VTK Polygonal Data (*.vtp)')

        if filename[0] == '':
            return

        polyData = vtk.vtkPolyData()
        polyData.DeepCopy(self.toothViewer.polyData)
        # Cell Label
        cellLabels = np.zeros(polyData.GetNumberOfCells(), dtype=np.uint8)
        selectedCellIds = set([
            self.toothViewer.selected_ids.GetValue(i)
            for i in range(self.toothViewer.selected_ids.GetNumberOfValues())
        ])
        cellLabels[np.array(list(selectedCellIds), np.int32)] = 1
        polyData.GetCellData().SetScalars(
            numpy_support.numpy_to_vtk(cellLabels))
        # Point Label
        pointLabels = np.zeros(polyData.GetNumberOfPoints(), dtype=np.uint8)
        pointIds = set()
        for cellId in selectedCellIds:
            cellPointIds = vtk.vtkIdList()
            polyData.GetCellPoints(cellId, cellPointIds)
            for i in range(cellPointIds.GetNumberOfIds()):
                pointIds.add(cellPointIds.GetId(i))
        pointLabels[np.array(list(pointIds), np.int32)] = 1
        polyData.GetPointData().SetScalars(
            numpy_support.numpy_to_vtk(pointLabels))

        writeVTP(polyData, filename[0])


if __name__ == '__main__':

    app = QApplication(sys.argv)
    main_window = ToothViewerApp()
    main_window.show()
    sys.exit(app.exec_())
