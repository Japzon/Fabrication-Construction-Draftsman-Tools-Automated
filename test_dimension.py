import bpy
import mathutils
import sys
import os

# Add addon path to sys.path so we can import its modules
addon_path = r"C:\Users\japzo\OneDrive\Desktop\Blender Add-on Workshop\Layouts-Systems-Draftsman-Toolkit-Addon"
if addon_path not in sys.path:
    sys.path.append(addon_path)

import core
import operators
import generators

# Clear scene
bpy.ops.wm.read_factory_settings(use_empty=True)
context = bpy.context

# Create a mock object
obj1 = bpy.data.objects.new("UserMesh", None)
context.scene.collection.objects.link(obj1)
obj1.location = (1, 1, 1)

# Mimic LSD_OT_Manually_Draw_Offset_Line
hook1 = bpy.data.objects.new("StartHook", None)
context.scene.collection.objects.link(hook1)
hook1.location = obj1.location
hook1.parent = obj1
hook1.matrix_parent_inverse = obj1.matrix_world.inverted()
hook1["lsd_is_offset_hook"] = "START"

hook2 = bpy.data.objects.new("Offset_EndHook", None)
context.scene.collection.objects.link(hook2)
hook2.location = (1, 1, 5)
hook2["lsd_is_offset_hook"] = "END"

hook1.parent = hook2
hook1.matrix_parent_inverse = hook2.matrix_world.inverted()

line_mesh = generators.create_dimension_line_mesh("Standalone_Offset")
line_obj = bpy.data.objects.new("Standalone_Offset_Line", line_mesh)
context.scene.collection.objects.link(line_obj)
line_obj.parent = hook1
line_obj.location = (0, 0, 0)
line_obj.lsd_is_standalone_offset = True
line_obj.scale.z = (hook2.location - hook1.location).length

con_track = line_obj.constraints.new('TRACK_TO')
con_track.target = hook2
con_track.track_axis = 'TRACK_Z'
con_track.up_axis = 'UP_Y'

# Update depsgraph to lock world matrices
context.view_layer.update()
print(f"BEFORE DIMENSION: hook2 world loc: {hook2.matrix_world.translation}")

# Now mimic generating a dimension between obj1 and hook2
p1_v = obj1.matrix_world.translation.copy()
p2_v = hook2.matrix_world.translation.copy()

# resolve_anchor for obj1 -> should return StartHook
def resolve_anchor(obj, measured_p):
    if obj.type == 'EMPTY' or obj.get("lsd_anchor") or obj.get("lsd_is_dimension_hook") or obj.get("lsd_is_offset_hook"):
        return obj
    if obj.parent and (obj.parent.get("lsd_is_offset_hook") or "StartHook" in obj.parent.name or "Offset_EndHook" in obj.parent.name):
        return obj.parent
    return None

h1 = resolve_anchor(obj1, p1_v)
h2 = resolve_anchor(hook2, p2_v)

print(f"Resolved h1: {h1.name if h1 else 'None'}")
print(f"Resolved h2: {h2.name if h2 else 'None'}")

parent_a = (h1, 'OBJECT', 0)
parent_b = (h2, 'OBJECT', 0)

dim_result = generators.generate_smart_dimension_parametric(context, p1_v, p2_v, parent_a=parent_a, parent_b=parent_b)

context.view_layer.update()
print(f"AFTER DIMENSION: hook2 world loc: {hook2.matrix_world.translation}")
