import bpy
from . import ui_common

class LSD_UL_Animation_Layers(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        layer = item
        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            row = layout.row(align=True)
            row.label(text="", icon='SOLO_ON' if index == active_data.active_layer_index else 'SOLO_OFF')
            row.prop(layer, "name", text="", emboss=False, icon_value=icon)
            
            # Additional layer info
            if layer.blend_type == 'REPLACE':
                row.label(text="R")
            else:
                row.label(text="C")
                
            
            if layer.is_muted:
                row.prop(layer, "is_muted", text="", icon='HIDE_ON', emboss=False)
            else:
                row.prop(layer, "is_muted", text="", icon='HIDE_OFF', emboss=False)
                
            row.prop(layer, "is_locked", text="", icon='LOCKED' if layer.is_locked else 'UNLOCKED', emboss=False)
        elif self.layout_type == 'GRID':
            layout.alignment = 'CENTER'
            layout.label(text="", icon_value=icon)

class LSD_PT_Animation_System_Main:
    @staticmethod
    def poll(context):
        return context.scene.lsd_panel_enabled_animation

    @staticmethod
    def draw(layout, context):
        box, is_expanded = ui_common.draw_panel_header(
            layout, context,
            "Animation Layers System",
            "lsd_show_panel_animation",
            "lsd_panel_enabled_animation"
        )
        if is_expanded:
            col_main = box.column(align=True)
            settings = context.scene.lsd_anim_settings
            
            # --- Animation Layers Subpanel ---
            layers_box = col_main.box()
            row = layers_box.row()
            row.prop(settings, "layers_enabled", text="", icon='TRIA_DOWN' if settings.layers_enabled else 'TRIA_RIGHT', emboss=False)
            row.label(text="Animation Layers")
            row.prop(settings, "layers_enabled", text="", icon='CHECKBOX_HLT' if settings.layers_enabled else 'CHECKBOX_DEHLT')
            
            if settings.layers_enabled:
                col = layers_box.column(align=True)
                row = col.row()
                row.template_list("LSD_UL_Animation_Layers", "", settings, "layers", settings, "active_layer_index", rows=4)
                
                col_btn = row.column(align=True)
                col_btn.operator("lsd.anim_layer_add", icon='ADD', text="")
                col_btn.operator("lsd.anim_layer_remove", icon='REMOVE', text="")
                col_btn.separator()
                op_up = col_btn.operator("lsd.anim_layer_move", icon='TRIA_UP', text="")
                op_up.direction = 'UP'
                op_down = col_btn.operator("lsd.anim_layer_move", icon='TRIA_DOWN', text="")
                op_down.direction = 'DOWN'
                
                if len(settings.layers) > 0 and settings.active_layer_index >= 0:
                    layer = settings.layers[settings.active_layer_index]
                    col.prop(layer, "influence", text="Influence")
                    col.prop(layer, "blend_type", text="Blend:")
                
                bake_box = col.box()
                row = bake_box.row()
                row.alignment = 'LEFT'
                row.prop(settings, "show_bake_operators", text="", icon='TRIA_DOWN' if settings.show_bake_operators else 'TRIA_RIGHT', emboss=False)
                row.label(text="Bake Operators")
                
                if settings.show_bake_operators:
                    bake_col = bake_box.column(align=True)
                    bake_col.operator("lsd.anim_merge_bake", text="Merge / Bake", icon='ACTION_TWEAK')
                    bake_col.operator("lsd.anim_duplicate_layer", text="Duplicate Layer", icon='DUPLICATE')
                    bake_col.operator("lsd.anim_extract_bones", text="Extract Selected Bones", icon='BONE_DATA')
                    bake_col.operator("lsd.anim_extract_keys", text="Extract Marked Keyframes", icon='KEYINGSET')
            
            # --- Layer Tools Subpanel ---
            if settings.layers_enabled:
                tools_box = col_main.box()
                row = tools_box.row()
                row.label(text="Layer Tools", icon='TOOL_SETTINGS')
                
                col = tools_box.column()
                col.operator("lsd.anim_select_bones", text="Select Bones in Layer", icon='BONE_DATA')
                
                row = col.row()
                row.prop(settings, "affect_selected_bones_only", text="Affect Only Selected Bones")
                row.label(icon='FILTER')
                
                col.operator("lsd.anim_reset_key_layer", text="Reset Key Layer", icon='KEYTYPE_KEYFRAME_VEC')
                col.prop(settings, "inbetween_value", text="Inbetween")
                
                row = col.row()
                row.label(text="Share Layer Keys")
                row.prop(settings, "share_layer_keys_type", text="")
                
                mk_box = col.box()
                mk_box.label(text="Multikey - Edit Multiple Keyframes")
                row = mk_box.row()
                row.prop(settings, "multikey_scale", text="Scale")
                row.prop(settings, "multikey_random", text="Random")
                mk_box.operator("lsd.anim_multikey_edit", text="Edit Selected Keyframes", icon='NODE_COMPOSITING')
                
                row = col.row(align=True)
                row.operator("lsd.anim_cyclic_fcurves", text="Cyclic Fcurves", icon='GRAPH')
                row.operator("lsd.anim_remove_fcurves", text="X Remove Fcurves")
                
                col.prop(settings, "view_multiple_layer_keyframes", text="View Multiple Layer Keyframes")
                row = col.row()
                row.prop(settings, "edit_type_toggle", text="Edit")
                row.prop(settings, "edit_type", text="")
                
            # --- Layer Settings Subpanel ---
            if settings.layers_enabled:
                settings_box = col_main.box()
                row = settings_box.row()
                row.label(text="Layer Settings", icon='PREFERENCES')
                
                col = settings_box.column()
                row = col.row()
                row.label(text="Active A...")
                row.prop(settings, "active_action", text="", icon='ACTION')
                
                row = col.row()
                row.prop(settings, "sync_layer_action", text="Sync Layer/Actio...")
                row.prop(settings, "auto_blend", text="Auto Blend")
                
                col.operator("lsd.anim_custom_frame_range", text="Custom Frame Range", icon='TRIA_LEFT')
                
                row = col.row()
                row.prop(settings, "frame_min", text="")
                row.prop(settings, "frame_max", text="")
                row.prop(settings, "frame_range_type", text="")
                
                row = col.row()
                col1 = row.column(align=True)
                col1.prop(settings, "always_sync", text="Always Sync")
                col1.prop(settings, "reversed", text="Reversed")
                
                col2 = row.column()
                col2.operator("lsd.anim_sync_to_action", text="Sync to Action", icon='FILE_REFRESH')
                row2 = col2.row(align=True)
                row2.prop(settings, "repeat", text="Repeat")
                row2.prop(settings, "offset", text="Offset")
                
                row = col.row(align=True)
                col1 = row.column()
                col1.prop(settings, "speed", text="Speed")

CLASSES = (
    LSD_UL_Animation_Layers,
)

def register():
    for cls in CLASSES:
        bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(CLASSES):
        bpy.utils.unregister_class(cls)
