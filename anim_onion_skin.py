import bpy
import gpu
from gpu_extras.batch import batch_for_shader
import mathutils

_draw_handler = None
_cached_data = {}

def get_bone_lines(obj):
    lines = []
    if obj.type != 'ARMATURE': return lines
    # Calculate world space head and tail for each bone
    mat = obj.matrix_world
    for bone in obj.pose.bones:
        lines.append(mat @ bone.head)
        lines.append(mat @ bone.tail)
    return lines

def get_mesh_lines(obj, depsgraph, display_type='BOUNDS'):
    lines = []
    if obj.type != 'MESH': return lines
    
    if display_type == 'BOUNDS':
        bbox = obj.bound_box
        if not bbox: return lines
        
        eval_obj = obj.evaluated_get(depsgraph)
        mat = eval_obj.matrix_world
        
        edges = [
            (0,1), (1,2), (2,3), (3,0),
            (4,5), (5,6), (6,7), (7,4),
            (0,4), (1,5), (2,6), (3,7)
        ]
        
        for e1, e2 in edges:
            v1 = mathutils.Vector(bbox[e1])
            v2 = mathutils.Vector(bbox[e2])
            lines.append(mat @ v1)
            lines.append(mat @ v2)
            
    else: # MESH mode
        eval_obj = obj.evaluated_get(depsgraph)
        mesh = eval_obj.to_mesh()
        mat = eval_obj.matrix_world
        
        # O(N) pseudo-decimation logic
        settings = getattr(bpy.context.scene, 'lsd_anim_settings', None)
        resolution = settings.onion_skin_mesh_resolution if settings else 1.0
        step = max(1, int(1.0 / max(0.01, resolution)))
        
        for i, edge in enumerate(mesh.edges):
            if i % step != 0: continue
            v1 = mesh.vertices[edge.vertices[0]].co
            v2 = mesh.vertices[edge.vertices[1]].co
            lines.append(mat @ v1)
            lines.append(mat @ v2)
            
        eval_obj.to_mesh_clear()
        
    return lines
    


def draw_callback():
    if not _cached_data: return
    
    context = bpy.context
    settings = getattr(context.scene, 'lsd_anim_settings', None)
    if not settings or not settings.onion_skin_enabled or not settings.layers_enabled:
        return
        
    shader = gpu.shader.from_builtin('UNIFORM_COLOR')
    gpu.state.blend_set('ALPHA')
    gpu.state.line_width_set(2.0)
    
    current_frame = context.scene.frame_current
    
    for frame, lines in _cached_data.items():
        if not lines: continue
        
        if frame < current_frame:
            color = list(settings.onion_skin_color_past) + [settings.onion_skin_opacity_before]
        elif frame > current_frame:
            color = list(settings.onion_skin_color_future) + [settings.onion_skin_opacity_after]
        else:
            color = list(settings.onion_skin_color_present) + [1.0]
            
        shader.bind()
        shader.uniform_float("color", color)
        batch = batch_for_shader(shader, 'LINES', {"pos": lines})
        batch.draw(shader)
        
    gpu.state.blend_set('NONE')

_is_building = False

def build_onion_cache(context=None):
    global _is_building
    if _is_building: return
    
    if context is None:
        context = bpy.context
        
    settings = getattr(context.scene, 'lsd_anim_settings', None)
    if not settings or not settings.onion_skin_enabled: return
    
    target_objs = []
    if settings.onion_skin_target == 'SELECTED':
        target_objs = [o for o in context.selected_objects if o.type in {'ARMATURE', 'MESH'}]
        if settings.onion_skin_near_count > 0 and len(target_objs) > 0:
            center_loc = target_objs[0].matrix_world.translation
            all_vis = [o for o in context.visible_objects if o.type in {'ARMATURE', 'MESH'} and o not in target_objs]
            all_vis.sort(key=lambda o: (o.matrix_world.translation - center_loc).length)
            target_objs.extend(all_vis[:settings.onion_skin_near_count])
    else:
        target_objs = [o for o in context.visible_objects if o.type in {'ARMATURE', 'MESH'}]
        
    if not target_objs: return
    
    orig_frame = context.scene.frame_current
    frame_step = max(1, settings.onion_skin_frame_distance)
    frames_before = settings.onion_skin_count_before
    frames_after = settings.onion_skin_count_after
    
    frames_to_cache = []
    for i in range(frames_before, 0, -1):
        frames_to_cache.append(orig_frame - (i * frame_step))
    frames_to_cache.append(orig_frame)
    for i in range(1, frames_after + 1):
        frames_to_cache.append(orig_frame + (i * frame_step))
        
    depsgraph = context.evaluated_depsgraph_get()
    
    _is_building = True
    
    _cached_data.clear()
    
    for f in frames_to_cache:
        context.scene.frame_set(f)
        _cached_data[f] = []
        for obj in target_objs:
            if obj.type == 'ARMATURE':
                _cached_data[f].extend(get_bone_lines(obj))
            elif obj.type == 'MESH':
                _cached_data[f].extend(get_mesh_lines(obj, depsgraph, settings.onion_skin_display_type))
                
    context.scene.frame_set(orig_frame)
    _is_building = False

def onion_skin_timer_update():
    try:
        settings = getattr(bpy.context.scene, 'lsd_anim_settings', None)
    except:
        return 1.0
        
    if not settings: return 1.0
    
    if settings.onion_skin_enabled and settings.onion_skin_auto_refresh:
        build_onion_cache(bpy.context)
        for window in bpy.context.window_manager.windows:
            for area in window.screen.areas:
                if area.type == 'VIEW_3D':
                    area.tag_redraw()
        return max(0.1, settings.onion_skin_refresh_interval)
    else:
        return 1.0

def update_onion_skin(self, context):
    global _draw_handler
    settings = context.scene.lsd_anim_settings
    
    if settings.onion_skin_enabled:
        if _draw_handler is None:
            _draw_handler = bpy.types.SpaceView3D.draw_handler_add(draw_callback, (), 'WINDOW', 'POST_VIEW')
        build_onion_cache(context)
    else:
        if _draw_handler is not None:
            bpy.types.SpaceView3D.draw_handler_remove(_draw_handler, 'WINDOW')
            _draw_handler = None
        _cached_data.clear()
        
    if context.area:
        context.area.tag_redraw()

class LSD_OT_Calculate_Onion_Skin(bpy.types.Operator):
    bl_idname = "lsd.calculate_onion_skin"
    bl_label = "Calculate Ghosts"
    bl_description = "Bake the onion skin frames based on the current timeline position"
    
    def execute(self, context):
        build_onion_cache(context)
        if context.area:
            context.area.tag_redraw()
        return {'FINISHED'}

def register():
    bpy.utils.register_class(LSD_OT_Calculate_Onion_Skin)
    if not bpy.app.timers.is_registered(onion_skin_timer_update):
        bpy.app.timers.register(onion_skin_timer_update)

def unregister():
    if bpy.app.timers.is_registered(onion_skin_timer_update):
        bpy.app.timers.unregister(onion_skin_timer_update)
    bpy.utils.unregister_class(LSD_OT_Calculate_Onion_Skin)
    global _draw_handler
    if _draw_handler is not None:
        try:
            bpy.types.SpaceView3D.draw_handler_remove(_draw_handler, 'WINDOW')
        except:
            pass
        _draw_handler = None

