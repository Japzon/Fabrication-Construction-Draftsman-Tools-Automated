import bpy
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.mesh.primitive_cube_add(size=2)
cube = bpy.context.active_object
vg = cube.vertex_groups.new(name="TestVG")
vg.add([0, 1, 2, 3], 1.0, 'REPLACE')
hooked = set()
for v in cube.data.vertices:
    try:
        if vg.weight(v.index) > 0.5:
            hooked.add(v.index)
    except Exception as e:
        pass
print("Hooked:", hooked)
