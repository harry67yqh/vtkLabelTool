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
                             QRadioButton, QButtonGroup, QSlider)
from PyQt5.QtCore import Qt
from vtk.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor
import vtk
from highlightCellPick import MouseInteractorPickCell

from vtkio import readSTL
from expandAlgorithm import neighborExpand, angleExpand


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
        self.expandAlgorithm = lambda polyData, ids: neighborExpand(polyData, ids, 5)

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

    def updateExpandAlgorithm(self, expandAlgorithm):
        self.expandAlgorithm = expandAlgorithm

    def update(self, ids):
        self.ids = ids
        self.expanded_ids = self.expandAlgorithm(self.polyData, ids)
        self.highlight(self.expanded_ids)

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
        self.loadButton = QPushButton("Load")
        self.saveButton = QPushButton("Save")

        # Selection Mode Pannel Initialization
        self.neighborSelectButton = QRadioButton("Neighbor")
        self.angleSelectButton = QRadioButton("Angle")
        self.selectModeGroup = QButtonGroup(self)
        self.selectModeGroup.addButton(self.neighborSelectButton)
        self.selectModeGroup.addButton(self.angleSelectButton)
        self.neighborSelectButton.setChecked(True)

        self.neighborThresholdSlider = QSlider(Qt.Horizontal)
        self.neighborThresholdSlider.setMaximum(20)
        self.neighborThresholdSlider.setMinimum(1)
        self.neighborThresholdSlider.setValue(5)

        self.angleThresholdSlider = QSlider(Qt.Horizontal)
        self.angleThresholdSlider.setMaximum(100)
        self.angleThresholdSlider.setMinimum(0)
        self.angleThresholdSlider.setValue(50)

        self.neighborThreshold = self.neighborThresholdSlider.value()
        self.angleThreshold = self.angleThresholdSlider.value() * 0.01

        self.loadButton.clicked.connect(self.loadSTL)
        self.neighborSelectButton.toggled.connect(self.switchToNeighborMode)
        self.angleSelectButton.toggled.connect(self.swtichToAngleMode)

        self.neighborThresholdSlider.valueChanged.connect(
            self.adjustNeighborThreshold)
        self.angleThresholdSlider.valueChanged.connect(
            self.adjustAngleThreshold
        )
        

        # Layout Design
        neighborMode = QHBoxLayout()
        neighborMode.addWidget(self.neighborSelectButton)
        neighborMode.addWidget(self.neighborThresholdSlider)

        angleMode = QHBoxLayout()
        angleMode.addWidget(self.angleSelectButton)
        angleMode.addWidget(self.angleThresholdSlider)

        selectionModePanel = QVBoxLayout()
        selectionModePanel.addLayout(neighborMode)
        selectionModePanel.addLayout(angleMode)

        IOPanel = QVBoxLayout()
        IOPanel.addWidget(self.loadButton)
        IOPanel.addWidget(self.saveButton)

        panel = QHBoxLayout()
        panel.addLayout(selectionModePanel)
        panel.addLayout(IOPanel)

        vbox = QVBoxLayout()
        vbox.addWidget(self.toothViewer)
        vbox.addLayout(panel)

        self.setGeometry(20, 20, 800, 600)
        self.setWindowTitle('Mesh Labeling Tool')
        self.widget.setLayout(vbox)
        self.show()
        self.toothViewer.start()

    def adjustNeighborThreshold(self):
        self.neighborThreshold = self.neighborThresholdSlider.value()
        self.toothViewer.updateExpandAlgorithm(
            lambda polyData, ids: neighborExpand(polyData, ids, self.neighborThreshold)
        )

    def switchToNeighborMode(self):
        self.toothViewer.updateExpandAlgorithm(
            lambda polyData, ids: neighborExpand(polyData, ids, self.neighborThreshold)
        )

    def adjustAngleThreshold(self):
        self.angleThreshold = self.angleThresholdSlider.value() * 0.01
        self.toothViewer.updateExpandAlgorithm(
            lambda polyData, ids: angleExpand(polyData, ids, self.angleThreshold)
        )

    def swtichToAngleMode(self):
        self.toothViewer.updateExpandAlgorithm(
            lambda polyData, ids: angleExpand(polyData, ids, self.angleThreshold)
        )



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
