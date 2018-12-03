import vtk

def showMeshWithPointScalar(mesh, value_title='Distance'):
    """Show a mesh with point scalars and scalarBar.

    Args: 
        mesh (vtkPolyData): mesh model with scalars.
        value_title (str): Title for the value.
    """
    renderer = vtk.vtkRenderer()
    renWin = vtk.vtkRenderWindow()
    renWin.AddRenderer(renderer)

    renWinInteractor = vtk.vtkRenderWindowInteractor()
    renWinInteractor.SetRenderWindow(renWin)

    mapper = vtk.vtkPolyDataMapper()
    mapper.SetInputData(mesh)
    mapper.SetScalarModeToUsePointData()

    actor = vtk.vtkActor()
    actor.SetMapper(mapper)
    renderer.AddActor(actor)

    scalarBar = vtk.vtkScalarBarActor()
    scalarBar.SetLookupTable(mapper.GetLookupTable())
    scalarBar.SetTitle(value_title)
    scalarBar.SetNumberOfLabels(4)

    renderer.AddActor2D(scalarBar)

    renWin.Render()
    renWinInteractor.Start()