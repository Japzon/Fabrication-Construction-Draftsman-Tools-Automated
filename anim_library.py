import bpy
import os
import shutil
import glob
import bpy.utils.previews

# Global dictionary to store preview collections
preview_collections = {}

# Global variable to track the current animation frame for the UI
_preview_frame_index = 0

def get_library_path():
    """Returns the absolute path to the project-specific or custom anim_library directory."""
    settings = getattr(bpy.context.scene, 'lsd_anim_settings', None)
    if settings and settings.custom_library_path and os.path.exists(bpy.path.abspath(settings.custom_library_path)):
        return bpy.path.abspath(settings.custom_library_path)
        
    blend_path = bpy.data.filepath
    if not blend_path:
        import tempfile
        base_dir = os.path.join(tempfile.gettempdir(), "LSD_Unsaved_Projects")
    else:
        base_dir = os.path.dirname(blend_path)
        
    lib_path = os.path.join(base_dir, "anim_library")
    if not os.path.exists(lib_path):
        os.makedirs(lib_path)
    return lib_path

def get_preview_dir(layer_name):
    """Returns the path to a specific layer's preview image sequence."""
    lib_path = get_library_path()
    preview_dir = os.path.join(lib_path, f"{layer_name}_preview")
    if not os.path.exists(preview_dir):
        os.makedirs(preview_dir)
    return preview_dir

def load_previews():
    """Scans the anim_library and loads all image sequences into bpy.utils.previews."""
    global preview_collections
    
    # Clear existing previews
    for pcoll in preview_collections.values():
        bpy.utils.previews.remove(pcoll)
    preview_collections.clear()
    
    pcoll = bpy.utils.previews.new()
    preview_collections["main"] = pcoll
    
    lib_path = get_library_path()
    
    # Scan for directories ending in _preview
    for item in os.listdir(lib_path):
        item_path = os.path.join(lib_path, item)
        if os.path.isdir(item_path) and item.endswith("_preview"):
            layer_name = item.replace("_preview", "")
            
            # Find all PNGs in this directory
            pngs = glob.glob(os.path.join(item_path, "*.png"))
            pngs.sort()
            
            # Load each PNG into the preview collection with a numbered key
            for i, png_path in enumerate(pngs):
                icon_name = f"{layer_name}_{i}"
                if icon_name not in pcoll:
                    pcoll.load(icon_name, png_path, 'IMAGE')
                    
            # Also store the total frame count for this layer as a custom property
            setattr(pcoll, f"{layer_name}_count", len(pngs))
            
def get_animated_icon_id(layer_name):
    """Returns the icon_id for the current frame of the animation loop."""
    pcoll = preview_collections.get("main")
    if not pcoll: return 0
    
    count = getattr(pcoll, f"{layer_name}_count", 0)
    if count == 0: return 0
    
    frame = _preview_frame_index % count
    icon_name = f"{layer_name}_{frame}"
    
    if icon_name in pcoll:
        return pcoll[icon_name].icon_id
    return 0

def preview_timer_update():
    """Timer callback to increment the preview frame and force UI redraws."""
    global _preview_frame_index
    _preview_frame_index += 1
    
    # Tag 3D View and Properties UI for redraw to animate the icon
    for window in bpy.context.window_manager.windows:
        for area in window.screen.areas:
            if area.type in {'VIEW_3D', 'PROPERTIES', 'NLA_EDITOR'}:
                area.tag_redraw()
                
    return 0.1 # Run at 10 FPS for the UI animation

from bpy_extras.io_utils import ImportHelper

class LSD_OT_Anim_Library_Select_Dir(bpy.types.Operator):
    bl_idname = "lsd.anim_library_select_dir"
    bl_label = "Select Animation Layer Folder"
    
    directory: bpy.props.StringProperty(
        name="Folder Path",
        subtype='DIR_PATH',
        default=""
    )
    
    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}
        
    def execute(self, context):
        settings = context.scene.lsd_anim_settings
        dir_path = self.directory
        if not os.path.isdir(dir_path):
            dir_path = os.path.dirname(dir_path)
            
        settings.custom_library_path = dir_path
        bpy.ops.lsd.anim_library_refresh()
        return {'FINISHED'}

class LSD_OT_Anim_Library_Refresh(bpy.types.Operator):
    bl_idname = "lsd.anim_library_refresh"
    bl_label = "Refresh Library"
    
    def execute(self, context):
        load_previews()
        
        settings = context.scene.lsd_anim_settings
        settings.library_items.clear()
        
        lib_path = get_library_path()
        for item in os.listdir(lib_path):
            if item.endswith(".blend"):
                layer_name = item.replace(".blend", "")
                if os.path.isdir(os.path.join(lib_path, f"{layer_name}_preview")):
                    new_item = settings.library_items.add()
                    new_item.name = layer_name
                    new_item.filepath = os.path.join(lib_path, item)
                
        return {'FINISHED'}

class LSD_OT_Anim_Library_Delete(bpy.types.Operator):
    bl_idname = "lsd.anim_library_delete"
    bl_label = "Delete Layer"
    bl_description = "Delete the selected animation layer from the library"
    
    @classmethod
    def poll(cls, context):
        settings = context.scene.lsd_anim_settings
        return len(settings.library_items) > 0

    def execute(self, context):
        settings = context.scene.lsd_anim_settings
        if not settings.library_items or settings.active_library_index >= len(settings.library_items):
            return {'CANCELLED'}
            
        item = settings.library_items[settings.active_library_index]
        layer_name = item.name
        lib_path = get_library_path()
        
        blend_file = os.path.join(lib_path, f"{layer_name}.blend")
        preview_dir = os.path.join(lib_path, f"{layer_name}_preview")
        
        try:
            import shutil
            if os.path.exists(blend_file):
                os.remove(blend_file)
            if os.path.exists(preview_dir):
                shutil.rmtree(preview_dir)
        except Exception as e:
            self.report({'ERROR'}, f"Failed to delete files: {e}")
            return {'CANCELLED'}
            
        bpy.ops.lsd.anim_library_refresh()
        
        if settings.active_library_index >= len(settings.library_items):
            settings.active_library_index = max(0, len(settings.library_items) - 1)
            
        return {'FINISHED'}

class LSD_OT_Anim_Library_Update_Preview(bpy.types.Operator):
    bl_idname = "lsd.anim_library_update_preview"
    bl_label = "Update Preview"
    bl_description = "Recapture the animated preview for the selected library item based on the active scene layer"
    
    def execute(self, context):
        settings = context.scene.lsd_anim_settings
        if not settings.library_items or settings.active_library_index >= len(settings.library_items):
            self.report({'ERROR'}, "No library item selected")
            return {'CANCELLED'}
            
        item = settings.library_items[settings.active_library_index]
        obj = context.active_object
        
        if not obj or not obj.animation_data:
            self.report({'ERROR'}, "No object/animation data selected")
            return {'CANCELLED'}
            
        layer = settings.layers[settings.active_layer_index]
        track = obj.animation_data.nla_tracks.get(layer.track_name if layer.track_name else layer.name)
        if not track or not track.strips:
            action = obj.animation_data.action
            if not action:
                self.report({'ERROR'}, "No active animation found to preview")
                return {'CANCELLED'}
        else:
            action = track.strips[0].action
            
        # Isolate layer
        original_mutes = {}
        if obj.animation_data and obj.animation_data.nla_tracks:
            for t in obj.animation_data.nla_tracks:
                original_mutes[t.name] = t.mute
                if track and t.name == track.name:
                    t.mute = False
                else:
                    t.mute = True
                    
        preview_dir = get_preview_dir(item.name)
        
        orig_filepath = context.scene.render.filepath
        orig_format = context.scene.render.image_settings.file_format
        orig_res_x = context.scene.render.resolution_x
        orig_res_y = context.scene.render.resolution_y
        
        try:
            context.scene.render.image_settings.file_format = 'PNG'
            context.scene.render.resolution_x = 200
            context.scene.render.resolution_y = 200
            
            frame_range = int(action.frame_range[1] - action.frame_range[0])
            step = max(1, frame_range // 10)
            orig_frame = context.scene.frame_current
            
            img_idx = 0
            for f in range(int(action.frame_range[0]), int(action.frame_range[1]) + 1, step):
                context.scene.frame_set(f)
                context.scene.render.filepath = os.path.join(preview_dir, f"prev_{img_idx:04d}.png")
                bpy.ops.render.opengl(write_still=True, view_context=True)
                img_idx += 1
                
            context.scene.frame_set(orig_frame)
        finally:
            if obj.animation_data and obj.animation_data.nla_tracks:
                for t in obj.animation_data.nla_tracks:
                    if t.name in original_mutes:
                        t.mute = original_mutes[t.name]
            context.scene.render.filepath = orig_filepath
            context.scene.render.image_settings.file_format = orig_format
            context.scene.render.resolution_x = orig_res_x
            context.scene.render.resolution_y = orig_res_y
            
        bpy.ops.lsd.anim_library_refresh()
        self.report({'INFO'}, f"Updated preview for {item.name}")
        return {'FINISHED'}

class LSD_OT_Anim_Library_Export(bpy.types.Operator):
    bl_idname = "lsd.anim_library_export"
    bl_label = "Export Active Layer"
    
    def execute(self, context):
        settings = context.scene.lsd_anim_settings
        if settings.active_layer_index < 0 or settings.active_layer_index >= len(settings.layers):
            self.report({'ERROR'}, "No active layer to export")
            return {'CANCELLED'}
            
        layer = settings.layers[settings.active_layer_index]
        obj = context.active_object
        
        if not obj or not obj.animation_data:
            self.report({'ERROR'}, "No object/animation data selected")
            return {'CANCELLED'}
            
        # Get action from the track
        track = obj.animation_data.nla_tracks.get(layer.track_name if layer.track_name else layer.name)
        if not track or not track.strips:
            action = obj.animation_data.action
            if not action:
                self.report({'ERROR'}, "No animation data found on this layer")
                return {'CANCELLED'}
        else:
            action = track.strips[0].action
            
        lib_path = get_library_path()
        out_filepath = os.path.join(lib_path, f"{layer.name}.blend")
        
        # Save action to blend file
        bpy.data.libraries.write(out_filepath, {action}, fake_user=True)
        
        # Now render preview images using OpenGL Viewport render
        preview_dir = get_preview_dir(layer.name)
        
        # Simple viewport render logic
        orig_filepath = context.scene.render.filepath
        orig_format = context.scene.render.image_settings.file_format
        orig_res_x = context.scene.render.resolution_x
        orig_res_y = context.scene.render.resolution_y
        
        # Save original track states to isolate this layer's animation
        original_mutes = {}
        if obj.animation_data and obj.animation_data.nla_tracks:
            for t in obj.animation_data.nla_tracks:
                original_mutes[t.name] = t.mute
                if track and t.name == track.name:
                    t.mute = False
                else:
                    t.mute = True
                    
        try:
            context.scene.render.image_settings.file_format = 'PNG'
            context.scene.render.resolution_x = 200
            context.scene.render.resolution_y = 200
            
            frame_range = int(action.frame_range[1] - action.frame_range[0])
            step = max(1, frame_range // 10) # 10 frames of preview
            
            orig_frame = context.scene.frame_current
            
            img_idx = 0
            for f in range(int(action.frame_range[0]), int(action.frame_range[1]) + 1, step):
                context.scene.frame_set(f)
                context.scene.render.filepath = os.path.join(preview_dir, f"prev_{img_idx:04d}.png")
                bpy.ops.render.opengl(write_still=True, view_context=True)
                img_idx += 1
                
            context.scene.frame_set(orig_frame)
            
        finally:
            # Restore original track states
            if obj.animation_data and obj.animation_data.nla_tracks:
                for t in obj.animation_data.nla_tracks:
                    if t.name in original_mutes:
                        t.mute = original_mutes[t.name]
            context.scene.render.filepath = orig_filepath
            context.scene.render.image_settings.file_format = orig_format
            context.scene.render.resolution_x = orig_res_x
            context.scene.render.resolution_y = orig_res_y
            
        bpy.ops.lsd.anim_library_refresh()
        return {'FINISHED'}

class LSD_OT_Anim_Library_Import(bpy.types.Operator):
    bl_idname = "lsd.anim_library_import"
    bl_label = "Import Layer"
    
    def execute(self, context):
        settings = context.scene.lsd_anim_settings
        if not settings.library_items or settings.active_library_index >= len(settings.library_items):
            return {'CANCELLED'}
            
        item = settings.library_items[settings.active_library_index]
        
        # Append action
        with bpy.data.libraries.load(item.filepath) as (data_from, data_to):
            data_to.actions = data_from.actions
            
        if not data_to.actions:
            self.report({'ERROR'}, "No action found in library file")
            return {'CANCELLED'}
            
        action = data_to.actions[0]
        
        # Shift action keyframes to align perfectly with the current playhead
        try:
            from . import anim_core
            fcurves = anim_core.get_action_fcurves(None, action)
        except Exception:
            fcurves = []
            
        min_frame = float('inf')
        has_keys = False
        if fcurves:
            for fc in fcurves:
                if fc.keyframe_points:
                    has_keys = True
                    for kp in fc.keyframe_points:
                        if kp.co.x < min_frame:
                            min_frame = kp.co.x
                            
        if has_keys:
            offset = context.scene.frame_current - min_frame
            if offset != 0:
                for fc in fcurves:
                    for kp in fc.keyframe_points:
                        kp.co.x += offset
                        kp.handle_left.x += offset
                        kp.handle_right.x += offset
                    fc.update()
        
        # Create a new layer in our UI
        bpy.ops.lsd.anim_layer_add()
        
        # Assign action
        obj = context.active_object
        if obj and obj.animation_data:
            try:
                from . import anim_core
                # Step 1: Force exit tweak mode so the action isn't locked as read-only by the dependency graph!
                anim_core.invisible_tweakmode_swap(context, exit_first=True, enter_second=False)
                
                # Step 2: Swap the action on the newly created layer's NLA strip
                layer = settings.layers[-1]
                track = obj.animation_data.nla_tracks.get(layer.track_name)
                if track and track.strips:
                    strip = track.strips[0]
                    old_action = strip.action
                    strip.action = action
                    if old_action:
                        bpy.data.actions.remove(old_action)
                        
                # Step 3: Rename track and layer to match the clean library item name (with collision handling)
                base_name = item.name
                action_name = base_name
                existing_names = [l.name for l in settings.layers if l != layer]
                counter = 1
                while action_name in existing_names:
                    action_name = f"{base_name}.{counter:03d}"
                    counter += 1
                    
                layer.name = action_name
                action.name = action_name
                if track:
                    track.name = action_name
                    layer.track_name = action_name
                    
                # Step 4: Re-enter tweak mode to resume animating
                anim_core.invisible_tweakmode_swap(context, exit_first=False, enter_second=True)
                
            except Exception as e:
                print(f"Error during library import action swap: {e}")
        
        return {'FINISHED'}

CLASSES = (
    LSD_OT_Anim_Library_Select_Dir,
    LSD_OT_Anim_Library_Refresh,
    LSD_OT_Anim_Library_Update_Preview,
    LSD_OT_Anim_Library_Export,
    LSD_OT_Anim_Library_Import,
    LSD_OT_Anim_Library_Delete,
)

def register():
    try:
        load_previews()
    except Exception as e:
        print(f"Failed to load anim library previews: {e}")
        
    try:
        if not bpy.app.timers.is_registered(preview_timer_update):
            bpy.app.timers.register(preview_timer_update)
    except: pass
    
    for cls in CLASSES:
        try:
            bpy.utils.register_class(cls)
        except Exception as e:
            print(f"Failed to register anim library class {cls}: {e}")

def unregister():
    try:
        if bpy.app.timers.is_registered(preview_timer_update):
            bpy.app.timers.unregister(preview_timer_update)
    except: pass
        
    try:
        for pcoll in preview_collections.values():
            bpy.utils.previews.remove(pcoll)
        preview_collections.clear()
    except: pass
    
    for cls in reversed(CLASSES):
        try:
            bpy.utils.unregister_class(cls)
        except: pass
