import bpy

class LSD_PT_Workflow_Optimizer(bpy.types.Panel):
    bl_label = "Workflow Optimizer"
    bl_idname = "LSD_PT_Workflow_Optimizer"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Layouts & Systems Toolkit"

    def draw(self, context):
        layout = self.layout
        box = layout.box()
        
        box.prop(context.scene, "lsd_enable_directional_translate", text="Enable Directional Translate (G)", toggle=True, icon='CON_TRANSLIKE')
        box.prop(context.scene, "lsd_enable_math_input", text="Enable Math Input (=)", toggle=True, icon='CON_SIZELIKE')
        box.prop(context.scene, "lsd_enable_asset_editor", text="Asset Browser Editor", toggle=True, icon='ASSET_MANAGER')
        if context.scene.lsd_enable_directional_translate:
            box.label(text="Select object > Press G > Move mouse > Type distance", icon='INFO')
            box.label(text="Moves exactly in cursor direction.", icon='BLANK1')
            
        if context.scene.lsd_enable_asset_editor:
            abox = box.box()
            abox.label(text="Selected Asset Editor:", icon='ASSET_MANAGER')
            
            asset = None
            for window in context.window_manager.windows:
                for area in window.screen.areas:
                    if area.type == 'FILE_BROWSER' and getattr(area, 'ui_type', '') == 'ASSETS':
                        # Try to find the selected asset using space params or context
                        with context.temp_override(window=window, area=area):
                            if hasattr(context, 'selected_assets') and context.selected_assets:
                                asset = context.selected_assets[0]
                            elif hasattr(context, 'selected_asset_files') and context.selected_asset_files:
                                asset = context.selected_asset_files[0]
                            elif hasattr(context, 'asset_file_handle') and context.asset_file_handle:
                                asset = context.asset_file_handle
                        if not asset:
                            space = area.spaces.active
                            if space and hasattr(space, 'params') and space.params:
                                asset = getattr(space.params, 'active_file', None)
                        if asset: break
                if asset: break
                
            if asset:
                if getattr(asset, 'local_id', None) is not None:
                    abox.prop(asset.local_id, "name", text="Name")
                    if hasattr(asset.local_id, 'asset_data') and asset.local_id.asset_data:
                        abox.prop(asset.local_id.asset_data, "catalog_id", text="Catalog")
                    
                    row = abox.row(align=True)
                    row.operator("lsd.asset_clear", text="Unmark Asset", icon='TRASH')
                else:
                    abox.prop(context.scene, "lsd_asset_new_name", text="Name")
                    abox.prop(context.scene, "lsd_asset_catalog", text="Catalog")
                    row = abox.row(align=True)
                    row.operator("lsd.asset_edit_external", text="Directly Save to External File", icon='FILE_TICK')
            else:
                abox.label(text="No asset selected.", icon='INFO')
                
        # Startup Preferences Box
        startup_box = layout.box()
        startup_box.label(text="Startup Preferences Override", icon='PREFERENCES')
        
        row1 = startup_box.row(align=True)
        row1.prop(context.scene, "lsd_startup_blend_path")
        row1.operator("lsd.select_startup_blend", icon='FILE_FOLDER', text="")
        
        row2 = startup_box.row(align=True)
        row2.prop(context.scene, "lsd_userpref_blend_path")
        row2.operator("lsd.select_userpref_blend", icon='FILE_FOLDER', text="")
        
        startup_box.operator("lsd.set_startup_files", icon='FILE_TICK')

classes = (
    LSD_PT_Workflow_Optimizer,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
