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
import bmesh
import math
import mathutils
import re
import os
import json
import xml.etree.ElementTree as ET
import gpu
from bpy.app.handlers import persistent
from operator import itemgetter
from bpy_extras.io_utils import ExportHelper, ImportHelper
from bpy_extras import view3d_utils
from gpu_extras.batch import batch_for_shader
from typing import List, Tuple, Optional, Set, Any, Dict
from .. import config
from ..config import *
from .. import core
from .. import properties
from .. import operators
from . import ui_common

class FCD_PT_Physics_Collision:
    """
    AI Editor Note:
    This class is a drawing helper for the 'Physics: Collision' panel. It is not a
    registered bpy.types.Panel, but is called by the main FCD_PT_FabricationConstructionDraftsmanToolsAutomated
    to draw its content. This structure allows for dynamic reordering of panels.
    """

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        # AI Editor Note: Panel is now always available if enabled in preferences.
        return context.scene.fcd_panel_enabled_collision

    @staticmethod
    def draw(layout: bpy.types.UILayout, context: bpy.types.Context) -> None:
        scene = context.scene
        
        # 1. Standardized Header
        box, is_expanded = ui_common.draw_panel_header(
            layout, context, 
            "Physics: Collision", 
            "fcd_show_panel_collision", 
            "fcd_panel_enabled_collision"
        )
        
        if is_expanded:
            props_owner = None
            if context.mode == 'POSE' and context.active_pose_bone:
                props_owner = context.active_pose_bone.fcd_pg_kinematic_props
            elif context.active_object and hasattr(context.active_object, "fcd_pg_mech_props") and context.active_object.fcd_pg_mech_props.is_part:
                props_owner = context.active_object.fcd_pg_mech_props
            
            if props_owner:
                collision_props = props_owner.collision
                box.prop(collision_props, "shape")
                if collision_props.shape == 'MESH':
                    box.prop(collision_props, "collision_object")
            else:
                box.label(text="Select a Parametric Part or Pose Bone", icon='INFO')


def register():
    for cls in [FCD_PT_Physics_Collision]:
        if hasattr(cls, 'bl_rna'):
            bpy.utils.register_class(cls)

def unregister():
    for cls in reversed([FCD_PT_Physics_Collision]):
        if hasattr(cls, 'bl_rna'):
            bpy.utils.unregister_class(cls)

