import sys
import re

filepath = r'c:\Users\japzo\OneDrive\Desktop\Blender Add-on Workshop\Layouts-Systems-Draftsman-Toolkit-Addon\generators.py'
with open(filepath, 'r', encoding='utf-8') as f:
    c = f.read()

# Fix the base vanishing by ensuring the volume fills the mesh entirely
c = c.replace("mesh_vol.inputs['Interior Band Width'].default_value = props.blend_distance", "mesh_vol.inputs['Interior Band Width'].default_value = 100.0")

# Revert EXACT solver back to FLOAT (Fast) to fix the extreme lag when moving
c = c.replace("mesh_bool.solver = 'EXACT'", "mesh_bool.solver = 'FLOAT'")

with open(filepath, 'w', encoding='utf-8', newline='\r\n') as f:
    f.write(c)
