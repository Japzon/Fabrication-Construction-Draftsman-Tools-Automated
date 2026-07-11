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

class LSD_PT_Materials_And_Textures:
    """
    Drawing helper for the 'Materials & Texturing' panel.
    Provides a clean, accessible interface for material management,
    smart presets, and texture painting tools.
    """
    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        return context.scene.lsd_panel_enabled_materials
    @staticmethod
    def draw(layout: bpy.types.UILayout, context: bpy.types.Context) -> None:
        scene = context.scene
        # --- Header ---
        box, is_expanded = ui_common.draw_panel_header(layout, context, "Materials & Textures", "lsd_show_panel_materials", "lsd_panel_enabled_materials")
        if is_expanded:
            # --- Paint Bucket Tool Section ---
            bucket_box = box.box()
            bucket_box.label(text="Paint Bucket Tool", icon='BRUSH_DATA')
            
            # 1. Main Toggle
            col = bucket_box.column(align=True)
            col.prop(scene, "lsd_paint_bucket_mode", text="Enable Paint Bucket", icon='EVENT_P' if scene.lsd_paint_bucket_mode else 'MOUSE_MOVE')
            col.prop(scene, "lsd_paint_bucket_prevent_initial_fill", text="Prevent Initial Fill")
            
            box2 = col.box()
            box2.prop(scene, "lsd_paint_bucket_purge_mode", text="Purge Mode", icon='TRASH')
            if scene.lsd_paint_bucket_purge_mode:
                box2.label(text="WARNING: Clicking will strip materials!", icon='ERROR')
            
            if scene.lsd_paint_bucket_mode:
                col.label(text="Mode Active: Select faces to paint.", icon='INFO')
            
            bucket_box.separator()
            
            # 2. Color Selection
            col = bucket_box.column(align=True)
            col.label(text="Base Color / Tint:")
            col.template_color_picker(scene, "lsd_paint_bucket_color", value_slider=True)
            col.prop(scene, "lsd_paint_bucket_color", text="")
            
            bucket_box.separator()
            
            # 3. Texture Selection (Upload)
            col = bucket_box.column(align=True)
            col.label(text="Custom Texture:")
            col.template_ID(scene, "lsd_paint_bucket_image", open="image.open")
            
            if scene.lsd_paint_bucket_image:
                img = scene.lsd_paint_bucket_image
                col.label(text=f"Resolution: {img.size[0]}x{img.size[1]}", icon='IMAGE_DATA')
            
            bucket_box.separator()
def register():
    for cls in [LSD_PT_Materials_And_Textures]:
        if hasattr(cls, 'bl_rna'):
            bpy.utils.register_class(cls)
def unregister():
    for cls in reversed([LSD_PT_Materials_And_Textures]):
        if hasattr(cls, 'bl_rna'):
            bpy.utils.unregister_class(cls)
