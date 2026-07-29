import bpy

obj = bpy.context.active_object
if obj and obj.type == 'ARMATURE':
    try:
        bone = obj.pose.bones[0]
        # Test if bone.keyframe_insert succeeds on an empty action
        res = bone.keyframe_insert('location')
        print(f"BONE KEYFRAME INSERT RES: {res}")
        if not obj.animation_data.action.fcurves:
            print("NO FCURVES CREATED!")
        else:
            print("FCURVES CREATED SUCCESSFULLY!")
    except Exception as e:
        print(f"ERROR: {e}")
