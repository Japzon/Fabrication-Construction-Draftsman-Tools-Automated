# --------------------------------------------------------------------------------
# Copyright (c) 2026 Greenlex Systems Services Incorporated. All rights reserved.
#
# Licensed under the GNU General Public License (GPL).
# Original Architecture & Logic by Greenlex Systems Services Incorporated.
#
# No person or organization is authorized to misrepresent this work or claim 
# original authorship for themselves. Proper attribution is mandatory.
# --------------------------------------------------------------------------------




import bpy
from . import ui_common

class FCD_PT_Dimensions_And_Measuring:
    """
    Dimensions & Measuring panel.
    Generates parametric mesh-based dimension displays from selected object bounding boxes,
    with adjustable visual properties and precise measurement labels.
    """

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        return getattr(context.scene, "fcd_panel_enabled_dimensions", False)

    @staticmethod
    def draw(layout: bpy.types.UILayout, context: bpy.types.Context) -> None:
        """
        Main drawing logic for the Dimensions toolkit.
        """
        scene = context.scene
        
        # 1. Standardized Header
        box, is_expanded = ui_common.draw_panel_header(
            layout, context, 
            "Dimensions & Measuring", 
            "fcd_show_panel_dimensions", 
            "fcd_panel_enabled_dimensions"
        )
        
        if is_expanded:
            # --- Smart Dimension Generator ---
            gen_box = box.box()
            col = gen_box.column(align=True)
            col.operator("fcd.add_dimension", text="Generate Dimensions for Selected", icon='DRIVER_DISTANCE')
            
            # --- Remove Selected Dimension ---
            active_obj = context.active_object
            is_dim = active_obj and active_obj.get("fcd_is_dimension")
            
            if is_dim:
                col.separator()
                col.operator("fcd.remove_dimension", text="Remove Selected Dimension", icon='TRASH')

            # --- Display Properties ---
            prop_box = box.box()
            # The display properties should only fully appear when an arrow is selected
            if is_dim:
                prop_box.label(text="Display Properties", icon='PROPERTIES')
                col2 = prop_box.column(align=True)
                dim_props = active_obj.fcd_pg_dim_props
                
                # AI Editor Note: 'Length' allows for precise input of dimensions.
                col2.prop(dim_props, "length", text="Length")
                
                row2 = col2.row(align=True)
                row2.prop(dim_props, "arrow_scale", text="Arrow")
                row2.prop(dim_props, "text_scale", text="Label")
                col2.prop(dim_props, "line_thickness", text="Line Thickness")
                col2.prop(dim_props, "offset", text="Offset from Object")
                col2.prop(dim_props, "extension", text="End Extension")
                col2.prop(dim_props, "text_color", text="Label Color")
                col2.prop(dim_props, "unit_display", text="Units")
            else:
                # A display to select a dimension arrow is shown when no arrows are selected
                row = prop_box.row(align=True)
                row.alignment = 'CENTER'
                row.label(text="Select a dimension arrow to adjust", icon='INFO')

def register():
    pass

def unregister():
    pass

