import bpy
import gpu
from gpu_extras.batch import batch_for_shader
import mathutils

_draw_handler = None
_cached_data = {}

def get_bone_lines(obj):
    lines = []
    if obj.type != 'ARMATURE': return lines
    mat = obj.matrix_world
    
    for bone in obj.pose.bones:
        lines.extend([mat @ bone.head, mat @ bone.tail])
            
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
            lines.extend([mat @ v1, mat @ v2])
            
    else: # MESH mode
        eval_obj = obj.evaluated_get(depsgraph)
        mesh = eval_obj.to_mesh()
        mat = eval_obj.matrix_world
        
        mesh.transform(mat)
        
        settings = getattr(bpy.context.scene, 'lsd_anim_settings', None)
        resolution = settings.onion_skin_mesh_resolution if settings else 1.0
        step = max(1, int(1.0 / max(0.01, resolution)))
        
        verts = mesh.vertices
        for i, edge in enumerate(mesh.edges):
            if i % step != 0: continue
            v1 = verts[edge.vertices[0]].co
            v2 = verts[edge.vertices[1]].co
            lines.extend(((v1.x, v1.y, v1.z), (v2.x, v2.y, v2.z)))
            
        eval_obj.to_mesh_clear()
        
    return lines
    


def draw_callback():
    if not _cached_data: return
    
    context = bpy.context
    settings = getattr(context.scene, 'lsd_anim_settings', None)
    if not settings or not settings.onion_skin_enabled:
        return
        
    shader = gpu.shader.from_builtin('UNIFORM_COLOR')
    gpu.state.blend_set('ALPHA')
    gpu.state.line_width_set(2.0)
    
    current_frame = context.scene.frame_current
    
    for frame, data in _cached_data.items():
        if isinstance(data, list):
            if not data: continue
            batch = batch_for_shader(shader, 'LINES', {"pos": data})
            _cached_data[frame] = batch
        else:
            batch = data
            
        if frame < current_frame:
            if not getattr(settings, 'onion_skin_show_past', True): continue
            base_opacity = settings.onion_skin_opacity_before
            if getattr(settings, 'onion_skin_fade', False) and settings.onion_skin_count_before >= max(1, settings.onion_skin_frame_distance):
                frame_dist = max(1, settings.onion_skin_frame_distance)
                n = (abs(current_frame - frame) + frame_dist - 1) // frame_dist
                max_n = settings.onion_skin_count_before // frame_dist
                if max_n > 1:
                    base_opacity *= max(0.0, 1.0 - (n - 1) / (max_n - 1))
            color = list(settings.onion_skin_color_past) + [base_opacity]
        elif frame > current_frame:
            if not getattr(settings, 'onion_skin_show_future', True): continue
            base_opacity = settings.onion_skin_opacity_after
            if getattr(settings, 'onion_skin_fade', False) and settings.onion_skin_count_after >= max(1, settings.onion_skin_frame_distance):
                frame_dist = max(1, settings.onion_skin_frame_distance)
                n = (abs(current_frame - frame) + frame_dist - 1) // frame_dist
                max_n = settings.onion_skin_count_after // frame_dist
                if max_n > 1:
                    base_opacity *= max(0.0, 1.0 - (n - 1) / (max_n - 1))
            color = list(settings.onion_skin_color_future) + [base_opacity]
        else:
            if not getattr(settings, 'onion_skin_show_present', False): continue
            color = list(settings.onion_skin_color_present) + [1.0]
            
        shader.bind()
        
        gpu.state.line_width_set(2.0)
        shader.uniform_float("color", color)
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
    
    start_frame = orig_frame
    if getattr(settings, 'onion_skin_show_past', True):
        start_frame -= frames_before
        
    end_frame = orig_frame
    if getattr(settings, 'onion_skin_show_future', True):
        end_frame += frames_after
        
    frames_to_cache = []
    
    first_mult = start_frame - (start_frame % frame_step)
    if first_mult < start_frame:
        first_mult += frame_step
        
    curr = first_mult
    while curr <= end_frame:
        frames_to_cache.append(curr)
        curr += frame_step
            
    if getattr(settings, 'onion_skin_show_present', False):
        if orig_frame not in frames_to_cache:
            frames_to_cache.append(orig_frame)
        
    depsgraph = context.evaluated_depsgraph_get()
    
    _is_building = True
    
    frames_to_remove = [f for f in _cached_data.keys() if f not in frames_to_cache]
    for f in frames_to_remove:
        del _cached_data[f]
        
    frames_to_build = [f for f in frames_to_cache if f not in _cached_data]
    
    if frames_to_build:
        for f in frames_to_build:
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

