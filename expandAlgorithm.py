import vtk
import ipdb
from vtk.util import numpy_support
import numpy as np


def multiThresholdExpand(polyData, ids, distance, angle):
    """ MultiThresholdExpand algorithm.

        Args:
            polyData (vtkPolyData): polydata to be processed.
            ids (vtkIdList): initial Point.
            distance (int): Largest number of cell to be passed through in expansion.
            angle (float): Largest angle difference between inital cell and expanded
                cells.
    """
    cellIds = set([ids.GetValue(i) for i in range(ids.GetNumberOfValues())])
    newCellIds = cellIds

    normals = getNormals(polyData)
    origin_norm = np.mean([normals[id] for id in cellIds], axis=0)

    polyData.BuildLinks()

    for i in range(distance):
        temp_newCellIds = set()
        for cellId in newCellIds:
            cellPointIds = vtk.vtkIdList()
            polyData.GetCellPoints(cellId, cellPointIds)
            for j in range(cellPointIds.GetNumberOfIds()):
                for k in range(j, cellPointIds.GetNumberOfIds()):
                    if polyData.IsEdge(
                            cellPointIds.GetId(j), cellPointIds.GetId(k)):
                        neighborCellIds = vtk.vtkIdList()
                        polyData.GetCellEdgeNeighbors(cellId,
                                                      cellPointIds.GetId(j),
                                                      cellPointIds.GetId(k),
                                                      neighborCellIds)
                        for l in range(neighborCellIds.GetNumberOfIds()):
                            new_id = neighborCellIds.GetId(l)
                            if np.degrees(np.pi - np.arccos(np.sum(normals[new_id] *
                                             origin_norm))) > angle:
                                temp_newCellIds.add(new_id)
        newCellIds = temp_newCellIds - cellIds
        cellIds.update(newCellIds)

    new_ids = vtk.vtkIdTypeArray()
    new_ids.SetNumberOfComponents(1)
    for id in cellIds:
        new_ids.InsertNextValue(id)

    return new_ids


def neighborExpand(polyData, ids, threshold):

    cellIds = set([ids.GetValue(i) for i in range(ids.GetNumberOfValues())])
    newCellIds = cellIds

    for i in range(threshold):
        temp_newCellIds = set()
        for cellId in newCellIds:
            cellPointIds = vtk.vtkIdList()
            polyData.GetCellPoints(cellId, cellPointIds)
            for j in range(cellPointIds.GetNumberOfIds()):
                pointId = vtk.vtkIdList()
                pointId.InsertNextId(cellPointIds.GetId(j))
                neighborCellIds = vtk.vtkIdList()
                polyData.GetCellNeighbors(cellId, pointId, neighborCellIds)
                for k in range(neighborCellIds.GetNumberOfIds()):
                    temp_newCellIds.add(neighborCellIds.GetId(k))
        newCellIds = temp_newCellIds - cellIds
        cellIds.update(newCellIds)

    new_ids = vtk.vtkIdTypeArray()
    new_ids.SetNumberOfComponents(1)
    for id in cellIds:
        new_ids.InsertNextValue(id)

    return new_ids


def angleExpand(polyData, ids, threshold):

    cellIds = set([ids.GetValue(i) for i in range(ids.GetNumberOfValues())])
    newCellIds = cellIds

    normals = getNormals(polyData)
    origin_norm = np.mean([normals[id] for id in cellIds], axis=0)

    polyData.BuildLinks()

    while newCellIds:
        temp_newCellIds = set()
        for cellId in newCellIds:
            cellPointIds = vtk.vtkIdList()
            polyData.GetCellPoints(cellId, cellPointIds)
            for j in range(cellPointIds.GetNumberOfIds()):
                for k in range(j, cellPointIds.GetNumberOfIds()):
                    if polyData.IsEdge(
                            cellPointIds.GetId(j), cellPointIds.GetId(k)):
                        neighborCellIds = vtk.vtkIdList()
                        polyData.GetCellEdgeNeighbors(cellId,
                                                      cellPointIds.GetId(j),
                                                      cellPointIds.GetId(k),
                                                      neighborCellIds)
                        for l in range(neighborCellIds.GetNumberOfIds()):
                            new_id = neighborCellIds.GetId(l)
                            if np.abs(np.sum(normals[new_id] *
                                             origin_norm)) > threshold:
                                temp_newCellIds.add(new_id)
        newCellIds = temp_newCellIds - cellIds
        cellIds.update(newCellIds)

    new_ids = vtk.vtkIdTypeArray()
    new_ids.SetNumberOfComponents(1)
    for id in cellIds:
        new_ids.InsertNextValue(id)

    return new_ids


def getCurvature(polyData):
    curvaturesFilter = vtk.vtkCurvatures()
    curvaturesFilter.SetInputData(polyData)
    curvaturesFilter.SetCurvatureTypeToGaussian()
    curvaturesFilter.Update()

    return curvaturesFilter.GetOutput()


def getNormals(polyData):

    normalFilter = vtk.vtkPolyDataNormals()
    normalFilter.SetInputData(polyData)
    normalFilter.ConsistencyOn()
    normalFilter.ComputeCellNormalsOn()
    normalFilter.Update()
    return numpy_support.vtk_to_numpy(
        normalFilter.GetOutput().GetCellData().GetArray("Normals"))


if __name__ == '__main__':
    import vtkio
    import random
    stl = vtkio.readSTL(r"D:\Data\caseDataArrangedDivided\train\T0001.stl")

    ipdb.set_trace()
