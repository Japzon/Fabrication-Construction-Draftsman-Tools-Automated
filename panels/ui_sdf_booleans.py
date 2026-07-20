import bpy
from . import ui_common

class LSD_PT_SDF_Booleans:
    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        return context.scene.lsd_panel_enabled_sdf_booleans

    @staticmethod
    def draw(layout: bpy.types.UILayout, context: bpy.types.Context) -> None:
        box_main, is_expanded = ui_common.draw_panel_header(
            layout, context, "Booleans", 
            "lsd_show_panel_sdf_booleans", "lsd_panel_enabled_sdf_booleans"
        )
        
        if not is_expanded:
            return

        col = box_main.column(align=True)
        obj = context.active_object
        if not obj:
            col.label(text="Please select an object")
            return
            
        props = obj.lsd_pg_sdf_props

        box = col.box()
        box.label(text="Advanced Booleans:", icon='MOD_BOOLEAN')
        box.prop(props, "boolean_operation")
        box.prop(props, "transfer_normals")
        box.prop(props, "outset_thickness")
        box.prop(props, "texture_blur")
        box.prop(props, "bevel_weld_radius")
        
        has_bool = "NM_Boolean" in obj.modifiers
        box.operator("lsd.nm_boolean_pro", text="Remove Boolean" if has_bool else "Boolean", icon='CANCEL' if has_bool else 'ADD')

        box = col.box()
        box.label(text="Surface Integration:", icon='MOD_SHRINKWRAP')
        row = box.row()
        has_proj = "NM_Surface_Project" in obj.modifiers
        row.operator("lsd.nm_surface_project", text="Remove Project" if has_proj else "Surface Project", icon='CANCEL' if has_proj else 'ADD')
        has_ins = "NM_Surface_Insert" in obj.modifiers
        row.operator("lsd.nm_surface_insert", text="Remove Insert" if has_ins else "Surface Insert", icon='CANCEL' if has_ins else 'ADD')

        box = col.box()
        box.label(text="Normal Control:", icon='MOD_NORMALEDIT')
        has_wn = "NM_Weighted_Normal" in obj.modifiers
        box.operator("lsd.nm_normal_weighted", text="Remove Weighted Normals" if has_wn else "Weighted Normals", icon='CANCEL' if has_wn else 'ADD')

        box = col.box()
        box.label(text="Workflow:", icon='MODIFIER')
        box.operator("lsd.nm_apply_modifiers", text="Apply All Modifiers")

def register():
    pass

def unregister():
    pass
