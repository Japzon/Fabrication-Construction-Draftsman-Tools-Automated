import bpy

bpy.ops.mesh.primitive_cube_add(size=2, location=(0,0,0))
obj = bpy.context.active_object
obj.scale = (10, 10, 10)
bpy.context.view_layer.update()

base_action = bpy.data.actions.new('Base')
fc_x = base_action.fcurves.new(data_path='location', index=0)
fc_x.keyframe_points.insert(1, 0)
fc_x.keyframe_points.insert(10, 0)

combine_action = bpy.data.actions.new('Combine')
fc_c = combine_action.fcurves.new(data_path='location', index=0)
fc_c.keyframe_points.insert(1, 0)
fc_c.keyframe_points.insert(10, 5)

obj.animation_data_create()
track_base = obj.animation_data.nla_tracks.new()
track_base.name = 'Base Track'
strip_base = track_base.strips.new('Base', 1, base_action)

track_combine = obj.animation_data.nla_tracks.new()
track_combine.name = 'Combine Track'
strip_combine = track_combine.strips.new('Combine', 1, combine_action)
strip_combine.blend_type = 'COMBINE'

bpy.context.scene.frame_set(1)
loc_1 = obj.matrix_world.translation.x
bpy.context.scene.frame_set(10)
loc_10 = obj.matrix_world.translation.x

print('---RESULT---')
print('FRAME 1 LOC_X:', loc_1)
print('FRAME 10 LOC_X:', loc_10)
print('DELTA:', loc_10 - loc_1)
print('---ENDRESULT---')
