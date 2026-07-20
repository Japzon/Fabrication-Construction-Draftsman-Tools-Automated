import os

base_dir = r"c:\Users\japzo\OneDrive\Desktop\Blender Add-on Workshop\Layouts-Systems-Draftsman-Toolkit-Addon"
patch_path = os.path.join(base_dir, "_dev", "patch_animation.py")

sync_op_code = '''
class LSD_OT_Sync_Active_Layer(bpy.types.Operator):
    bl_idname = "lsd.sync_active_layer"
    bl_label = "Sync Layers"
    bl_options = {'INTERNAL'}
    
    _is_syncing = False
    _timer = None
    _state = 0
    _original_area_type = 'VIEW_3D'
    _target_area = None

    def finish(self, context):
        LSD_OT_Sync_Active_Layer._is_syncing = False
        if getattr(self, '_timer', None):
            context.window_manager.event_timer_remove(self._timer)
            self._timer = None
        if hasattr(self, "_original_area_type") and getattr(self, "_target_area", None):
            try:
                self._target_area.type = self._original_area_type
            except: pass

    def modal(self, context, event):
        from . import anim_core
        if event.type == 'TIMER':
            if LSD_OT_Sync_Active_Layer._is_syncing:
                return {'PASS_THROUGH'}

            if self._state == 0:
                LSD_OT_Sync_Active_Layer._is_syncing = True
                anim_core.execute_sync_logic(context)
                self._state = 1
                return {'PASS_THROUGH'}
                
            elif self._state == 1:
                # Find an area to temporarily switch to NLA_EDITOR
                for area in context.screen.areas:
                    if area.type == 'VIEW_3D':
                        self._target_area = area
                        self._original_area_type = area.type
                        area.type = 'NLA_EDITOR'
                        break
                self._state = 2
                return {'PASS_THROUGH'}

            elif self._state == 2:
                try:
                    if self._target_area:
                        with context.temp_override(area=self._target_area):
                            bpy.ops.nla.tweakmode_enter(isolate_action=True)
                except Exception as e:
                    print("Tweakmode enter failed:", e)
                
                self.finish(context)
                return {'FINISHED'}

        return {'PASS_THROUGH'}

    def invoke(self, context, event):
        wm = context.window_manager
        self._timer = wm.event_timer_add(0.01, window=context.window)
        wm.modal_handler_add(self)
        return {'RUNNING_MODAL'}
'''

with open(patch_path, "r", encoding="utf-8") as f:
    content = f.read()

if "LSD_OT_Sync_Active_Layer" not in content:
    # Insert before ops_register_code
    content = content.replace("ops_register_code =", sync_op_code + "\nops_register_code =")
    content = content.replace("LSD_OT_Anim_Layer_Add,", "LSD_OT_Sync_Active_Layer,\n    LSD_OT_Anim_Layer_Add,")
    with open(patch_path, "w", encoding="utf-8") as f:
        f.write(content)
    print("Injected Sync_Active_Layer into patch_animation.py")
else:
    print("Already in patch_animation.py")
