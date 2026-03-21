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

class URDF_PT_DimensionsAndMeasuring:
    """
    AI Editor Note:
    This class is a drawing helper for the 'Dimensions & Tools' panel. It is not a
    registered bpy.types.Panel, but is called by the main URDF_PT_AutoRobotAndCNCDevKit
    to draw its content.
    """

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        return context.scene.urdf_panel_enabled_dimensions

    @staticmethod
    def draw(layout: bpy.types.UILayout, context: bpy.types.Context) -> None:
        scene = context.scene
        box = layout.box()
        
        is_expanded = scene.urdf_show_panel_dimensions
        icon = 'TRIA_DOWN' if is_expanded else 'TRIA_RIGHT'
        row = box.row(align=True)
        op = row.operator("urdf.toggle_panel_visibility", text="Dimensions & Measuring", emboss=False, icon=icon)
        op.panel_property = "urdf_show_panel_dimensions"
        row.prop(scene, "urdf_show_panel_dimensions", text="", emboss=False, toggle=True)
        close_op = row.operator("urdf.disable_panel", text="", icon='X')
        close_op.prop_name = "urdf_panel_enabled_dimensions"

        if is_expanded:
            # --- Section: Dimensions & Text Descriptions ---
            dim_box = box.box()
            dim_box.label(text="Dimensions & Text Descriptions", icon='DRIVER_DISTANCE')
            dim_box.prop(scene, "urdf_dim_direction", text="Creation Direction")
            
            # AI Editor Note: Show manual direction setting if a dimension is selected
            if context.active_object and context.active_object.get("urdf_is_dimension"):
                dim_box.prop(context.active_object, "urdf_dim_direction", text="Direction")
            
            dim_box.prop(scene, "urdf_text_color", text="Text Color")
            
            row = dim_box.row(align=True)
            row.prop(scene, "urdf_dim_arrow_scale")
            row.prop(scene, "urdf_dim_text_scale")
            dim_box.prop(scene, "urdf_dim_unit_display", text="Display Units")
            
            if scene.urdf_text_placement_mode:
                dim_box.operator("urdf.toggle_text_placement", text="Stop Text Placement Mode", icon='CHECKMARK')
            else:
                dim_box.operator("urdf.toggle_text_placement", text="Start Text Placement Mode", icon='TRANSFORM_ORIGINS')
                
            dim_box.operator("urdf.add_dimension", text="Add Dimension (Vertex to Vertex)", icon='SNAP_PEEL_OBJECT')
            if context.active_object and context.active_object.get("urdf_is_dimension"):
                dim_box.operator("urdf.remove_dimension", text="Remove Selected Dimension", icon='TRASH')
            dim_box.operator("urdf.add_text_description", text="Add Text Description", icon='TEXT')


def register():
    for cls in [URDF_PT_DimensionsAndMeasuring]:
        if hasattr(cls, 'bl_rna'):
            bpy.utils.register_class(cls)

def unregister():
    for cls in reversed([URDF_PT_DimensionsAndMeasuring]):
        if hasattr(cls, 'bl_rna'):
            bpy.utils.unregister_class(cls)
