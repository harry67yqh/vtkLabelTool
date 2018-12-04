"""VTK labeling UI

Mainframe for vtk-labeling based on PyQt, vtk. 

"""
import sys
import os
import numpy as np
import pdb
from PyQt5.QtWidgets import (QApplication, QWidget, QDesktopWidget,
                             QFileDialog, QFrame, QVBoxLayout, QMainWindow,
                             QPushButton, QLineEdit, QHBoxLayout, QVBoxLayout,
                             QRadioButton, QButtonGroup, QSlider, QLabel)
from PyQt5.QtCore import Qt
from vtk.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor
import vtk
from highlightCellPick import MouseInteractorPickCell

from vtkio import readSTL
from expandAlgorithm import multiThresholdExpand, addSelection, minusSelection


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
        self.selectedMapper = vtk.vtkDataSetMapper()
        self.selectedActor = vtk.vtkActor()

        # selection Mode
        self.selectionMode = 'NOT'
        self.selected_ids = vtk.vtkIdTypeArray()
        self.selected_ids.SetNumberOfComponents(1)

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
        else:
            return
        self.highlight(self.selected_ids)

    def highlight(self, ids):

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

        self.selectedMapper.SetInputData(selected)
        self.selectedActor.SetMapper(self.selectedMapper)
        self.selectedActor.GetProperty().SetColor(1, 0, 0)

        self.interactor.GetRenderWindow().GetRenderers().GetFirstRenderer(
        ).AddActor(self.selectedActor)

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
        IOPanel = QHBoxLayout()
        IOPanel.addWidget(self.loadButton)
        IOPanel.addWidget(self.saveButton)

        # Selection Mode Panel Iitialization
        self.noSelectionButton = QPushButton('N')
        self.selectButton = QPushButton('o')
        self.addSelectionButton = QPushButton('+')
        self.minusSelectionButton = QPushButton('-')
        self.noSelectionButton.setAutoExclusive(True)
        self.selectButton.setAutoExclusive(True)
        self.addSelectionButton.setAutoExclusive(True)
        self.minusSelectionButton.setAutoExclusive(True)
        self.noSelectionButton.setCheckable(True)
        self.selectButton.setCheckable(True)
        self.addSelectionButton.setCheckable(True)
        self.minusSelectionButton.setCheckable(True)
        self.noSelectionButton.setChecked(True)

        selectionModePanel = QHBoxLayout()
        selectionModePanel.addWidget(self.noSelectionButton)
        selectionModePanel.addWidget(self.selectButton)
        selectionModePanel.addWidget(self.addSelectionButton)
        selectionModePanel.addWidget(self.minusSelectionButton)

        # Selection Method Panel Initalization

        self.neighborLabel = QLabel("NEIGHBOR")
        self.neighborThresholdSlider = QSlider(Qt.Horizontal)
        self.neighborThresholdSlider.setMaximum(100)
        self.neighborThresholdSlider.setMinimum(0)
        self.neighborThresholdSlider.setValue(5)
        self.neighborCount = QLabel("5")
        self.toothViewer.neighborThreshold = self.neighborThresholdSlider.value(
        )

        neighborMode = QHBoxLayout()
        neighborMode.addWidget(self.neighborLabel)
        neighborMode.addWidget(self.neighborThresholdSlider)
        neighborMode.addWidget(self.neighborCount)

        self.angleLabel = QLabel("ANGLE (DEGREE)")
        self.angleThresholdSlider = QSlider(Qt.Horizontal)
        self.angleThresholdSlider.setMaximum(180)
        self.angleThresholdSlider.setMinimum(0)
        self.angleThresholdSlider.setValue(90)
        self.angleCount = QLabel("90")
        self.toothViewer.angleThreshold = self.angleThresholdSlider.value()

        angleMode = QHBoxLayout()
        angleMode.addWidget(self.angleLabel)
        angleMode.addWidget(self.angleThresholdSlider)
        angleMode.addWidget(self.angleCount)

        selectionMethodPanel = QVBoxLayout()
        selectionMethodPanel.addLayout(neighborMode)
        selectionMethodPanel.addLayout(angleMode)

        # Selection Algorithm Panel Initalization

        self.inverseButton = QPushButton('INVERSE')
        self.boundaryOptimizationButton = QPushButton('BOUNDARY OPTIMIZATION')
        self.fillHoleButton = QPushButton('FILL HOLE')

        selectionAlgorithmPanel = QVBoxLayout()
        selectionAlgorithmPanel.addWidget(self.inverseButton)
        selectionAlgorithmPanel.addWidget(self.boundaryOptimizationButton)
        selectionAlgorithmPanel.addWidget(self.fillHoleButton)

        # Function Connection
        self.loadButton.clicked.connect(self.loadSTL)

        self.neighborThresholdSlider.valueChanged.connect(
            self.adjustNeighborThreshold)
        self.angleThresholdSlider.valueChanged.connect(
            self.adjustAngleThreshold)
        self.noSelectionButton.clicked.connect(self.switchSelectionMode)
        self.addSelectionButton.clicked.connect(self.switchSelectionMode)
        self.selectButton.clicked.connect(self.switchSelectionMode)
        self.minusSelectionButton.clicked.connect(self.switchSelectionMode)

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

    def switchSelectionMode(self):
        if self.addSelectionButton.isChecked():
            self.toothViewer.selectionMode = 'ADD'
        elif self.selectButton.isChecked():
            self.toothViewer.selectionMode = 'SEL'
        elif self.minusSelectionButton.isChecked():
            self.toothViewer.selectionMode = 'DEL'
        else:
            self.toothViewer.selectionMode = 'NOT'

    def adjustNeighborThreshold(self):
        self.neighborCount.setText(str(self.neighborThresholdSlider.value()))
        self.toothViewer.neighborThreshold = self.neighborThresholdSlider.value(
        )

    def adjustAngleThreshold(self):
        self.angleCount.setText(str(self.angleThresholdSlider.value()))
        self.toothViewer.angleThreshold = self.angleThresholdSlider.value()

    def loadSTL(self):
        try:
            filename = QFileDialog.getOpenFileName(self, 'Select STL file')
            polyData = readSTL(filename[0])
        except:
            self.statusBar().showMessage('Loading File Failed.')
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


if __name__ == '__main__':

    app = QApplication(sys.argv)
    main_window = ToothViewerApp()
    main_window.show()
    sys.exit(app.exec_())
