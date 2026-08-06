import bpy

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.mesh.primitive_cube_add(size=2)
cube = bpy.context.active_object

# Dim 1
bpy.ops.object.mode_set(mode='EDIT')
bpy.ops.mesh.select_all(action='DESELECT')
import bmesh
bm = bmesh.from_edit_mesh(cube.data)
bm.faces.ensure_lookup_table()
bm.faces[0].select = True
bm.faces[1].select = True
bmesh.update_edit_mesh(cube.data)

bpy.ops.lsd.add_dimension()

# Check selection state after Dim 1
bpy.ops.object.mode_set(mode='EDIT')
bm = bmesh.from_edit_mesh(cube.data)
selected_faces = [f.index for f in bm.faces if f.select]
print("Selected faces after Dim 1:", selected_faces)

bpy.ops.mesh.select_all(action='DESELECT')
bm.faces.ensure_lookup_table()
bm.faces[2].select = True
bm.faces[3].select = True
bmesh.update_edit_mesh(cube.data)

bpy.ops.lsd.add_dimension()

# Print out constraints and modifiers
for obj in bpy.data.objects:
    if "Hook_Dim" in obj.name:
        for con in obj.constraints:
            print(f"Empty {obj.name} -> {con.target.name if con.target else 'None'}")
            
for mod in cube.modifiers:
    print(f"Cube Mod: {mod.name} -> {mod.object.name if getattr(mod, 'object', None) else 'None'} (VG: {getattr(mod, 'vertex_group', 'None')})")
