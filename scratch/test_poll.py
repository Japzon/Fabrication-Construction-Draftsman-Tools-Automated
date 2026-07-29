import bpy
for window in bpy.context.window_manager.windows:
    screen = window.screen
    for area in screen.areas:
        if area.type == 'VIEW_3D':
            for region in area.regions:
                if region.type == 'WINDOW':
                    obj = bpy.context.active_object
                    override = {'window': window, 'screen': screen, 'area': area, 'region': region, 'active_object': obj, 'object': obj}
                    with bpy.context.temp_override(**override):
                        print("POLL keyframe_insert:", bpy.ops.anim.keyframe_insert.poll())
                    break
            break
