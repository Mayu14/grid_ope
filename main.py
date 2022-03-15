#!/usr/bin/python3
# import pickle
from pathlib import Path
import numpy as np
import re
from itertools import combinations
import gc

class UnstruncturedVTK(object):
    def __init__(self, fname=None):
        version_vtk = ""
        name_vtk = ""
        code_vtk = ""
        type_vtk = ""
        header_points = ""
        number_points = 0
        points = np.zeros(shape=(1, 3), dtype=float)
        header_cells = ""
        number_cells = 0
        cells = np.zeros(shape=(1, 1), dtype=int)
        header_celldata = ""
        number_celldata = 0
        celldatas = np.zeros(shape=(1, 1), dtype=int)

        if fname is not None:
            self.read_vtk(fname)

    def read_vtk(self, fname):
        with open(fname, 'r') as f:
            self.header_vtk = f.readline()
            self.name_vtk = f.readline()
            self.code_vtk = f.readline()
            self.type_vtk = f.readline()

            self.header_points = f.readline()
            self.number_points = int(re.sub('[^0-9]', '', self.header_points))
            self.points = np.zeros(shape=(self.number_points, 3))
            for id in range(self.number_points):
                self.points[id, :] = f.readline().split()

            ___ = f.readline()
            self.header_cells = f.readline()
            self.number_cells = int(self.header_cells.split()[1])

            self.cells = np.zeros(shape=(self.number_cells, 4), dtype=int)
            for id in range(self.number_cells):
                cells = list(map(int, f.readline().split()))
                if cells[0] != 4:
                    raise ValueError(f'This vtkfile {fname} has not only tetra element')
                else:
                    self.cells[id, :] = cells[1:]

            ___ = f.readline()
            self.header_celldata = f.readline()
            self.number_celldata = int(self.header_celldata.split()[1])
            self.celldata = np.zeros(shape=(self.number_celldata, 1), dtype=int)
            for id in range(self.number_celldata):
                self.celldata[id] = f.readline().split()

    def get_point(self):
        if self.number_points == 0:
            raise ValueError("points are not defined, read vtk before using this method")
        return self.points

    def get_cell(self):
        if self.number_cells == 0:
            raise ValueError("cells are not defined, read vtk before using this method")
        return self.cells

class Grid(object):
    def __init__(self, fname=None):
        if not type(fname) is type('string'):
            raise ValueError("please input vtk file name")

        outfile = Path(f'{fname}.pkl')

        if outfile.exists():
            print(f'pickle {outfile} find')
            # pickle.load(open(outfile, 'rb'))

        else:
            print(f'pickle {outfile} does not find')
            vtk = UnstruncturedVTK(fname)

            pts = vtk.get_point()
            cells = vtk.get_cell()
            num_cells = cells.shape[0]
            face_per_cell = cells.shape[1]

            # create face object from cell
            file_faces = Path(f'{fname}_faces.npy')
            file_face2cell = Path(f'{fname}_face2cell.npy')
            file_cell2face = Path(f'{fname}_cell2face.npy')
            if file_faces.exists() and file_face2cell.exists() and file_cell2face.exists():
                faces = np.load(str(file_faces))
                face2cell = np.load(str(file_face2cell))
                cell2face = np.load(str(file_cell2face))
                num_faces = faces.shape[0]

            else:
                tmp_num_faces = face_per_cell*num_cells
                tmp_faces = np.zeros(shape=(tmp_num_faces, 3), dtype=int)
                tmp_face2cell = np.zeros(shape=(tmp_num_faces, 1), dtype=int)
                tmp_cell2face = np.zeros(shape=(num_cells, face_per_cell), dtype=int)
                face_id = 0
                for cell_id, cell in enumerate(cells):
                    for face in combinations(cell, 3):
                        tmp_face2cell[face_id] = cell_id
                        tmp_cell2face[cell_id, face_id % face_per_cell] = face_id
                        tmp_faces[face_id] = sorted(face)
                        face_id += 1

                # remove overlap
                file_re_numbering_face = Path(f'{fname}_re_numbering_face.npy')
                if file_re_numbering_face.exists():
                    re_numbering_face = np.load(str(file_re_numbering_face))
                    num_faces = np.unique(re_numbering_face).shape[0]
                else:
                    re_numbering_face = np.full(shape=(tmp_num_faces, 1), fill_value=-1, dtype=int)
                    new_face_id = 0
                    for face_id1, face1 in enumerate(tmp_faces):
                        if re_numbering_face[face_id1] != -1:
                            continue

                        re_numbering_face[face_id1] = new_face_id
                        for face_id2, face2 in enumerate(tmp_faces):
                            # bubble
                            if face_id1 >= face_id2:
                                continue

                            # if same face
                            if np.all(face1 == face2):
                                re_numbering_face[face_id2] = new_face_id

                        new_face_id += 1

                    np.save(str(file_re_numbering_face), re_numbering_face)
                    num_faces = new_face_id

                # regist face
                faces = np.zeros(shape=(num_faces, 3))
                face2cell = np.full(shape=(num_faces, 2), fill_value=-1, dtype=int)

                for old_face_id, face in enumerate(tmp_faces):
                    new_face_id = re_numbering_face[old_face_id]
                    faces[new_face_id] = face

                    tmp_f2c = tmp_face2cell[old_face_id]
                    if face2cell[new_face_id, 0] == -1:
                        face2cell[new_face_id, 0] = tmp_f2c
                    elif face2cell[new_face_id, 1] == -1:
                        face2cell[new_face_id, 1] = tmp_f2c
                    else:
                        print(face2cell[new_face_id])
                        print(new_face_id)
                        print(old_face_id)
                        raise ValueError

                np.save(str(file_faces), faces)
                np.save(str(file_face2cell), face2cell)

                cell2face = np.zeros(shape=(num_cells, face_per_cell), dtype=int)
                for cell_id, c2f in enumerate(tmp_cell2face):
                    for face_id_in_cell, face_id in enumerate(c2f):
                        cell2face[cell_id, face_id_in_cell] = re_numbering_face[face_id]

                np.save(str(file_cell2face), cell2face)

                del tmp_num_faces, tmp_f2c, tmp_faces, tmp_face2cell, tmp_cell2face, re_numbering_face
                gc.collect()

            # create line object from face
            file_lines = Path(f'{fname}_lines.npy')
            file_line2face = Path(f'{fname}_line2face.npy')
            file_face2line = Path(f'{fname}_face2line.npy')
            if file_lines.exists() and file_line2face.exists() and file_face2line.exists():
                lines = np.load(str(file_lines))
                line2face = np.load(str(file_line2face))
                face2line = np.load(str(file_face2line))
                num_lines = lines.shape[0]

            else:
                line_per_face = 3
                tmp_num_lines = line_per_face * num_faces
                tmp_lines = np.zeros(shape=(tmp_num_lines, 2), dtype=int)
                tmp_line2face = np.zeros(shape=(tmp_num_lines, 1), dtype=int)
                tmp_face2line = np.zeros(shape=(num_faces, line_per_face), dtype=int)
                line_id = 0
                for face_id, face in enumerate(faces):
                    for line in combinations(face, 2):
                        tmp_line2face[line_id] = face_id
                        tmp_face2line[face_id, line_id % line_per_face] = line_id
                        tmp_lines[line_id] = sorted(line)
                        line_id += 1

                # remove overlap
                file_re_numbering_line = Path(f'{fname}_re_numbering_line.npy')
                if file_re_numbering_line.exists():
                    re_numbering_line = np.load(str(file_re_numbering_line))
                    num_lines = np.unique(re_numbering_line).shape[0]

                else:
                    re_numbering_line = np.full(shape=(tmp_num_lines, 1), fill_value=-1, dtype=int)
                    new_line_id = 0
                    for line_id1, line1 in enumerate(tmp_lines):
                        if re_numbering_line[line_id1] != -1:
                            continue

                        re_numbering_line[line_id1] = new_line_id
                        for line_id2, line2 in enumerate(tmp_lines):
                            # bubble
                            if line_id1 >= line_id2:
                                continue

                            # if same line (sorted)
                            if np.all(line1 == line2):
                                re_numbering_line[line_id2] = new_line_id

                        new_line_id += 1

                    np.save(str(file_re_numbering_line), re_numbering_line)
                    num_lines = new_line_id

                # regist line
                lines = np.zeros(shape=(num_lines, 2))

                _, counts = np.unique(re_numbering_line, return_counts=True)
                num_connected_face = np.max(counts)
                line2face = np.full(shape=(num_lines, num_connected_face), fill_value=-1, dtype=int)

                for old_line_id, line in enumerate(tmp_lines):
                    new_line_id = re_numbering_line[old_line_id]
                    lines[new_line_id] = line

                    tmp_l2f = tmp_line2face[old_line_id]
                    i = 0
                    while line2face[new_line_id, i] != -1:
                        i += 1
                    line2face[new_line_id, i] = tmp_l2f

                np.save(str(file_lines), lines)
                np.save(str(file_line2face), line2face)

                face2line = np.zeros(shape=(num_faces, line_per_face), dtype=int)
                for face_id, f2l in enumerate(tmp_face2line):
                    for line_id_in_face, line_id in enumerate(f2l):
                        face2line[face_id, line_id_in_face] = re_numbering_line[line_id]

                np.save(str(file_face2line), face2line)

                del tmp_num_lines, tmp_l2f, tmp_lines, tmp_line2face, tmp_face2line, re_numbering_line
                gc.collect()

            # create cell 2 line object from face
            file_cell2line = Path(f'{fname}_cell2line.npy')
            if file_cell2line.exists():
                cell2line = np.load(str(file_cell2line))
            else:
                cell2line = np.zeros(shape=(num_cells, 6), dtype=int)
                tmp_cell2line = np.zeros(shape=(12), dtype=int)
                for cell_id, cell in enumerate(cells):
                    for face_id_in_cell, face_id in enumerate(cell2face[cell_id]):
                        line_id_in_cell = (face_id_in_cell + 1) * (face_id + 1)
                        tmp_cell2line[line_id_in_cell] = face2line[face_id, face_id_in_cell]

                    cell2line[cell_id] = np.unique(tmp_cell2line)

                np.save(str(file_cell2line), cell2line)

            file_line2cell = Path(f'{fname}_line2cell.npy')
            if file_line2cell.exists():
                line2cell = np.load(str(file_line2cell))
            else:
                pass
            # save to pickle


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    fname = 'IGRID.vtk'
    Grid(fname)

# See PyCharm help at https://www.jetbrains.com/help/pycharm/
