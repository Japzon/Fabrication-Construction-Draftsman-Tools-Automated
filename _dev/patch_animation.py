import os

base_dir = r"c:\Users\japzo\OneDrive\Desktop\Blender Add-on Workshop\Layouts-Systems-Draftsman-Toolkit-Addon"
properties_path = os.path.join(base_dir, "properties.py")
operators_path = os.path.join(base_dir, "operators.py")

props_code = """
class LSD_PG_Animation_Layer(bpy.types.PropertyGroup):
    name: bpy.props.StringProperty(name="Name", default="Anim_Layer")
    blend_type: bpy.props.EnumProperty(
        name="Blend Type",
        items=[('REPLACE', "Replace", ""), ('COMBINE', "Combine", "")]
    )
    influence: bpy.props.FloatProperty(name="Influence", default=1.0, min=0.0, max=1.0)
    is_visible: bpy.props.BoolProperty(name="Visible", default=True)
    is_locked: bpy.props.BoolProperty(name="Locked", default=False)

class LSD_PG_Animation_Settings(bpy.types.PropertyGroup):
    layers_enabled: bpy.props.BoolProperty(name="Turn Animation Layers On", default=False)
    layers: bpy.props.CollectionProperty(type=LSD_PG_Animation_Layer)
    active_layer_index: bpy.props.IntProperty(default=-1)
    show_bake_operators: bpy.props.BoolProperty(default=True)
    
    affect_selected_bones_only: bpy.props.BoolProperty(default=False)
    inbetween_value: bpy.props.FloatProperty(default=0.8, min=0.0, max=1.0)
    share_layer_keys_type: bpy.props.EnumProperty(items=[('RUN', "Run", "")])
    
    multikey_scale: bpy.props.FloatProperty(default=1.0)
    multikey_random: bpy.props.FloatProperty(default=0.1)
    
    view_multiple_layer_keyframes: bpy.props.BoolProperty(default=True)
    edit_type_toggle: bpy.props.BoolProperty(default=True)
    edit_type: bpy.props.EnumProperty(items=[('TYPE', "Type", "")])
    
    active_action: bpy.props.PointerProperty(type=bpy.types.Action)
    sync_layer_action: bpy.props.BoolProperty(default=True)
    auto_blend: bpy.props.BoolProperty(default=True)
    
    frame_min: bpy.props.FloatProperty(default=0.0)
    frame_max: bpy.props.FloatProperty(default=122.0)
    frame_range_type: bpy.props.EnumProperty(items=[('NOTHING', "Nothing", "")])
    
    always_sync: bpy.props.BoolProperty(default=False)
    reversed: bpy.props.BoolProperty(default=False)
    repeat: bpy.props.FloatProperty(default=1.0)
    offset: bpy.props.FloatProperty(default=0.0)
    speed: bpy.props.FloatProperty(default=1.0)
"""

props_register_code = """
    bpy.utils.register_class(LSD_PG_Animation_Layer)
    bpy.utils.register_class(LSD_PG_Animation_Settings)
    bpy.types.Scene.lsd_anim_settings = bpy.props.PointerProperty(type=LSD_PG_Animation_Settings)
"""

props_unregister_code = """
    if hasattr(bpy.types.Scene, "lsd_anim_settings"):
        del bpy.types.Scene.lsd_anim_settings
    try:
        bpy.utils.unregister_class(LSD_PG_Animation_Settings)
        bpy.utils.unregister_class(LSD_PG_Animation_Layer)
    except: pass
"""

with open(properties_path, "r", encoding="utf-8") as f:
    content = f.read()

if "LSD_PG_Animation_Layer" not in content:
    content = content.replace("CLASSES = (", props_code + "\nCLASSES = (")
    content = content.replace("    for cls in CLASSES:", props_register_code + "\n    for cls in CLASSES:")
    content = content.replace("    for cls in reversed(CLASSES):", props_unregister_code + "\n    for cls in reversed(CLASSES):")

    with open(properties_path, "w", encoding="utf-8") as f:
        f.write(content)

ops_code = """
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


class LSD_OT_Anim_Layer_Add(bpy.types.Operator):
    bl_idname = "lsd.anim_layer_add"
    bl_label = "Add Animation Layer"
    def execute(self, context):
        settings = context.scene.lsd_anim_settings
        layer = settings.layers.add()
        layer.name = "Anim_Layer"
        if settings.active_layer_index >= 0 and settings.active_layer_index < len(settings.layers) - 1:
            active_layer = settings.layers[settings.active_layer_index]
            layer.blend_type = active_layer.blend_type
        settings.active_layer_index = len(settings.layers) - 1
        return {'FINISHED'}

class LSD_OT_Anim_Layer_Remove(bpy.types.Operator):
    bl_idname = "lsd.anim_layer_remove"
    bl_label = "Remove Animation Layer"
    def execute(self, context):
        settings = context.scene.lsd_anim_settings
        if settings.active_layer_index >= 0 and settings.active_layer_index < len(settings.layers):
            settings.layers.remove(settings.active_layer_index)
            settings.active_layer_index = max(0, settings.active_layer_index - 1)
        return {'FINISHED'}

class LSD_OT_Anim_Layer_Move(bpy.types.Operator):
    bl_idname = "lsd.anim_layer_move"
    bl_label = "Move Animation Layer"
    direction: bpy.props.EnumProperty(items=[('UP', "Up", ""), ('DOWN', "Down", "")])
    def execute(self, context):
        settings = context.scene.lsd_anim_settings
        idx = settings.active_layer_index
        if self.direction == 'UP' and idx > 0:
            settings.layers.move(idx, idx - 1)
            settings.active_layer_index -= 1
        elif self.direction == 'DOWN' and idx < len(settings.layers) - 1:
            settings.layers.move(idx, idx + 1)
            settings.active_layer_index += 1
        return {'FINISHED'}

class LSD_OT_Anim_Merge_Bake(bpy.types.Operator):
    bl_idname = "lsd.anim_merge_bake"
    bl_label = "Merge / Bake"
    def execute(self, context): return {'FINISHED'}

class LSD_OT_Anim_Duplicate_Layer(bpy.types.Operator):
    bl_idname = "lsd.anim_duplicate_layer"
    bl_label = "Duplicate Layer"
    def execute(self, context): return {'FINISHED'}

class LSD_OT_Anim_Extract_Bones(bpy.types.Operator):
    bl_idname = "lsd.anim_extract_bones"
    bl_label = "Extract Selected Bones"
    def execute(self, context): return {'FINISHED'}

class LSD_OT_Anim_Extract_Keys(bpy.types.Operator):
    bl_idname = "lsd.anim_extract_keys"
    bl_label = "Extract Marked Keyframes"
    def execute(self, context): return {'FINISHED'}

class LSD_OT_Anim_Select_Bones(bpy.types.Operator):
    bl_idname = "lsd.anim_select_bones"
    bl_label = "Select Bones in Layer"
    def execute(self, context): return {'FINISHED'}

class LSD_OT_Anim_Reset_Key_Layer(bpy.types.Operator):
    bl_idname = "lsd.anim_reset_key_layer"
    bl_label = "Reset Key Layer"
    def execute(self, context): return {'FINISHED'}

class LSD_OT_Anim_Multikey_Edit(bpy.types.Operator):
    bl_idname = "lsd.anim_multikey_edit"
    bl_label = "Edit Selected Keyframes"
    def execute(self, context): return {'FINISHED'}

class LSD_OT_Anim_Cyclic_Fcurves(bpy.types.Operator):
    bl_idname = "lsd.anim_cyclic_fcurves"
    bl_label = "Cyclic Fcurves"
    def execute(self, context): return {'FINISHED'}

class LSD_OT_Anim_Remove_Fcurves(bpy.types.Operator):
    bl_idname = "lsd.anim_remove_fcurves"
    bl_label = "Remove Fcurves"
    def execute(self, context): return {'FINISHED'}

class LSD_OT_Anim_Custom_Frame_Range(bpy.types.Operator):
    bl_idname = "lsd.anim_custom_frame_range"
    bl_label = "Custom Frame Range"
    def execute(self, context): return {'FINISHED'}

class LSD_OT_Anim_Sync_To_Action(bpy.types.Operator):
    bl_idname = "lsd.anim_sync_to_action"
    bl_label = "Sync to Action"
    def execute(self, context): return {'FINISHED'}

"""

ops_register_code = """
    LSD_OT_Sync_Active_Layer,
    LSD_OT_Anim_Layer_Add,
    LSD_OT_Anim_Layer_Remove,
    LSD_OT_Anim_Layer_Move,
    LSD_OT_Anim_Merge_Bake,
    LSD_OT_Anim_Duplicate_Layer,
    LSD_OT_Anim_Extract_Bones,
    LSD_OT_Anim_Extract_Keys,
    LSD_OT_Anim_Select_Bones,
    LSD_OT_Anim_Reset_Key_Layer,
    LSD_OT_Anim_Multikey_Edit,
    LSD_OT_Anim_Cyclic_Fcurves,
    LSD_OT_Anim_Remove_Fcurves,
    LSD_OT_Anim_Custom_Frame_Range,
    LSD_OT_Anim_Sync_To_Action,
"""

with open(operators_path, "r", encoding="utf-8") as f:
    op_content = f.read()

if "LSD_OT_Sync_Active_Layer" not in op_content:
    op_content = op_content.replace("CLASSES = (", ops_code + "\nCLASSES = (\n" + ops_register_code)
    with open(operators_path, "w", encoding="utf-8") as f:
        f.write(op_content)

print("Patch applied successfully.")
