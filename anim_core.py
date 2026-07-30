import bpy

def reset_auto_keyframe_cache():
    """Resets the auto-keyframe cache so UI toggles don't falsely trigger snapshots."""
    try:
        from . import core
        if getattr(core, '_ak_cache', None) is not None:
            core._ak_dirty = False
            core._ak_dirty_time = 0.0
            obj = bpy.context.active_object
            if obj and obj.type == 'ARMATURE':
                core._ak_cache.clear()
                for bone in obj.pose.bones:
                    core._ak_cache[bone.name] = bone.matrix_basis.copy()
    except Exception:
        pass

def get_anim_settings(context):
    return context.scene.lsd_anim_settings

def get_active_object(context):
    obj = context.active_object
    if obj and obj.type == 'ARMATURE':
        return obj
    # If a mesh is selected, check its parent or modifiers
    if obj and obj.parent and obj.parent.type == 'ARMATURE':
        return obj.parent
    return obj

def ensure_nla_track(obj, track_name):
    if not obj.animation_data:
        obj.animation_data_create()
    for track in obj.animation_data.nla_tracks:
        if track.name == track_name:
            return track
    
    # If the track doesn't exist, create it
    track = obj.animation_data.nla_tracks.new()
    track.name = track_name
    return track

def get_action_fcurves(obj, action):
    """Safely retrieves F-Curves from both legacy Actions and Blender 4.3+ Slotted Actions."""
    fcurves = []
    if not action: return fcurves
    
    if hasattr(action, "fcurves"):
        fcurves.extend(action.fcurves)
    elif hasattr(action, "slots"):
        # For Slotted Actions, we must extract fcurves from the channelbags
        try:
            from bpy_extras import anim_utils
            for slot in action.slots:
                # If obj is provided and we can get the specific slot for this object, great.
                # Otherwise, just grab from all slots (like when importing)
                cb = anim_utils.action_get_channelbag_for_slot(action, slot)
                if cb and hasattr(cb, "fcurves"):
                    fcurves.extend(cb.fcurves)
        except Exception:
            pass
    return fcurves
def sync_layer_light(context):
    """Fast, synchronous update for influence and blend type. Does not touch Tweak Mode."""
    settings = get_anim_settings(context)
    if not settings.layers_enabled or not settings.layers:
        return
    # Apply to all objects to ensure global influence update
    for scene_obj in context.scene.objects:
        if not scene_obj.animation_data:
            continue
        
        for i, layer in enumerate(settings.layers):
            track = None
            for t in scene_obj.animation_data.nla_tracks:
                if t.name == layer.name or t.name == layer.track_name:
                    track = t
                    break
            
            if track:
                for strip in track.strips:
                    strip.blend_type = layer.blend_type
                    strip.influence = 0.0 if layer.is_muted else layer.influence
                    strip.mute = layer.is_muted
    
    context.view_layer.update()
    
    # CRITICAL: Muting the active layer while in Tweak Mode causes the Action slot to override the NLA strip!
    # Instead of forcefully exiting Tweak Mode (which flashes the UI), we can simply mute the active action's F-curves!
    obj = get_active_object(context)
    if obj and settings.active_layer_index < len(settings.layers):
        active_layer = settings.layers[settings.active_layer_index]
        if obj.animation_data and obj.animation_data.action:
            for fcurve in get_action_fcurves(obj, obj.animation_data.action):
                fcurve.mute = active_layer.is_muted
    
    context.view_layer.update()
    reset_auto_keyframe_cache()
def execute_sync_logic(context):
    """Core logic to restructure NLA tracks. Must be called when Tweak Mode is OFF."""
    settings = get_anim_settings(context)
    if not settings.layers_enabled or not settings.layers:
        return
        
    obj = get_active_object(context)
    if not obj or not obj.animation_data:
        return

    # 1. Apply muting and blending settings to ALL objects in the scene 
    # to guarantee global suppression (e.g., if a user animated multiple characters/meshes)
    for scene_obj in context.scene.objects:
        if not scene_obj.animation_data:
            continue
        for i, layer in enumerate(settings.layers):
            # Check if this object actually has a track for this layer
            track = None
            for t in scene_obj.animation_data.nla_tracks:
                if t.name == layer.name or t.name == layer.track_name:
                    track = t
                    break
            
            # If we are the active object, ensure the track exists
            if scene_obj == obj and not track:
                track = ensure_nla_track(scene_obj, layer.track_name if layer.track_name else layer.name)
            
            if track:
                if scene_obj == obj:
                    layer.track_name = track.name
                    if layer.name == track.name:
                        track.name = layer.name
                    
                track.mute = layer.is_muted
                track.lock = layer.is_locked
                
                # In NLA, strips hold the influence and blend_type
                for strip in track.strips:
                    strip.blend_type = layer.blend_type
                    
                    # Forcibly drop the strip influence to 0 and explicitly mute the strip itself
                    strip.influence = 0.0 if layer.is_muted else layer.influence
                    strip.mute = layer.is_muted
                    
                    strip.extrapolation = 'HOLD'
                    try:
                        strip.action_frame_start = -100000
                        strip.action_frame_end = 100000
                    except: pass
                    strip.frame_start = -100000
                    strip.frame_end = 100000
                    strip.scale = 1.0
            
    active_layer = None
    active_track = None
    if settings.active_layer_index >= 0 and settings.active_layer_index < len(settings.layers):
        active_layer = settings.layers[settings.active_layer_index]
        for t in obj.animation_data.nla_tracks:
            if t.name == active_layer.name or t.name == active_layer.track_name:
                active_track = t
                break
        
        if not active_track:
            active_track = ensure_nla_track(obj, active_layer.track_name if active_layer.track_name else active_layer.name)

        if active_track.strips:
            obj.animation_data.use_nla = True
            
            # Set the track as the active track for Tweak Mode
            for t in obj.animation_data.nla_tracks:
                t.select = False
                for s in t.strips:
                    s.select = False
            
            active_track.select = True
            active_track.strips[0].select = True
            
            try:
                # Explicitly set the internal active track pointer so Blender doesn't tweak the wrong one!
                obj.animation_data.nla_tracks.active = active_track
                
                if not active_track.strips and getattr(obj.animation_data, "action", None):
                    # Auto-push the floating action if a new layer was created and user started animating
                    strip = active_track.strips.new(
                        name=active_track.name,
                        start=int(obj.animation_data.action.frame_range[0]),
                        action=obj.animation_data.action
                    )
                    strip.blend_type = active_layer.blend_type
                    strip.extrapolation = 'HOLD'
                    if hasattr(strip, 'use_sync_length'):
                        strip.use_sync_length = False
                    try:
                        strip.action_frame_start = -100000
                        strip.action_frame_end = 100000
                    except: pass
                    strip.frame_start = -100000
                    strip.frame_end = 100000
                    strip.scale = 1.0
                elif not active_track.strips:
                    # Create an empty strip so tweak mode has something to lock onto and blend type applies
                    empty_action = bpy.data.actions.new(name=active_track.name)
                    if hasattr(empty_action, 'slots'):
                        try: 
                            slot_name = obj.id_data.name if hasattr(obj, 'id_data') else obj.name
                            empty_action.slots.new(name=slot_name, id_type=obj.id_type if hasattr(obj, 'id_type') else 'OBJECT')
                        except: pass
                        
                    strip = active_track.strips.new(
                        name=active_track.name,
                        start=1,
                        action=empty_action
                    )
                    strip.blend_type = active_layer.blend_type
                    strip.extrapolation = 'HOLD'
                    if hasattr(strip, 'use_sync_length'):
                        strip.use_sync_length = False
                    try:
                        strip.action_frame_start = -100000
                        strip.action_frame_end = 100000
                    except: pass
                    strip.frame_start = -100000
                    strip.frame_end = 100000
                    strip.scale = 1.0

                # Retroactively ensure all existing strips use true infinite mapping to bypass Tweak Mode freeze
                if active_track.strips:
                    existing_strip = active_track.strips[0]
                    existing_strip.blend_type = active_layer.blend_type
                    existing_strip.extrapolation = 'HOLD'
                    if hasattr(existing_strip, 'use_sync_length'):
                        existing_strip.use_sync_length = False
                    try:
                        existing_strip.action_frame_start = -100000
                        existing_strip.action_frame_end = 100000
                    except: pass
                    existing_strip.frame_start = -100000
                    existing_strip.frame_end = 100000
                    existing_strip.scale = 1.0
                active_track.strips[0].active = True
            except:
                pass
            
            # Try to assign the active track if the API supports it
            try:
                for t in obj.animation_data.nla_tracks:
                    t.is_solo = False
                active_track.is_solo = False
            except: pass
            
            # Ensure the action matches the layer state
            if active_layer.is_muted:
                # Clear the action if muted to prevent accidental base-level edits
                obj.animation_data.action = None
            elif active_track.strips:
                # Explicitly push the layer's action into the active slot for graph separation
                assigned_action = active_track.strips[0].action
                obj.animation_data.action = assigned_action
                if assigned_action and hasattr(obj.animation_data, 'action_slot') and hasattr(assigned_action, 'slots') and assigned_action.slots:
                    try: obj.animation_data.action_slot = assigned_action.slots[0]
                    except: pass
                
            # Aggressively disable NLA track visibility in all Graph Editors so the user only sees the active layer
            for window in context.window_manager.windows:
                for area in window.screen.areas:
                    if area.type in {'GRAPH_EDITOR', 'DOPESHEET_EDITOR'}:
                        if hasattr(area.spaces.active, 'dopesheet'):
                            try:
                                area.spaces.active.dopesheet.show_nla = False
                            except: pass
            
    # Now configure the active track ONLY for the active object
            if active_layer and active_track:
                pass

def invisible_tweakmode_swap(context, exit_first=False, enter_second=False):
    """Executes Tweak Mode transitions invisibly within a single frame redraw, avoiding UI flashes."""
    target_area = None
    target_window = None
    original_type = None
    
    # Prefer an existing NLA Editor if one happens to be open
    for window in context.window_manager.windows:
        for area in window.screen.areas:
            if area.type == 'NLA_EDITOR':
                target_window = window
                target_area = area
                original_type = area.type
                break
        if target_area: break
        
    if not target_area:
        # Hijack an inactive background area (e.g. Outliner or Timeline)
        for window in context.window_manager.windows:
            for area in window.screen.areas:
                if area != context.area and area.type != 'PROPERTIES':
                    target_window = window
                    target_area = area
                    original_type = area.type
                    break
            if target_area: break
            
    if not target_area:
        # Fallback to pure logic if no safe area exists
        obj = get_active_object(context)
        if exit_first and obj and obj.animation_data:
            obj.animation_data.action = None
        execute_sync_logic(context)
        return
        
    try:
        # Synchronous hijack: Swap the area type in memory
        if target_area.type != 'NLA_EDITOR':
            target_area.type = 'NLA_EDITOR'
            
        target_region = None
        for region in target_area.regions:
            if region.type == 'WINDOW':
                target_region = region
                break
                
        if target_region:
            override = context.copy()
            override['window'] = target_window
            override['area'] = target_area
            override['region'] = target_region
            if hasattr(target_area, "spaces") and target_area.spaces.active:
                override['space_data'] = target_area.spaces.active
            
            with context.temp_override(**override):
                if exit_first:
                    try: bpy.ops.nla.tweakmode_exit(isolate_action=False)
                    except:
                        try: bpy.ops.nla.tweakmode_exit()
                        except: pass
                    
                obj = get_active_object(context)
                if obj and obj.animation_data:
                    obj.animation_data.action = None  # Prevent old layer action from leaking
                    
                execute_sync_logic(context)
                
                # CRITICAL: Force a depsgraph update before entering Tweak Mode. 
                # If we don't, Blender caches the uninitialized strip state and COMBINE mode acts like REPLACE until the user manually switches layers.
                if context.view_layer:
                    context.view_layer.update()
                
                if enter_second:
                    try: bpy.ops.nla.tweakmode_enter(isolate_action=False)
                    except:
                        try: bpy.ops.nla.tweakmode_enter()
                        except: pass
                        
                # CRITICAL: Force another depsgraph update and tag the object after entering Tweak Mode.
                # If we don't, Blender's viewport gets stuck displaying the previous layer's poses until the user manually toggles a property like Mute.
                if context.view_layer:
                    context.view_layer.update()
                
                obj = get_active_object(context)
                if obj:
                    obj.update_tag(refresh={'OBJECT', 'DATA'})
                    
                    # CRITICAL: Force NLA cache invalidation by quickly toggling the mute state of all tracks.
                    # This physically mimics the user's manual mute/unmute workaround to fix Blender's C++ NLA cache freezing.
                    if obj.animation_data:
                        for t in obj.animation_data.nla_tracks:
                            orig_mute = t.mute
                            t.mute = not orig_mute
                            t.mute = orig_mute
        else:
            # Fallback if region generation failed
            execute_sync_logic(context)
            
    finally:
        # CRITICAL: Instantly restore the area type BEFORE Blender executes its next frame redraw!
        # This completely hides the NLA Editor swap from the user's screen.
        if target_area and original_type and target_area.type != original_type:
            target_area.type = original_type
        reset_auto_keyframe_cache()
        
        # CRITICAL: Force onion skin to instantly flush and rebuild after a tweakmode swap (layer change)
        try:
            from . import anim_onion_skin
            anim_onion_skin._cached_data.clear()
            anim_onion_skin._cached_keyframe_frames.clear()
        except: pass

def update_layer_property_light(self, context):
    sync_layer_light(context)

def update_layer_property_heavy(self, context):
    invisible_tweakmode_swap(context, exit_first=True, enter_second=True)

def update_active_layer(self, context):
    invisible_tweakmode_swap(context, exit_first=True, enter_second=True)

