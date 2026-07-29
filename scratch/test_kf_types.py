import bpy

obj = bpy.context.active_object
if obj and obj.type == 'ARMATURE':
    try:
        res = bpy.ops.anim.keyframe_insert(type='LocRotScale')
        print(f"Result LocRotScale: {res}")
    except Exception as e:
        print(f"Error LocRotScale: {e}")
        
    try:
        res = bpy.ops.anim.keyframe_insert(type='BUILTIN_KSI_LocRotScale')
        print(f"Result BUILTIN_KSI_LocRotScale: {res}")
    except Exception as e:
        print(f"Error BUILTIN_KSI_LocRotScale: {e}")
