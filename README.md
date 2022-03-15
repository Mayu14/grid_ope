# Grid_ope
- This is review of the 3d unstructured grid operations.

## Function
1. load vtk file
  - get point structures (3-dimension)
  - get cell structures (only tetra)

2. make information
   1. structures
      1. face
      2. line
   2. relationship
      1. face 2 cell
      2. cell 2 face
      3. line 2 face
      4. face 2 line
      5. line 2 cell
      6. cell 2 line

3. method
   1. get angle
      1. from 2-faces
      2. from 2-lines
   2. get distance
      1. from 2-cells
      2. from 2-faces
      3. from 2-lines
   
4. 