#!/usr/bin/env python

# This example demonstrates cell picking using vtkCellPicker.  It
# displays the results of picking using a vtkTextMapper.

from __future__ import print_function
import vtk
import ipdb



class MouseInteractorPickCell(vtk.vtkInteractorStyleTrackballCamera):
    def __init__(self, polyData, viewer):
        self.AddObserver("LeftButtonPressEvent", self.leftButtonPressEvent)
        self.polyData = polyData
        self.viewer = viewer

    def leftButtonPressEvent(self, obj, event):
        clickPos = self.GetInteractor().GetEventPosition()

        picker = vtk.vtkCellPicker()
        picker.SetTolerance(0.0005)
        picker.Pick(clickPos[0], clickPos[1], 0, self.GetDefaultRenderer())

        # Get the cell
        cellId = picker.GetCellId()
        
        if (cellId != -1):
            ids = vtk.vtkIdTypeArray()
            ids.SetNumberOfComponents(1)
            ids.InsertNextValue(cellId)        

            self.viewer.update(ids)

        self.OnLeftButtonDown()



class MouseInteractorHighLightCell(vtk.vtkInteractorStyleTrackballCamera):
    def __init__(self, polyData, expandAlgorithm=None):
        self.AddObserver("LeftButtonPressEvent", self.leftButtonPressEvent)
        self.selectedMapper = vtk.vtkDataSetMapper()
        self.selectedActor = vtk.vtkActor()
        self.polyData = polyData
        self.expandAlgorithm = expandAlgorithm

    def leftButtonPressEvent(self, obj, event):
        clickPos = self.GetInteractor().GetEventPosition()

        picker = vtk.vtkCellPicker()
        picker.SetTolerance(0.0005)
        picker.Pick(clickPos[0], clickPos[1], 0, self.GetDefaultRenderer())

        # Get the cell
        cellId = picker.GetCellId()
        if (cellId != -1):
            ids = vtk.vtkIdTypeArray()
            ids.SetNumberOfComponents(1)
            ids.InsertNextValue(cellId)

            if self.expandAlgorithm is not None:
                new_ids = self.expandAlgorithm(self.polyData, ids)

            selectionNode = vtk.vtkSelectionNode()
            selectionNode.SetFieldType(vtk.vtkSelectionNode.CELL)
            selectionNode.SetContentType(vtk.vtkSelectionNode.INDICES)
            selectionNode.SetSelectionList(new_ids)

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

            self.GetInteractor().GetRenderWindow().GetRenderers(
            ).GetFirstRenderer().AddActor(self.selectedActor)
        
        self.OnLeftButtonDown()


if __name__ == '__main__':

    # create a sphere source, mapper, and actor
    sphere = vtk.vtkSphereSource()
    sphere.Update()
    shperePolyData = sphere.GetOutput()
    sphereMapper = vtk.vtkPolyDataMapper()
    sphereMapper.SetInputData(shperePolyData)
    sphereActor = vtk.vtkLODActor()
    sphereActor.SetMapper(sphereMapper)

    # Create the Renderer, RenderWindow, etc. and set the Picker.
    ren = vtk.vtkRenderer()
    renWin = vtk.vtkRenderWindow()
    renWin.AddRenderer(ren)
    iren = vtk.vtkRenderWindowInteractor()
    iren.SetRenderWindow(renWin)

    # add the custom style
    style = MouseInteractorHighLightCell(shperePolyData)
    style.SetDefaultRenderer(ren)
    iren.SetInteractorStyle(style)

    # Add the actors to the renderer, set the background and size
    ren.AddActor(sphereActor)
    ren.SetBackground(1, 1, 1)
    renWin.SetSize(300, 300)

    # Get the camera and zoom in closer to the image.
    ren.ResetCamera()
    cam1 = ren.GetActiveCamera()
    cam1.Zoom(1.4)

    iren.Initialize()
    # Initially pick the cell at this location.
    renWin.Render()
    iren.Start()