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
from .. import config
from ..config import *
from .. import core
from .. import properties
from .. import operators
from . import ui_common

class FCD_PT_Physics:
    """
    AI Editor Note:
    This class is a drawing helper for the unified 'Physics' panel (Collision & Inertial).
    It is not a registered bpy.types.Panel, but is called by the main 
    FCD_PT_FabricationConstructionDraftsmanToolsAutomated to draw its content.
    """

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        return context.scene.fcd_panel_enabled_physics

    @staticmethod
    def draw(layout: bpy.types.UILayout, context: bpy.types.Context) -> None:
        scene = context.scene
        
        # 1. Standardized Header
        box, is_expanded = ui_common.draw_panel_header(
            layout, context, 
            "Physics", 
            "fcd_show_panel_physics", 
            "fcd_panel_enabled_physics"
        )
        
        if is_expanded:
            # --- COLLISION SECTION ---
            cbox = box.box()
            cbox.label(text="Collision Geometry", icon='PHYSICS')
            
            # 1. Collision Mesh Generation
            cbox.operator("fcd.generate_collision_mesh", text="Generate Collision Mesh (Selected)", icon='MESH_ICOSPHERE')
            
            # 2. Polygon Simplification Control
            # Properties are bound to the part itself if it's a parametric part
            obj = context.active_object
            if obj and hasattr(obj, "fcd_pg_mech_props"):
                props = obj.fcd_pg_mech_props.collision
                row = cbox.row(align=True)
                row.prop(props, "decimate_ratio", text="Poly Reduction", slider=True)
            else:
                cbox.label(text="Select a Parametric Part to adjust Poly Reduction", icon='INFO')

            cbox.separator()

            # --- INERTIAL SECTION ---
            ibox = box.box()
            ibox.label(text="Inertial Properties", icon='NODE_COMPOSITING')
            
            # Determine the property owner
            props_owner = None
            if context.mode == 'POSE' and context.active_pose_bone:
                props_owner = context.active_pose_bone.fcd_pg_kinematic_props
            elif context.active_object and hasattr(context.active_object, "fcd_pg_mech_props") and context.active_object.fcd_pg_mech_props.is_part:
                props_owner = context.active_object.fcd_pg_mech_props
            
            if props_owner:
                inertial_props = props_owner.inertial
                ibox.prop(inertial_props, "mass")
                
                col = ibox.column(align=True)
                col.prop(inertial_props, "center_of_mass")
                
                row = ibox.row(align=True)
                row.operator("fcd.calculate_center_of_mass", text="Calc COM", icon='CENTER_ONLY')
                row.operator("fcd.calculate_inertia", text="Calc Inertia", icon='DRIVER_ROTATIONAL_DIFFERENCE')
                
                ibox.separator()
                tensor_box = ibox.box()
                tensor_box.label(text="Inertia Tensor", icon='STRANDS')
                grid = tensor_box.grid_flow(columns=2, align=True)
                grid.prop(inertial_props, "ixx")
                grid.prop(inertial_props, "iyy")
                grid.prop(inertial_props, "izz")
                grid.prop(inertial_props, "ixy")
                grid.prop(inertial_props, "ixz")
                grid.prop(inertial_props, "iyz")
            else:
                ibox.label(text="Select a Parametric Part or Pose Bone", icon='INFO')


def register():
    pass

def unregister():
    pass
