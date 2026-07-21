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
            row.operator("lsd.anim_refresh_sync", text="", icon='FILE_REFRESH')
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
                    col.prop(layer, "blend_type", text="Blend:")
                
                bake_box = col.box()
                row = bake_box.row()
                row.alignment = 'LEFT'
                row.prop(settings, "show_bake_operators", text="", icon='TRIA_DOWN' if settings.show_bake_operators else 'TRIA_RIGHT', emboss=False)
                row.label(text="Bake Operators")
                
                if settings.show_bake_operators:
                    bake_col = bake_box.column(align=True)
                    bake_col.operator("lsd.anim_merge_bake", text="Merge Layer Above", icon='ACTION_TWEAK')
                    bake_col.operator("lsd.anim_duplicate_layer", text="Duplicate Layer", icon='DUPLICATE')
                    bake_col.operator("lsd.anim_extract_bones", text="Extract Selected Bones", icon='BONE_DATA')
                    bake_col.operator("lsd.anim_extract_keys", text="Extract Marked Keyframes", icon='KEYINGSET')
            
            # --- Onion Skinning Subpanel ---
            if settings.layers_enabled:
                onion_box = col_main.box()
                row = onion_box.row()
                row.prop(settings, "onion_skin_enabled", text="", icon='TRIA_DOWN' if settings.onion_skin_enabled else 'TRIA_RIGHT', emboss=False)
                row.label(text="Timeline Onion Skinning", icon='GHOST_ENABLED')
                row.prop(settings, "onion_skin_enabled", text="", icon='CHECKBOX_HLT' if settings.onion_skin_enabled else 'CHECKBOX_DEHLT')
                
                if settings.onion_skin_enabled:
                    col = onion_box.column()
                    
                    row = col.row()
                    row.operator("lsd.calculate_onion_skin", icon='FILE_REFRESH')
                    
                    row_timer = col.row(align=True)
                    row_timer.prop(settings, "onion_skin_auto_refresh", icon='CHECKBOX_HLT' if settings.onion_skin_auto_refresh else 'CHECKBOX_DEHLT')
                    row_timer.prop(settings, "onion_skin_refresh_interval")
                    
                    col.prop(settings, "onion_skin_target", text="")
                    if settings.onion_skin_target == 'SELECTED':
                        col.prop(settings, "onion_skin_near_count")
                        
                    col.prop(settings, "onion_skin_display_type", text="")
                    if settings.onion_skin_display_type == 'MESH':
                        col.prop(settings, "onion_skin_mesh_resolution")
                        
                    col.prop(settings, "onion_skin_fade")
                    
                    col.separator()
                    col.prop(settings, "onion_skin_frame_distance")
                    
                    row = col.row(align=True)
                    row.prop(settings, "onion_skin_opacity_before", text="Opacity Before")
                    row.prop(settings, "onion_skin_opacity_after", text="Opacity After")
                    
                    row = col.row(align=True)
                    row.prop(settings, "onion_skin_count_before")
                    row.prop(settings, "onion_skin_count_after")
                    
                    col.separator()
                    row = col.row(align=True)
                    row.prop(settings, "onion_skin_color_past", text="")
                    row.prop(settings, "onion_skin_color_present", text="")
                    row.prop(settings, "onion_skin_color_future", text="")

CLASSES = (
    LSD_UL_Animation_Layers,
)

def register():
    for cls in CLASSES:
        bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(CLASSES):
        bpy.utils.unregister_class(cls)
