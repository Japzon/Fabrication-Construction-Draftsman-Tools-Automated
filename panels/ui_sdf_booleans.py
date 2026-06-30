import bpy

from . import ui_common

class LSD_PT_SDF_Booleans:
    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        return context.scene.lsd_panel_enabled_sdf_booleans

    @staticmethod
    def draw(layout: bpy.types.UILayout, context: bpy.types.Context):
        box, is_expanded = ui_common.draw_panel_header(layout, context, "SDF Booleans", "lsd_show_panel_sdf_booleans", "lsd_panel_enabled_sdf_booleans")
        if not is_expanded:
            return

        obj = context.active_object
        if not obj:
            box.label(text="Please select an object")
            return
            
        selected = [o for o in context.selected_objects if o != obj]
        props = obj.lsd_pg_sdf_props
        
        # Quick Setup Workflow
        if len(selected) > 0:
            cutter = selected[0]
            setup_box = box.box()
            setup_box.label(text=f"Base: {obj.name}", icon='MESH_CUBE')
            setup_box.label(text=f"Cutter: {cutter.name}", icon='MESH_CYLINDER')
            setup_box.separator()
            setup_box.label(text="Select Operation:")
            
            row = setup_box.row()
            op_union = row.operator("lsd.quick_sdf_boolean", text="Union")
            op_union.operation = 'UNION'
            op_diff = row.operator("lsd.quick_sdf_boolean", text="Difference")
            op_diff.operation = 'DIFFERENCE'
            op_int = row.operator("lsd.quick_sdf_boolean", text="Intersect")
            op_int.operation = 'INTERSECT'
            return

        has_sdf = bool(props.target_object) or (obj.modifiers.get("LSD_SDF_Boolean") is not None)
        
        if not has_sdf:
            info_box = box.box()
            info_box.label(text="SDF Boolean Setup:", icon='INFO')
            info_box.label(text="1. Select Cutter object")
            info_box.label(text="2. Shift-Select Base object")
            info_box.label(text="3. Click an operation button")
            
            box.separator()
            box.prop(props, "target_object", text="Manual Target")
            return
            
        # Active Management Workflow
        sdf_box = box.box()
        sdf_box.label(text="Active SDF Blending:", icon='MOD_BOOLEAN')
        sdf_box.prop(props, "operation", text="Operation")
        sdf_box.prop(props, "blend_distance", text="Smooth Radius")
        sdf_box.prop(props, "voxel_size", text="Resolution (Size)")
        
        row = box.row(align=True)
        row.prop(props, "target_object", text="Cutter")
        if props.target_object:
            vis_icon = 'RESTRICT_VIEW_OFF' if props.target_object.display_type != 'BOUNDS' else 'RESTRICT_VIEW_ON'
            row.operator("lsd.toggle_cutter_visibility", text="", icon=vis_icon)

def register():
    pass

def unregister():
    pass
