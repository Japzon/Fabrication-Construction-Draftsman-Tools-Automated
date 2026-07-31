import bpy
from . import ui_common

class LSD_UL_Anim_Library(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            row = layout.row()
            row.label(text=item.name, icon='ACTION')

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
            
            # --- Animation Library Subpanel ---
            if hasattr(settings, "library_items"):
                lib_box = col_main.box()
                header_row = lib_box.row()
                header_row.label(text="Animation Layer Library", icon='ASSET_MANAGER')
                
                # Add custom directory selector operator
                dir_row = header_row.row(align=True)
                dir_row.operator("lsd.anim_library_select_dir", icon='FILE_FOLDER', text="")
                
                header_row.operator("lsd.anim_library_update_preview", icon='FILE_REFRESH', text="")
                
                lib_box.prop(settings, "preview_capture_interval")
                
                col = lib_box.column(align=True)
                row = col.row()
                row.template_list("LSD_UL_Anim_Library", "", settings, "library_items", settings, "active_library_index", rows=4)
                
                col_btn = row.column(align=True)

                col_btn.operator("lsd.anim_library_export", icon='EXPORT', text="")
                col_btn.operator("lsd.anim_library_import", icon='IMPORT', text="")
                col_btn.separator()
                col_btn.operator("lsd.anim_library_delete", icon='TRASH', text="")
                
                col.separator()
                col.prop(settings, "import_blend_type", text="Mode")
                
                # Animated Preview
                if len(settings.library_items) > 0 and settings.active_library_index < len(settings.library_items):
                    item = settings.library_items[settings.active_library_index]
                    try:
                        from .. import anim_library
                        icon_id = anim_library.get_animated_icon_id(item.name)
                        if icon_id > 0:
                            box_prev = col.box()
                            row_prev = box_prev.row(align=True)
                            row_prev.template_icon(icon_value=icon_id, scale=6.0)
                    except: pass
                    
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
                col_btn.operator("lsd.anim_layer_move", icon='TRIA_UP', text="").direction = 'UP'
                col_btn.operator("lsd.anim_layer_move", icon='TRIA_DOWN', text="").direction = 'DOWN'
                
                if len(settings.layers) > 0 and settings.active_layer_index >= 0:
                    layer = settings.layers[settings.active_layer_index]
                    
                    row = col.row(align=True)
                    row.prop(layer, "blend_type", text="Blend")
                    
                col.separator()
                col.operator("lsd.anim_keyframe_entire_pose", icon='KEYINGSET')
                
                col.separator()
                box = col.box()
                box.label(text="Snap to Frame with Keyframes", icon='SNAP_ON')
                row = box.row(align=True)
                op_past = row.operator("lsd.snap_to_keyframe", text="Snap to Nearest Past Keyframe", icon='TRIA_LEFT')
                op_past.direction = 'PAST'
                op_future = row.operator("lsd.snap_to_keyframe", text="Snap to Nearest Future Keyframe", icon='TRIA_RIGHT')
                op_future.direction = 'FUTURE'
            
            # --- Onion Skinning Subpanel ---
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
                col.prop(settings, "onion_skin_delete_outer_keyframes")
                
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
                row.prop(settings, "onion_skin_keyframe_filter", text="")
                
                row = col.row(align=True)
                row.prop(settings, "onion_skin_show_past", text="", icon='CHECKBOX_HLT' if getattr(settings, 'onion_skin_show_past', True) else 'CHECKBOX_DEHLT')
                row.prop(settings, "onion_skin_color_past", text="")
                row.prop(settings, "onion_skin_show_present", text="", icon='CHECKBOX_HLT' if getattr(settings, 'onion_skin_show_present', False) else 'CHECKBOX_DEHLT')
                row.prop(settings, "onion_skin_color_present", text="")
                row.prop(settings, "onion_skin_color_present_2", text="")
                row.prop(settings, "onion_skin_show_future", text="", icon='CHECKBOX_HLT' if getattr(settings, 'onion_skin_show_future', True) else 'CHECKBOX_DEHLT')
                row.prop(settings, "onion_skin_color_future", text="")

CLASSES = (
    LSD_UL_Anim_Library,
    LSD_UL_Animation_Layers,
)

def register():
    for cls in CLASSES:
        bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(CLASSES):
        bpy.utils.unregister_class(cls)
