import bpy

def test_keyframe():
    obj = bpy.context.active_object
    if not obj or obj.type != 'ARMATURE':
        print("No armature selected")
        return
        
    for window in bpy.context.window_manager.windows:
        screen = window.screen
        for area in screen.areas:
            if area.type == 'VIEW_3D':
                for region in area.regions:
                    if region.type == 'WINDOW':
                        override = {'window': window, 'screen': screen, 'area': area, 
                                    'region': region, 'active_object': obj, 'object': obj}
                        with bpy.context.temp_override(**override):
                            print("Running keyframe_insert(type='LocRotScale')...")
                            try: 
                                res = bpy.ops.anim.keyframe_insert(type='LocRotScale')
                                print(f"Result: {res}")
                            except Exception as e: 
                                print(f"Error LocRotScale: {e}")
                                
                            print("Running keyframe_insert(type='Available')...")
                            try: 
                                res = bpy.ops.anim.keyframe_insert(type='Available')
                                print(f"Result: {res}")
                            except Exception as e: 
                                print(f"Error Available: {e}")
                        return

test_keyframe()
