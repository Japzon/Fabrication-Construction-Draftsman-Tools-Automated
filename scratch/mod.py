import sys
import re

filepath = r'c:\Users\japzo\OneDrive\Desktop\Blender Add-on Workshop\Layouts-Systems-Draftsman-Toolkit-Addon\generators.py'
with open(filepath, 'r', encoding='utf-8') as f:
    c = f.read()

c = c.replace("vol_mesh.inputs['Adaptivity'].default_value = 0.0", "vol_mesh.inputs['Adaptivity'].default_value = 0.025")
c = c.replace("mesh_bool.operation = props.operation", "mesh_bool.operation = props.operation\n        mesh_bool.solver = 'EXACT'")

pattern = r'    # Apply surface projection if requested.*?if sw: obj\.modifiers\.remove\(sw\)'
replacement = '    sw = obj.modifiers.get("LSD_SDF_Project")\n    if sw: obj.modifiers.remove(sw)'
c = re.sub(pattern, replacement, c, flags=re.DOTALL)

with open(filepath, 'w', encoding='utf-8', newline='\r\n') as f:
    f.write(c)
