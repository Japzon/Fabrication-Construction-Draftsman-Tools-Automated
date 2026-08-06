import bpy

# Clean up
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.mesh.primitive_cube_add(size=2)
cube = bpy.context.active_object

# Add subsurf to make vertices clear
bpy.ops.object.modifier_add(type='SUBSURF')

# Create first dimension in edit mode
bpy.ops.object.mode_set(mode='EDIT')
bpy.ops.mesh.select_all(action='DESELECT')
import bmesh
bm = bmesh.from_edit_mesh(cube.data)
bm.faces.ensure_lookup_table()
bm.faces[0].select = True
bm.faces[1].select = True
bmesh.update_edit_mesh(cube.data)

try:
    bpy.ops.lsd.add_dimension()
except Exception as e:
    print(f"Error 1: {e}")

# Create second dimension in edit mode
bpy.ops.object.mode_set(mode='EDIT')
bpy.ops.mesh.select_all(action='DESELECT')
bm = bmesh.from_edit_mesh(cube.data)
bm.faces.ensure_lookup_table()
bm.faces[2].select = True
bm.faces[3].select = True
bmesh.update_edit_mesh(cube.data)

try:
    bpy.ops.lsd.add_dimension()
except Exception as e:
    print(f"Error 2: {e}")

print("=== FINAL STATE ===")
# Print out constraints and modifiers
for obj in bpy.data.objects:
    if "Hook_Dim" in obj.name:
        print(f"Empty {obj.name} (Parent: {obj.parent.name if obj.parent else 'None'}):")
        for con in obj.constraints:
            print(f"  Con: {con.name} -> {con.target.name if con.target else 'None'}")
            
print("Cube Modifiers:")
for mod in cube.modifiers:
    print(f"  Mod: {mod.name} -> {mod.object.name if getattr(mod, 'object', None) else 'None'} (VG: {getattr(mod, 'vertex_group', 'None')})")
