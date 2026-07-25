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

class LSD_UL_PaintLayers(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        layer = item
        
        row = layout.row(align=True)
        # Mute
        mute_icon = 'HIDE_ON' if layer.is_muted else 'HIDE_OFF'
        row.prop(layer, "is_muted", text="", icon=mute_icon, emboss=False)
        
        # Opacity
        op_col = row.column(align=True)
        op_col.scale_x = 0.5
        op_col.prop(layer, "opacity", text="", slider=True) 
        
        # Name (Double-click/F2 to rename natively supported by UIList)
        row.prop(layer, "name", text="", emboss=False)


class LSD_PT_Materials_And_Textures:
    """
    Drawing helper for the 'Paint Tools' panel.
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
        box, is_expanded = ui_common.draw_panel_header(layout, context, "Paint Tools", "lsd_show_panel_materials", "lsd_panel_enabled_materials")
        if is_expanded:
            # --- Paint Mode Section ---
            mode_box = box.box()
            mode_header = mode_box.row()
            mode_icon = 'TRIA_DOWN' if scene.lsd_enable_paint_mode else 'TRIA_RIGHT'
            mode_header.prop(scene, "lsd_enable_paint_mode", icon=mode_icon, emboss=False, text="")
            mode_header.label(text="Paint Mode", icon='TPAINT_HLT')
            
            op_row = mode_header.row(align=True)
            op_row.alignment = 'RIGHT'
            check_icon = 'CHECKBOX_HLT' if scene.lsd_enable_paint_mode else 'CHECKBOX_DEHLT'
            op_row.prop(scene, "lsd_enable_paint_mode", icon=check_icon, emboss=False, text="")
            
            if scene.lsd_enable_paint_mode:
                mode_col = mode_box.column(align=True)
                mode_col.prop(scene, "lsd_paint_tool", text="Active Tool")
                
                if scene.lsd_paint_tool == 'PAINT_BUCKET':
                    mode_col.prop(scene, "lsd_paint_bucket_prevent_initial_fill", text="Prevent Initial Selection Fill")
                    
                    box2 = mode_col.box()
                    box2.prop(scene, "lsd_paint_bucket_purge_mode", text="Purge Mode", icon='TRASH')
                    if scene.lsd_paint_bucket_purge_mode:
                        box2.label(text="WARNING: Clicking will strip materials!", icon='ERROR')
                    
                    mode_col.label(text="Mode Active: Select faces to paint.", icon='INFO')
            
            # --- Materials & Texture Selection Section ---
            bucket_box = box.box()
            
            header_row = bucket_box.row()
            header_row.label(text="Materials & Texture Selection", icon='BRUSH_DATA')
            
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

            # --- Paint Layers Section ---
            layer_box = box.box()
            header_row = layer_box.row()
            header_row.label(text="Paint Layers", icon='MOD_HUE_SATURATION')
            
            # Add/Remove buttons on the top right
            
            row = layer_box.row()
            row.template_list("LSD_UL_PaintLayers", "", scene, "lsd_paint_layers", scene, "lsd_active_paint_layer_index", rows=4)
            
            col = row.column(align=True)
            col.operator("lsd.paint_layer_add", text="", icon='ADD')
            col.operator("lsd.paint_layer_remove", text="", icon='REMOVE')
            col.separator()
            up_op = col.operator("lsd.paint_layer_move", text="", icon='TRIA_UP')
            up_op.direction = 'UP'
            down_op = col.operator("lsd.paint_layer_move", text="", icon='TRIA_DOWN')
            down_op.direction = 'DOWN'
            
            layer_box.separator()
def register():
    for cls in [LSD_PT_Materials_And_Textures, LSD_UL_PaintLayers]:
        if hasattr(cls, 'bl_rna'):
            bpy.utils.register_class(cls)
def unregister():
    for cls in reversed([LSD_PT_Materials_And_Textures, LSD_UL_PaintLayers]):
        if hasattr(cls, 'bl_rna'):
            bpy.utils.unregister_class(cls)
