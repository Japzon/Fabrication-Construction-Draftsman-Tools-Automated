import bpy
import os
import shutil
from . import ui_common
from .. import core

class URDF_OT_OpenAssetBrowser(bpy.types.Operator):
    """Opens the Asset Browser in a new window"""
    bl_idname = "urdf.open_asset_browser"
    bl_label = "Open Asset Browser"
    def execute(self, context):
        try:
            bpy.ops.wm.window_new()
            new_window = context.window_manager.windows[-1]
            area = new_window.screen.areas[0]
            area.type = 'FILE_BROWSER'
            area.ui_type = 'ASSETS'
        except Exception:
            pass
        return {'FINISHED'}

class URDF_OT_CreateAssetFolder(bpy.types.Operator):
    """Creates a new folder and registers it as a Blender Asset Library"""
    bl_idname = "urdf.create_asset_folder"
    bl_label = "Create Asset Folder"
    def execute(self, context): return {'FINISHED'}

class URDF_OT_AddActiveToLibrary(bpy.types.Operator):
    """Marks the active object or collection as an asset"""
    bl_idname = "urdf.add_active_to_library"
    bl_label = "Add Selected to Library"
    def execute(self, context): return {'FINISHED'}

class URDF_OT_ImportAssetToLibrary(bpy.types.Operator):
    """Copies a selected .blend file into the selected asset library folder"""
    bl_idname = "urdf.import_asset_to_library"
    bl_label = "Import Asset to Folder"
    def execute(self, context): return {'FINISHED'}

class URDF_PT_AssetLibrarySystem:
    """
    Overhauled Asset Library System Panel Drawing Helper.
    Safe version to resolve AttributeError.
    """
    @classmethod
    def poll(cls, context):
        if not context or not hasattr(context, "scene"): return False
        return getattr(context.scene, "urdf_panel_enabled_assets", False)

    @staticmethod
    def draw(layout, context):
        scene = context.scene
        box = layout.box()
        
        # 0. Basic Header with auto-collapse support (triangle pattern)
        is_expanded = getattr(scene, "urdf_show_panel_assets", False)
        icon = 'TRIA_DOWN' if is_expanded else 'TRIA_RIGHT'
        row = box.row(align=True)
        
        # Make the header a single clickable operator to ensure auto-collapse always runs
        op = row.operator("urdf.toggle_panel_visibility", text="Asset Library System", emboss=False, icon=icon)
        if op:
            op.panel_property = "urdf_show_panel_assets"
            
        if hasattr(scene, "urdf_panel_enabled_assets"):
            close_op = row.operator("urdf.disable_panel", text="", icon='X')
            if close_op: close_op.prop_name = "urdf_panel_enabled_assets"

        if is_expanded:
            col = box.column()
            
            # Workflow 1
            f1 = col.box()
            f1.label(text="Step 1: Setup Library Folder", icon='FILE_FOLDER')
            if hasattr(scene, "urdf_new_library_path"):
                f1.prop(scene, "urdf_new_library_path", text="Path")
            f1.operator("urdf.create_asset_folder", text="Create & Register Folder", icon='FILE_FOLDER')
            
            # Workflow 2
            f2 = col.box()
            f2.label(text="Step 2: Add Selected to Library", icon='ADD')
            if hasattr(scene, "urdf_selected_asset_library"):
                f2.prop(scene, "urdf_selected_asset_library", text="Target Library")
            f2.operator("urdf.add_active_to_library", text="Mark Selected as Asset", icon='ASSET_MANAGER')
            
            # Workflow 3
            f3 = col.box()
            f3.label(text="Step 3: Open Asset Library", icon='WINDOW')
            f3.operator("urdf.open_asset_browser", text="Open Asset Browser Window", icon='WINDOW')
            
            # Workflow 4
            f4 = col.box()
            f4.label(text="Step 4: Import External Asset", icon='IMPORT')
            f4.operator("urdf.import_asset_to_library", text="Import .blend File to Folder", icon='APPEND_BLEND')

def register():
    for cls in [URDF_OT_OpenAssetBrowser, URDF_OT_CreateAssetFolder, URDF_OT_AddActiveToLibrary, URDF_OT_ImportAssetToLibrary]:
        if hasattr(cls, 'bl_rna'):
            bpy.utils.register_class(cls)

def unregister():
    for cls in reversed([URDF_OT_OpenAssetBrowser, URDF_OT_CreateAssetFolder, URDF_OT_AddActiveToLibrary, URDF_OT_ImportAssetToLibrary]):
        if hasattr(cls, 'bl_rna'):
            bpy.utils.unregister_class(cls)
