# gmsh_convert.py

import gmsh
import sys

input_stl_path = sys.argv[1]
output_msh_path = sys.argv[2]

gmsh.initialize()
gmsh.option.setNumber("General.Terminal", 1)
gmsh.option.setNumber("Mesh.MshFileVersion", 2.2)  # ✅ force Gmsh 2.2 format

gmsh.model.add("TetraMesh")

# Merge STL surface
gmsh.merge(input_stl_path)

# Classify surface
angle = 40
force_parametrizable_patches = True
include_boundary = True
curve_angle = 180

gmsh.model.mesh.classifySurfaces(angle, include_boundary,
                                 force_parametrizable_patches,
                                 curve_angle)

# Generate tetrahedral volume mesh
gmsh.model.mesh.createGeometry()
gmsh.model.mesh.generate(3)

gmsh.write(output_msh_path)
gmsh.finalize()
