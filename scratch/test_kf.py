import bpy

obj = bpy.context.active_object
if obj and obj.type == 'ARMATURE':
    try:
        bpy.ops.anim.keyframe_insert(type='Location')
        print("Location SUCCESS")
    except Exception as e:
        print(f"Location ERROR: {e}")
