import vtk

def readSTL(filename):
    reader = vtk.vtkSTLReader()
    reader.SetFileName(filename)
    reader.Update()

    return reader.GetOutput()

def writeVTP(polyData, filename):
    """Wrtie VTP file.
    
    Args:
        polyData (vtkPolyData): pd to be written.
        filename (str): filename of written file.
    """
    writer = vtk.vtkPolyDataWriter()
    writer.SetFileName(filename)
    writer.SetInputData(polyData)
    writer.Write()