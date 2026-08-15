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
    if not settings.layers_enabled:
        return
        
    obj = get_active_object(context)
    if not obj or not hasattr(obj, 'lsd_anim_layers_data') or not obj.animation_data:
        return
        
    layer_data = obj.lsd_anim_layers_data
    if not layer_data.layers: return
    
    # Apply to the active object ONLY
    for i, layer in enumerate(layer_data.layers):
        track = None
        for t in obj.animation_data.nla_tracks:
            if t.name == layer.name or t.name == layer.track_name:
                track = t
                break
        
        if track:
            for strip in track.strips:
                strip.blend_type = layer.blend_type
                strip.extrapolation = 'NOTHING' if layer.blend_type == 'REPLACE' else 'HOLD_FORWARD'
                strip.influence = 0.0 if layer.is_muted else layer.influence
                strip.mute = layer.is_muted
                
                if strip.action:
                    for fcurve in get_action_fcurves(obj, strip.action):
                        fcurve.mute = layer.is_muted
    
    context.view_layer.update()
    
    # CRITICAL: Muting the active layer while in Tweak Mode causes the Action slot to override the NLA strip!
    # Instead of forcefully exiting Tweak Mode (which flashes the UI), we can simply mute the active action's F-curves!
    if layer_data.active_layer_index < len(layer_data.layers):
        active_layer = layer_data.layers[layer_data.active_layer_index]
        
        # Restore the action if it was cleared while muted
        if not active_layer.is_muted and not obj.animation_data.action:
            track = obj.animation_data.nla_tracks.get(active_layer.track_name)
            if track and track.strips:
                try:
                    obj.animation_data.action = track.strips[0].action
                except: pass
                
        if obj.animation_data and obj.animation_data.action:
            for fcurve in get_action_fcurves(obj, obj.animation_data.action):
                fcurve.mute = active_layer.is_muted
    
    context.view_layer.update()
    
    # CRITICAL: Force NLA cache invalidation
    if obj and obj.animation_data:
        for t in obj.animation_data.nla_tracks:
            orig_mute = t.mute
            t.mute = not orig_mute
            t.mute = orig_mute
            
    context.view_layer.update()
    reset_auto_keyframe_cache()
def execute_sync_logic(context, enter_tweak_mode=True):
    """Core logic to restructure NLA tracks."""
    settings = get_anim_settings(context)
    if not settings.layers_enabled:
        return
        
    obj = get_active_object(context)
    if not obj or not obj.animation_data or not hasattr(obj, 'lsd_anim_layers_data'):
        return
        
    layer_data = obj.lsd_anim_layers_data
    if not layer_data.layers: return

    # Aggressively repair existing broken files: forcibly unmute the base track so the base animation is never frozen
    for track in obj.animation_data.nla_tracks:
        if "Base_Layer" in track.name or "Base Layer" in track.name:
            track.mute = False

    # 1. Apply muting and blending settings to the active object ONLY
    for i, layer in enumerate(layer_data.layers):
        # Check if this object actually has a track for this layer
        track = None
        for t in obj.animation_data.nla_tracks:
            if t.name == layer.name or t.name == layer.track_name:
                track = t
                break
        
        # Ensure the track exists
        if not track:
            track = ensure_nla_track(obj, layer.track_name if layer.track_name else layer.name)
        
        if track:
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
                
                if strip.action:
                    for fcurve in get_action_fcurves(obj, strip.action):
                        fcurve.mute = layer.is_muted
                
                strip.extrapolation = 'NOTHING' if layer.blend_type == 'REPLACE' else 'HOLD_FORWARD'
                if hasattr(strip, 'use_sync_length'):
                    strip.use_sync_length = True
                        
    def safe_enter_tweak_mode(context_ref, o, t, s):
        if not o or not o.animation_data: return
        for window in context_ref.window_manager.windows:
            for area in window.screen.areas:
                if area.type == 'NLA_EDITOR':
                    target_space = None
                    if hasattr(area, "spaces"):
                        for space in area.spaces:
                            if space.type == 'NLA_EDITOR':
                                target_space = space
                                break
                    target_region = None
                    for region in area.regions:
                        if region.type == 'WINDOW':
                            target_region = region
                            break
                            
                    with context_ref.temp_override(window=window, area=area, region=target_region, space_data=target_space, active_object=o, selected_objects=[o]):
                        if getattr(o.animation_data, 'use_tweak_mode', False):
                            try: bpy.ops.nla.tweakmode_exit(isolate_action=False)
                            except: pass
                        if t and s:
                            for tr in o.animation_data.nla_tracks:
                                tr.select = False
                                for st in tr.strips: st.select = False
                            t.select = True
                            s.select = True
                            try: bpy.ops.nla.tweakmode_enter(isolate_action=False)
                            except: pass
                    return
            
    active_layer = None
    active_track = None
    if layer_data.active_layer_index >= 0 and layer_data.active_layer_index < len(layer_data.layers):
        active_layer = layer_data.layers[layer_data.active_layer_index]
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
                    strip.extrapolation = 'HOLD' if active_layer.blend_type == 'REPLACE' else 'HOLD_FORWARD'
                    if hasattr(strip, 'use_sync_length'):
                        strip.use_sync_length = True
                    try:
                        obj.animation_data.action_blend_type = active_layer.blend_type
                        obj.animation_data.action_extrapolation = 'HOLD' if active_layer.blend_type == 'REPLACE' else 'HOLD_FORWARD'
                    except: pass
                elif not active_track.strips:
                    # Create an empty strip so tweak mode has something to lock onto and blend type applies
                    empty_action = bpy.data.actions.new(name=active_track.name)
                        
                    strip = active_track.strips.new(
                        name=active_track.name,
                        start=1,
                        action=empty_action
                    )
                    strip.blend_type = active_layer.blend_type
                    strip.extrapolation = 'HOLD' if active_layer.blend_type == 'REPLACE' else 'HOLD_FORWARD'
                    if hasattr(strip, 'use_sync_length'):
                        strip.use_sync_length = True

                # Retroactively ensure all existing strips use true infinite mapping to bypass Tweak Mode freeze
                if active_track.strips:
                    existing_strip = active_track.strips[0]
                    existing_strip.blend_type = active_layer.blend_type
                    existing_strip.extrapolation = 'NOTHING' if active_layer.blend_type == 'REPLACE' else 'HOLD_FORWARD'
                    if hasattr(existing_strip, 'use_sync_length'):
                        existing_strip.use_sync_length = True
                active_track.strips[0].active = True
                
                try:
                    obj.animation_data.action_blend_type = active_layer.blend_type
                    obj.animation_data.action_extrapolation = 'HOLD' if active_layer.blend_type == 'REPLACE' else 'HOLD_FORWARD'
                except: pass
            except:
                pass
            
            # Try to assign the active track if the API supports it
            try:
                for t in obj.animation_data.nla_tracks:
                    t.is_solo = False
                active_track.is_solo = False
            except: pass
            
            # Ensure the action matches the layer state
            try:
                if active_layer.is_muted:
                    if getattr(obj.animation_data, 'use_tweak_mode', False):
                        for window in context.window_manager.windows:
                            for area in window.screen.areas:
                                if area.type == 'NLA_EDITOR':
                                    with context.temp_override(window=window, area=area, active_object=obj):
                                        try: bpy.ops.nla.tweakmode_exit(isolate_action=False)
                                        except: pass
                                    break
                    if not getattr(obj.animation_data, 'use_tweak_mode', False):
                        obj.animation_data.action = None
                elif active_track.strips:
                    if enter_tweak_mode:
                        safe_enter_tweak_mode(context, obj, active_track, active_track.strips[0])
                    # Ensure action does not float and double-evaluate if tweak mode is off
                    if not getattr(obj.animation_data, 'use_tweak_mode', False):
                        obj.animation_data.action = None
            except: pass
                
            # Ensure NLA track visibility is ON in Dopesheet so the user can still see base animation keyframes in the Timeline
            for window in context.window_manager.windows:
                for area in window.screen.areas:
                    if area.type in {'GRAPH_EDITOR', 'DOPESHEET_EDITOR'}:
                        if hasattr(area.spaces.active, 'dopesheet'):
                            try:
                                area.spaces.active.dopesheet.show_nla = True
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
        if exit_first and obj and obj.animation_data:
            if getattr(obj.animation_data, 'use_tweak_mode', False):
                try: bpy.ops.nla.tweakmode_exit(isolate_action=False)
                except: pass
            if not getattr(obj.animation_data, 'use_tweak_mode', False):
                try:
                    obj.animation_data.action = None
                except: pass
        execute_sync_logic(context, enter_tweak_mode=enter_second)
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
            if hasattr(target_area, "spaces"):
                for space in target_area.spaces:
                    if space.type == 'NLA_EDITOR':
                        override['space_data'] = space
                        break
            override['active_object'] = get_active_object(context)
            if override['active_object']:
                override['selected_objects'] = [override['active_object']]
            
            with context.temp_override(**override):
                if exit_first:
                    try: bpy.ops.nla.tweakmode_exit(isolate_action=False)
                    except:
                        try: bpy.ops.nla.tweakmode_exit()
                        except: pass
                    
                obj = get_active_object(context)
                if obj and obj.animation_data:
                    # CRITICAL: If tweakmode_exit failed (we are still in Tweak Mode), do NOT set action = None
                    # Otherwise Blender will permanently erase the action from the NLA strip!
                    if not getattr(obj.animation_data, 'use_tweak_mode', False):
                        try:
                            obj.animation_data.action = None  # Prevent old layer action from leaking
                        except: pass
                    
                execute_sync_logic(context, enter_tweak_mode=enter_second)
                
                # CRITICAL: Force a depsgraph update before entering Tweak Mode. 
                # If we don't, Blender caches the uninitialized strip state and COMBINE mode acts like REPLACE until the user manually switches layers.
                if context.view_layer:
                    context.view_layer.update()
                
                # Tweak Mode is already safely entered by execute_sync_logic
                
                # CRITICAL: Force another depsgraph update and tag the object after entering Tweak Mode.
                # If we don't, Blender's viewport gets stuck displaying the previous layer's poses until the user manually toggles a property like Mute.
                if context.view_layer:
                    context.view_layer.update()
                
                obj = get_active_object(context)
                if obj:
                    obj.update_tag(refresh={'OBJECT', 'DATA'})
                            
                    if context.view_layer:
                        context.view_layer.update()
        else:
            # Fallback if region generation failed
            execute_sync_logic(context, enter_tweak_mode=enter_second)
            
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

