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

class LSD_PT_Dimensions_And_Precision_Transforms:
    """
    Dimensions & Precision Transforms panel.
    Generates parametric mesh-based dimension displays. In Object Mode, measures between
    selected object bounding box centers. In Edit Mode, automatically attaches Parametric
    Anchor hooks at each selection group's center, then generates the dimension between
    those hooks — no vertex-parenting required.
    Provides accurate scaling/transform tools for drafting precision.
    """
    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        return getattr(context.scene, "lsd_panel_enabled_dimensions", False)
    @staticmethod
    def draw(layout: bpy.types.UILayout, context: bpy.types.Context) -> None:
        """
        Main drawing logic for the Dimensions toolkit.
        """
        scene = context.scene
        # 1. Standardized Header
        box, is_expanded = ui_common.draw_panel_header(
            layout, context,
            "Dimensions & Precision Transforms",
            "lsd_show_panel_dimensions",
            "lsd_panel_enabled_dimensions"
        )
        # Standard Dimensions Interface
        if is_expanded:
            col_main = box.column(align=True)
            # --- Section: Parametric Anchors (Moved from Procedural Toolkit) ---
            anchor_box = col_main.box()
            anchor_box.label(text="Parametric Anchors", icon='HOOK')
            # AI Editor Note: Enabled for both Edit and Object modes to support per-vertex and per-object hooks.
            row_anchor = anchor_box.row(align=True)
                        # AI Editor Note: Added anchor sizing controls (Project Task 1.1.2)
            row_size = anchor_box.row(align=True)
            row_size.prop(scene, "lsd_anchor_initial_size", text="Initial Size")
            row_size.prop(scene, "lsd_anchor_auto_size", text="Auto-Size", icon='AUTO')
            anchor_box.prop(scene, "lsd_anchor_placement_source", text="Generate At")
            anchor_box.prop(scene, "lsd_anchor_grouping_mode", text="Anchor Grouping")
            anchor_box.separator()
            # AI Editor Note: Enabled for both Edit and Object modes to support per-vertex and per-object hooks.
            row_anchor = anchor_box.row(align=True)
            row_anchor.operator("lsd.add_parametric_anchor", text="Attach Hook", icon='ORIENTATION_GLOBAL')
            row_anchor.operator("lsd.add_marker", text="Attach Marker", icon='EMPTY_AXIS')
            # Persistent Control for Anchor Transforms (regardless of initial selection)
            if context.scene.lsd_hook_placement_mode:
                anchor_box.operator("lsd.toggle_hook_placement", text="Stop Anchor Transform Mode", icon='CHECKMARK')
            else:
                anchor_box.operator("lsd.toggle_hook_placement", text="Start Anchor Transform Mode", icon='TRANSFORM_ORIGINS')
            row_ops = anchor_box.row(align=True)
            row_ops.operator("lsd.bake_anchor", text="Update Selected", icon='MODIFIER_ON')
            row_ops.operator("lsd.cleanup_anchor", text="Remove Selected", icon='TRASH')
            # Global Hide/Show All Anchors
            anchor_box.prop(scene, "lsd_hide_all_anchors", text="Hide All Anchors", toggle=True, icon='HIDE_OFF' if not scene.lsd_hide_all_anchors else 'HIDE_ON')
            # Contextual info for meshes with existing hooks
            if context.active_object and context.active_object.type == 'MESH':
                has_hooks = any(m.type == 'HOOK' for m in context.active_object.modifiers)
                if has_hooks:
                    anchor_box.label(text="Mesh has active hooks", icon='INFO')
            # --- Smart Dimension Toolkit (Unified) ---
            dim_toolkit_box = col_main.box()
            dim_toolkit_box.label(text="Dimension Generator & Preferences", icon='DRIVER_DISTANCE')
            # Global Preferences (For new dimensions)
            pref_col = dim_toolkit_box.column(align=True)
            # Row 0: Header + Auto Size Toggle
            row_header = pref_col.row(align=True)
            row_header.label(text="Default Preferences (New Assemblies):", icon='PREFERENCES')
            row_header.prop(scene, "lsd_dim_auto_scale_new", text="Auto Scale", icon='AUTO')
            # Row 1: Arrow + Txt Size
            row_size = pref_col.row(align=True)
            row_size.prop(scene, "lsd_dim_arrow_scale", text="Arrow")
            row_size.prop(scene, "lsd_dim_text_scale", text="Txt Size")
            # Row 2: Thickness + Txt Off
            row_thick = pref_col.row(align=True)
            row_thick.prop(scene, "lsd_dim_line_thickness", text="Thickness")
            row_thick.prop(scene, "lsd_dim_text_offset", text="Txt Off")
            # Row 3: Default Offset
            row_offset = pref_col.row(align=True)
            row_offset.prop(scene, "lsd_dim_use_offset", text="", icon='CHECKBOX_HLT' if getattr(scene, "lsd_dim_use_offset", False) else 'CHECKBOX_DEHLT')
            row_offset.prop(scene, "lsd_dim_offset", text="Default Offset")
            dim_toolkit_box.separator()
            col = dim_toolkit_box.column(align=True)
            col.operator("lsd.manually_draw_offset_line", text="Draw Offset Line from Selected", icon='CURVE_PATH')
            col.prop(scene, "lsd_edit_offset_anchors", toggle=True, icon='HOOK')
            col.operator("lsd.add_dimension", text="Generate Dimension", icon='ADD')
            
            active_obj = context.active_object
            is_standalone = active_obj and getattr(active_obj, "lsd_is_standalone_offset", False)
            
            from .. import core
            dim_host = core.get_dimension_host(active_obj)
            is_dim = dim_host is not None
            
            if is_dim:
                col.operator("lsd.remove_dimension", text="Remove Selected Dimensions", icon='TRASH')
            
            if is_standalone:
                col.separator()
                box = col.box()
                box.label(text="Standalone Offset Line", icon='LINCURVE')
                box.prop(active_obj, "lsd_standalone_thickness")
                box.prop(active_obj, "lsd_standalone_mimic_target")
                
            if is_dim or is_standalone:
                col.separator()
                color_box = col.box()
                scene = context.scene 
                color_row = color_box.row(align=True)
                color_row.prop(scene, "lsd_dim_global_text_color_sync", text="Force Global Sync", icon='WORLD')
                
                # Fetch local props
                if is_dim:
                    local_props = dim_host.lsd_pg_dim_props
                else:
                    local_props = active_obj.lsd_pg_dim_props
                
                if scene.lsd_dim_global_text_color_sync:
                    color_box.prop(scene, "lsd_dim_universal_text_color", text="Label Color")
                    color_box.prop(scene, "lsd_dim_universal_line_color", text="Dimension & Offset Line Color")
                else:
                    if is_dim:
                        color_box.prop(local_props, "text_color", text="Label Color")
                    color_box.prop(local_props, "line_color", text="Dimension & Offset Line Color")
            # --- Unified Display Properties ---
            col.separator()
            if is_dim:
                # prop_box.label(text="Display Properties", icon='PROPERTIES')
                dim_props = dim_host.lsd_pg_dim_props
                # 'Length' allows for precise input of dimensions.
                col.prop(dim_props, "length", text="Line Length")
                row2 = col.row(align=True)
                row2.prop(dim_props, "arrow_scale", text="Arrow")
                row2.prop(dim_props, "text_scale", text="Text Size")
                col.prop(dim_props, "text_offset", text="Text Offset")
                col.prop(dim_props, "line_thickness", text="Line Thickness")
                offset_row = col.row(align=True)
                offset_row.prop(dim_props, "use_offset", text="", icon='CHECKBOX_HLT' if dim_props.use_offset else 'CHECKBOX_DEHLT')
                offset_row.prop(dim_props, "offset", text="Line Offset from Target")
                col.operator("lsd.dimension_auto_scale", text="Auto Size Components", icon='AUTO')
                col.operator("lsd.register_default_proportions", text="Register Custom Proportions", icon='SETTINGS')
                col.prop(dim_props, "is_flipped", text="Flip Target Roles")
                col.prop(dim_props, "use_extension_lines", text="Use Extension Lines")
                # Architecture and Engineering fonts feature
                row_style = col.row(align=True)
                row_style.label(text="Font Style:")
                col.prop(dim_props, "font_name", text="")
                row_style_inner = col.row(align=True)
                row_style_inner.prop(dim_props, "font_bold", toggle=True, icon='BOLD')
                row_style_inner.prop(dim_props, "font_italic", toggle=True, icon='ITALIC')
                col.prop(dim_props, "flip_text", text="Flip Text")
                col.prop(dim_props, "unit_display", text="Units")
                # --- Swapped Section: Alignment Tools ---
            # Now placed after general dimension properties for a more logical flow
            if is_dim:
                align_box = col.box()
                align_box.label(text="Text Alignment", icon='ALIGN_CENTER')
                row_text = align_box.row(align=True)
                row_text.prop(dim_props, "text_alignment", expand=True)
                align_box.separator()
                # 2. Offset Alignment (Orthographic Constraints)
                grid_col = col.column(align=True)
                row_pos = grid_col.row(align=True)
                row_pos.prop(dim_props, "align_x", toggle=True, text="+X")
                row_pos.prop(dim_props, "align_y", toggle=True, text="+Y")
                row_pos.prop(dim_props, "align_z", toggle=True, text="+Z")
                row_neg = grid_col.row(align=True)
                row_neg.prop(dim_props, "align_nx", toggle=True, text="-X")
                row_neg.prop(dim_props, "align_ny", toggle=True, text="-Y")
                row_neg.prop(dim_props, "align_nz", toggle=True, text="-Z")
                # Bulk Alignment Tool (User Request)
                col.separator()
                col.operator("lsd.align_all_selected_dimensions", icon='ORIENTATION_GLOBAL')
            # Global Hide/Show All Dimensions (Moved outside the box for direct accessibility)
            col.separator()
            col.prop(scene, "lsd_hide_all_dimensions", text="Hide All Dimensions", toggle=True, icon='HIDE_OFF' if not scene.lsd_hide_all_dimensions else 'HIDE_ON')
            # --- Dimensions Master Tracker (Restored for Visibility) ---
            # Provides a unified list of dimensions within the sidebar for quick management.
            col.separator()
            lsd_draw_master_tracker_ui(col, context)
            col.separator()
            # --- Accurate Scale (New) ---
            scale_box = col_main.box()
            scale_box.label(text="Accurate Scaling", icon='CON_FOLLOWPATH')
            col_scale = scale_box.column(align=True)
            col_scale.prop(scene, "lsd_scale_mode", text="Scaling Mode")
            col_scale.prop(scene, "lsd_scale_pivot", text="Pivot Point")
            col_scale.separator()
            row_axes = col_scale.row(align=True)
            row_axes.prop(scene, "lsd_scale_axes", index=0, text="X", toggle=True)
            row_axes.prop(scene, "lsd_scale_axes", index=1, text="Y", toggle=True)
            row_axes.prop(scene, "lsd_scale_axes", index=2, text="Z", toggle=True)
            col_scale.prop(scene, "lsd_scale_value", text="Target Dimension")
            col_scale.separator()
            # Live Execution Controls (rearranged)
            col_scale.prop(scene, "lsd_scale_realtime", text="Live Calibration", icon='TIME')
            if not scene.lsd_scale_realtime:
                 col_scale.operator("lsd.accurate_scale", text="Commit Scale", icon='CHECKMARK')
def lsd_draw_master_tracker_ui(layout, context):
    """Drawing logic for the un-grouped tracked dimensions."""
    scene = context.scene
    master_box = layout.box()
    master_box.label(text="Dimensions Master Tracker", icon='OUTLINER')
    # Manual List Management
    row = master_box.row()
    row.operator("lsd.add_to_dimension_master", text="Track Selected Dimensions", icon='ADD')
    row_nav = master_box.row()
    row_nav.operator("lsd.navigate_to_dimension_groups", text="Locate Dimension Groups", icon='SCENE_DATA')
    master = scene.lsd_dimensions_master
    if not master:
        master_box.label(text="No tracked dimensions in active list.", icon='INFO')
    else:
        for idx, item in enumerate(master):
            host = item.obj
            if not host: continue
            # --- Two-Row Master Entry ---
            item_box = master_box.column(align=True)
            # Row 1: Selection | Name | Length
            r1 = item_box.row(align=True)
            sel_op = r1.operator("lsd.select_object_by_name", text="", icon='RESTRICT_SELECT_OFF')
            sel_op.target_name = host.name
            r1.prop(host, "name", text="")
            r1.prop(host.lsd_pg_dim_props, "length", text="Length")
            # Row 2: Ratio | Parent/Target | Remove
            r2 = item_box.row(align=True)
            r2.prop(item, "ratio", text="Ratio")
            r2.prop(item, "driver_target", text="Driver")
            rem_op = r2.operator("lsd.remove_from_dimension_master", text="", icon='X')
            rem_op.index = idx
            item_box.separator(factor=0.5)
    if master:
        master_box.separator()
        master_box.prop(scene, "lsd_dim_tracker_group_name", text="Group Name")
        master_box.operator("lsd.bake_dimensions_master", text="Group Tracked Dimensions", icon='GEOMETRY_NODES')
def lsd_draw_grouped_dimensions_ui(layout, scene):
    """Core drawing logic for the persistent grouped dimensions."""
    grouped_sets = getattr(scene, "lsd_dimensions_grouped_sets", [])
    if not grouped_sets:
        return
    for g_idx, group in enumerate(grouped_sets):
        box = layout.box()
        header = box.row()
        icon = 'DISCLOSURE_TRI_DOWN' if group.is_expanded else 'DISCLOSURE_TRI_RIGHT'
        header.prop(group, "is_expanded", text="", icon=icon, emboss=False)
        header.prop(group, "name", text="")
        manage_row = header.row(align=True)
        imp_op = manage_row.operator("lsd.import_grouped_dimensions_back", text="", icon='IMPORT')
        imp_op.group_index = g_idx
        del_op = manage_row.operator("lsd.clear_grouped_dimensions", text="", icon='TRASH')
        del_op.group_index = g_idx
        if group.is_expanded:
            box.separator()
            for idx, item in enumerate(group.items):
                host = item.obj
                if not host: continue
                # --- Single-Row Item Layout (Grouped Archive) ---
                item_box = box.row(align=True)
                sel_op = item_box.operator("lsd.select_object_by_name", text="", icon='RESTRICT_SELECT_OFF')
                sel_op.target_name = host.name
                item_box.prop(host, "name", text="")
                item_box.prop(host.lsd_pg_dim_props, "length", text="Length")
                rem_op = item_box.operator("lsd.remove_from_dimension_master", text="", icon='X')
                rem_op.index = idx
                rem_op.group_index = g_idx
                rem_op.is_grouped = True
class LSD_PT_Dimension_Group_Manager(bpy.types.Panel):
    """Unified manager for archived dimension groups in the Scene Tab."""
    bl_label = "Dimensions Group Manager"
    bl_idname = "LSD_PT_Dimension_Group_Manager"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = 'scene'
    bl_parent_id = "SCENE_PT_scene"
    bl_order = -1
    bl_options = set()
    def draw(self, context):
        layout = self.layout
        # Grouped Sets (Persistent Archives)
        lsd_draw_grouped_dimensions_ui(layout, context.scene)
def register():
    bpy.utils.register_class(LSD_PT_Dimension_Group_Manager)
def unregister():
    bpy.utils.unregister_class(LSD_PT_Dimension_Group_Manager)
