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
from typing import List, Tuple, Optional, Set, Any, Dict, Union
from . import core
from .config import (
    MOD_PREFIX, CUTTER_PREFIX, BOOL_PREFIX, WELD_THRESHOLD,
    NATIVE_SPRING_MOD_NAME, NATIVE_DAMPER_MOD_NAME, NATIVE_SLINKY_MOD_NAME
)

# ------------------------------------------------------------------------
#   BMesh Dispatcher & Regeneration Handlers
# ------------------------------------------------------------------------

def update_mesh_wrapper(self, context: bpy.types.Context):
    """
    Standard 'update' callback for parametric properties.
    Ensures changes propagate to all selected objects and follows
    the strict separation of concerns mandate.
    """
    owner_obj = self.id_data
    if not owner_obj or not hasattr(self, "is_part") or not self.is_part:
        return

    # Trigger synchronization across all selected items
    for obj in context.selected_objects:
        if obj.type == 'MESH' and hasattr(obj, "fcd_pg_mech_props"):
            if obj.fcd_pg_mech_props.is_part:
                regenerate_mech_mesh(obj, context)
                sync_part_to_bone_gizmo(obj, context)

def sync_part_to_bone_gizmo(obj: bpy.types.Object, context: bpy.types.Context):
    """Syncs the part's primary radius to the parent bone's gizmo radius."""
    if obj.parent and obj.parent_type == 'BONE' and obj.parent.type == 'ARMATURE':
        props = obj.fcd_pg_mech_props
        r = 0.05
        # Sync the radius property from the part to the bone's kinematic properties
        if props.category == 'GEAR': r = props.gear_radius
        elif props.category == 'WHEEL': r = props.wheel_radius
        elif props.category == 'PULLEY': r = props.pulley_radius
        elif props.category == 'BASIC_JOINT': r = props.joint_radius
        
        u = context.scene.unit_settings.scale_length
        s = 1.0 / u if u > 0 else 1.0
        
        pbone = obj.parent.pose.bones.get(obj.parent_bone)
        if pbone and hasattr(pbone, "fcd_pg_kinematic_props"):
            pbone.fcd_pg_kinematic_props.joint_radius = r * s
            if hasattr(core, 'update_single_bone_gizmo'):
                core.update_single_bone_gizmo(pbone, context.scene.fcd_viz_gizmos)

def regenerate_mech_mesh(obj: bpy.types.Object, context: bpy.types.Context):
    """The central entry point for procedural mesh construction."""
    if not obj or not hasattr(obj, "fcd_pg_mech_props") or not obj.fcd_pg_mech_props.is_part:
        return
    
    props = obj.fcd_pg_mech_props

    # 1. Non-BMesh Categories (Geometry Nodes or Curve based)
    if props.category == 'SPRING':
        update_native_spring_properties(obj, props, context)
        return
    elif props.category == 'CHAIN':
        target_obj = props.instanced_link_obj
        if target_obj:
            update_mesh_data(target_obj, context, lambda bm: generate_chain_link_mesh(bm, props))
        update_native_chain_properties(obj, props, context)
        return
    elif props.category == 'ROPE':
        update_mesh_data(obj, context, lambda bm: generate_rope_mesh(bm, props))
        update_native_rope_properties(obj, props, context)
        return

    # 2. Standard BMesh Bounding Box/Generation Categories
    update_mesh_data(obj, context, lambda bm: dispatch_generation(bm, props, obj, context))
    
    # --- AI Editor Note: Sub-Component Regeneration ---
    # We must also regenerate all stationary or auxiliary objects (stator, screw, etc.)
    for attr in ["joint_stator_obj", "joint_screw_obj", "joint_pin_obj"]:
        sub_obj = getattr(props, attr, None)
        if sub_obj and sub_obj.type == 'MESH':
            # Use specific generator logic for the sub-object
            update_mesh_data(sub_obj, context, lambda bm: generate_stator_mesh(bm, props, sub_obj, context))
    
    # 3. Post-generation Modifiers and Shading
    finalize_modifiers(obj, props, context)

def update_mesh_data(obj: bpy.types.Object, context: bpy.types.Context, gen_func):
    """Generic BMesh lifecycle handler ensuring memory safety and clean geometry."""
    bm = bmesh.new()
    try:
        gen_func(bm)
        if bm.verts:
            # Rule 6: Mandatory Memory Cycle & Cleaning
            bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=WELD_THRESHOLD)
            bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
            obj.data.clear_geometry()
            bm.to_mesh(obj.data)
            obj.data.update()
    finally:
        bm.free()

def dispatch_generation(bm: bmesh.types.BMesh, props, obj, context):
    """Dispatches to specific generator logic based on category."""
    cat = props.category
    if cat == 'GEAR': generate_gear_mesh(bm, props, obj)
    elif cat == 'RACK': generate_rack_mesh(bm, props, obj)
    elif cat == 'FASTENER': generate_fastener_mesh(bm, props, obj, context)
    elif cat == 'ELECTRONICS': generate_electronics_mesh(bm, props, obj)
    elif cat == 'WHEEL': generate_wheel_mesh(bm, props, obj)
    elif cat == 'PULLEY': generate_pulley_mesh(bm, props, obj)
    elif cat == 'BASIC_JOINT': generate_basic_joint_mesh(bm, props, obj, context)
    elif cat == 'BASIC_SHAPE': generate_basic_shape_mesh(bm, props, obj)
    elif cat == 'ARCHITECTURAL': generate_architectural_mesh(bm, props, obj)
    elif cat == 'VEHICLE': generate_vehicle_mesh(bm, props, obj)

# ------------------------------------------------------------------------
#   GENERATION LOGIC
# ------------------------------------------------------------------------

def generate_gear_mesh(bm: bmesh.types.BMesh, props, obj):
    """Procedural circular gear construction."""
    unit_scale = bpy.context.scene.unit_settings.scale_length
    s = 1.0 / unit_scale if unit_scale > 0 else 1.0
    
    teeth = max(1, props.gear_teeth_count)
    segs = teeth * 2
    rad = props.gear_radius * s
    width = props.gear_width * s
    depth = props.gear_tooth_depth * s
    taper = props.gear_tooth_taper

    if props.type_gear == 'INTERNAL':
        outer_rad = max(props.gear_outer_radius * s, rad + depth + 0.05*s)
        mat = mathutils.Matrix.Translation((0,0,-width/2))
        res_outer = bmesh.ops.create_circle(bm, radius=outer_rad, segments=segs, matrix=mat)
        res_inner = bmesh.ops.create_circle(bm, radius=rad, segments=segs, matrix=mat)
        edges = list({e for v in res_outer['verts']+res_inner['verts'] for e in v.link_edges})
        bmesh.ops.bridge_loops(bm, edges=edges)
        res_ex = bmesh.ops.extrude_face_region(bm, geom=list(bm.faces))
        bmesh.ops.translate(bm, verts=[v for v in res_ex['geom'] if isinstance(v, bmesh.types.BMVert)], vec=(0,0,width))
        faces = [f for f in bm.faces if len(f.verts)==4 and abs(f.normal.z)<0.1]
    else:
        bmesh.ops.create_cone(bm, cap_ends=True, radius1=rad, radius2=rad, depth=width, segments=segs)
        faces = [f for f in bm.faces if len(f.verts)==4 and abs(f.normal.z)<0.1]
    
    faces.sort(key=lambda f: math.atan2(f.calc_center_median().y, f.calc_center_median().x))
    faces_to_extrude = faces[::2]
    
    for f in faces_to_extrude:
        ex = bmesh.ops.extrude_face_region(bm, geom=[f])
        new_f = [g for g in ex['geom'] if isinstance(g, bmesh.types.BMFace)][0]
        ext_dir = new_f.normal if props.type_gear != 'INTERNAL' else -new_f.normal
        bmesh.ops.translate(bm, verts=new_f.verts, vec=ext_dir * depth)
        c = new_f.calc_center_median()
        bmesh.ops.transform(bm, matrix=mathutils.Matrix.Translation(c) @ mathutils.Matrix.Diagonal((taper, taper, 1.0, 1.0)) @ mathutils.Matrix.Translation(-c), verts=new_f.verts)

def generate_rack_mesh(bm: bmesh.types.BMesh, props, obj):
    """Procedural rack segment construction with array setup."""
    unit_scale = bpy.context.scene.unit_settings.scale_length
    s = 1.0 / unit_scale if unit_scale > 0 else 1.0
    
    teeth = max(1, props.rack_teeth_count)
    total_l = props.rack_length * s
    seg_l = total_l / teeth
    w = props.rack_width * s
    h = props.rack_height * s
    d = props.rack_tooth_depth * s
    
    bmesh.ops.create_cube(bm, size=1.0)
    bmesh.ops.scale(bm, verts=bm.verts, vec=(seg_l, w, h))
    bmesh.ops.translate(bm, verts=bm.verts, vec=(seg_l/2, 0, -h/2))
    
    top = max((f for f in bm.faces if f.normal.z > 0.5), key=lambda f: f.calc_center_median().z, default=None)
    if top:
        ex = bmesh.ops.extrude_face_region(bm, geom=[top])
        bmesh.ops.translate(bm, verts=[v for v in ex['geom'] if isinstance(v, bmesh.types.BMVert)], vec=(0,0,d))
        new_top = max((f for f in ex['geom'] if isinstance(f, bmesh.types.BMFace) and f.normal.z > 0.1), key=lambda f: f.calc_center_median().z, default=None)
        if new_top:
            c = new_top.calc_center_median()
            bmesh.ops.transform(bm, matrix=mathutils.Matrix.Translation(c) @ mathutils.Matrix.Diagonal((props.gear_tooth_taper, 1.0, 1.0, 1.0)) @ mathutils.Matrix.Translation(-c), verts=new_top.verts)
    
    # ARRAY MODIFIER SYNC
    mod_name = f"{MOD_PREFIX}Rack_Array"
    mod = obj.modifiers.get(mod_name) or obj.modifiers.new(mod_name, 'ARRAY')
    mod.fit_type = 'FIXED_COUNT'; mod.count = teeth; mod.use_relative_offset = False; mod.use_constant_offset = True
    mod.constant_offset_displace = (seg_l, 0, 0)
    weld_name = f"{MOD_PREFIX}Rack_Weld"
    if weld_name not in obj.modifiers: obj.modifiers.new(weld_name, 'WELD').merge_threshold = WELD_THRESHOLD

def generate_fastener_mesh(bm: bmesh.types.BMesh, props, obj, context):
    unit_scale = bpy.context.scene.unit_settings.scale_length
    s = 1.0 / unit_scale if unit_scale > 0 else 1.0
    r = props.fastener_radius * s
    l = props.fastener_length * s
    bmesh.ops.create_cone(bm, cap_ends=True, radius1=r, radius2=r, depth=l, segments=12)

def generate_electronics_mesh(bm: bmesh.types.BMesh, props, obj):
    unit_scale = bpy.context.scene.unit_settings.scale_length
    s = 1.0 / unit_scale if unit_scale > 0 else 1.0
    if 'MOTOR' in props.type_electronics:
        r = props.joint_motor_radius * s; l = props.joint_motor_length * s
        bmesh.ops.create_cone(bm, cap_ends=True, radius1=r, radius2=r, depth=l, segments=32)
        if props.joint_motor_shaft:
            sl = props.joint_motor_shaft_length * s; sr = props.joint_motor_shaft_radius * s
            bmesh.ops.create_cone(bm, cap_ends=True, radius1=sr, radius2=sr, depth=sl, segments=12, matrix=mathutils.Matrix.Translation((0,0,l/2+sl/2)))
    else:
        # Default box fallback
        bmesh.ops.create_cube(bm, size=0.05*s)

def generate_wheel_mesh(bm: bmesh.types.BMesh, props, obj):
    unit_scale = bpy.context.scene.unit_settings.scale_length
    s = 1.0 / unit_scale if unit_scale > 0 else 1.0
    r = props.wheel_radius * s; w = props.wheel_width * s
    bmesh.ops.create_cone(bm, cap_ends=True, radius1=r, radius2=r, depth=w, segments=32)
    bmesh.ops.rotate(bm, verts=bm.verts, cent=(0,0,0), matrix=mathutils.Matrix.Rotation(math.radians(90), 4, 'X'))

def generate_pulley_mesh(bm: bmesh.types.BMesh, props, obj):
    unit_scale = bpy.context.scene.unit_settings.scale_length
    s = 1.0 / unit_scale if unit_scale > 0 else 1.0
    r = props.pulley_radius * s; w = props.pulley_width * s
    bmesh.ops.create_cone(bm, cap_ends=True, radius1=r, radius2=r, depth=w, segments=32)

def generate_stator_mesh(bm: bmesh.types.BMesh, props, obj, context):
    """Generates the stationary (base) components of a mechatronic joint."""
    unit_scale = bpy.context.scene.unit_settings.scale_length
    s = 1.0 / unit_scale if unit_scale > 0 else 1.0
    r = props.joint_radius * s; w = props.joint_width * s

    if props.type_basic_joint == 'JOINT_REVOLUTE':
        # Frame (Stator)
        fw = props.joint_frame_width * s; fl = props.joint_frame_length * s
        # Align frame with the eye/axis
        bmesh.ops.create_cube(bm, size=1.0, matrix=mathutils.Matrix.Translation((0, -fl/2 - r, 0)) @ mathutils.Matrix.Scale(fw, 4, (1,0,0)) @ mathutils.Matrix.Scale(fl, 4, (0,1,0)) @ mathutils.Matrix.Scale(w, 4, (0,0,1)))
    
    elif props.type_basic_joint == 'JOINT_CONTINUOUS':
        # Motor Body (Stator)
        br = props.joint_base_radius * s; bl = props.joint_base_length * s
        bmesh.ops.create_cone(bm, cap_ends=True, radius1=br, radius2=br, depth=bl, segments=32)
    
    elif props.type_basic_joint == 'JOINT_PRISMATIC':
        # Screw Shaft (Stator) - Reoriented to VERTICAL (Z)
        bmesh.ops.create_cone(bm, cap_ends=True, radius1=r, radius2=r, depth=w, segments=16)
    
    elif 'WHEELS' in props.type_basic_joint:
        # Rack Rail (Stator) - Already Vertical (Z)
        rl = props.rack_length * s; rw = props.rack_width * s; rt = props.joint_sub_thickness * s
        bmesh.ops.create_cube(bm, size=1.0, matrix=mathutils.Matrix.Scale(rt, 4, (1,0,0)) @ mathutils.Matrix.Scale(rw, 4, (0,1,0)) @ mathutils.Matrix.Scale(rl, 4, (0,0,1)))

def generate_basic_joint_mesh(bm: bmesh.types.BMesh, props, obj, context):
    """Generates the moving (rotor/carriage) components of a mechatronic joint."""
    unit_scale = bpy.context.scene.unit_settings.scale_length
    s = 1.0 / unit_scale if unit_scale > 0 else 1.0
    r = props.joint_radius * s; w = props.joint_width * s
    sub_s = props.joint_sub_size * s; sub_t = props.joint_sub_thickness * s

    if props.type_basic_joint == 'JOINT_REVOLUTE':
        # Eye (Cylinder)
        bmesh.ops.create_cone(bm, cap_ends=True, radius1=r, radius2=r, depth=w, segments=32)
        # Pin
        pr = props.joint_pin_radius * s
        bmesh.ops.create_cone(bm, cap_ends=True, radius1=pr, radius2=pr, depth=w*1.5, segments=16)
        
        # --- Rotor Arm Implementation ---
        al = props.rotor_arm_length * s; aw = props.rotor_arm_width * s; ah = props.rotor_arm_height * s
        # Arm extends outward from the eye (Y axis in current frame logic)
        bmesh.ops.create_cube(bm, size=1.0, matrix=mathutils.Matrix.Translation((0, al/2 + r, 0)) @ mathutils.Matrix.Scale(aw, 4, (1,0,0)) @ mathutils.Matrix.Scale(al, 4, (0,1,0)) @ mathutils.Matrix.Scale(ah, 4, (0,0,1)))

    elif props.type_basic_joint == 'JOINT_CONTINUOUS':
        # Shaft Only (Rotor)
        sr = props.joint_motor_shaft_radius * s; sl = props.joint_motor_shaft_length * s
        bl = props.joint_base_length * s
        bmesh.ops.create_cone(bm, cap_ends=True, radius1=sr, radius2=sr, depth=sl, segments=12, matrix=mathutils.Matrix.Translation((0,0,bl/2+sl/2)))
        
        # --- Rotor Arm (Optional for motors) ---
        al = props.rotor_arm_length * s; aw = props.rotor_arm_width * s; ah = props.rotor_arm_height * s
        if al > 0:
             bmesh.ops.create_cube(bm, size=1.0, matrix=mathutils.Matrix.Translation((0, al/2 + sr, bl/2 + sl - ah/2)) @ mathutils.Matrix.Scale(aw, 4, (1,0,0)) @ mathutils.Matrix.Scale(al, 4, (0,1,0)) @ mathutils.Matrix.Scale(ah, 4, (0,0,1)))

    elif props.type_basic_joint == 'JOINT_PRISMATIC':
        # Nut Block Only (Rotor) - Influenced by moving gizmo
        # Logic: Moves along the Screw Shaft (Z)
        bmesh.ops.create_cube(bm, size=sub_s)
    
    elif props.type_basic_joint == 'JOINT_SPHERICAL':
        # Ball and Socket
        bmesh.ops.create_uvsphere(bm, u_segments=32, v_segments=16, radius=r)
        sr = props.joint_pin_radius * s; sl = props.joint_pin_length * s
        bmesh.ops.create_cone(bm, cap_ends=True, radius1=sr, radius2=sr, depth=sl, segments=12, matrix=mathutils.Matrix.Translation((0,0,r+sl/2)))

    elif 'WHEELS' in props.type_basic_joint:
        # Carriage & Wheels (Rotor)
        cw = props.joint_carriage_width * s; cl = props.joint_sub_size * s; ct = props.joint_carriage_thickness * s
        wt = props.wheel_thickness * s; wr = props.joint_radius * s
        
        # Carriage Plate (Vertical in XZ, moves on Z)
        # Note: Original code was oriented differently, reorienting to vertical rack rail.
        bmesh.ops.create_cube(bm, size=1.0, matrix=mathutils.Matrix.Scale(cw, 4, (1,0,0)) @ mathutils.Matrix.Scale(ct, 4, (0,1,0)) @ mathutils.Matrix.Scale(cl, 4, (0,0,1)))
        
        # Wheels
        for side in [-1, 1]:
            for end in [-1, 1]:
                mat = mathutils.Matrix.Translation((side * (cw/2 + wt/2), 0, end * (cl/2 - wr))) @ mathutils.Matrix.Rotation(math.radians(90), 4, 'Y')
                bmesh.ops.create_cone(bm, cap_ends=True, radius1=wr, radius2=wr, depth=wt, segments=16, matrix=mat)
    else:
        # Default simple cylinder
        bmesh.ops.create_cone(bm, cap_ends=True, radius1=r, radius2=r, depth=w, segments=32)

def generate_basic_shape_mesh(bm: bmesh.types.BMesh, props, obj):
    unit_scale = bpy.context.scene.unit_settings.scale_length
    s = 1.0 / unit_scale if unit_scale > 0 else 1.0
    
    t = props.type_basic_shape
    if t == 'SHAPE_PLANE':
        sz = props.shape_size * s
        bmesh.ops.create_grid(bm, x_segments=1, y_segments=1, size=sz/2)
    elif t == 'SHAPE_CUBE':
        # Use individual axes
        lx = props.shape_length_x * s; wy = props.shape_width_y * s; hz = props.shape_height_z * s
        bmesh.ops.create_cube(bm, size=1.0, matrix=mathutils.Matrix.Scale(lx, 4, (1,0,0)) @ mathutils.Matrix.Scale(wy, 4, (0,1,0)) @ mathutils.Matrix.Scale(hz, 4, (0,0,1)))
    elif t == 'SHAPE_CIRCLE':
        bmesh.ops.create_circle(bm, cap_ends=True, radius=props.shape_radius*s, segments=props.shape_vertices)
    elif t == 'SHAPE_CYLINDER':
        bmesh.ops.create_cone(bm, cap_ends=True, radius1=props.shape_radius*s, radius2=props.shape_radius*s, depth=props.shape_height*s, segments=props.shape_vertices)
    elif t == 'SHAPE_UVSPHERE':
        bmesh.ops.create_uvsphere(bm, u_segments=props.shape_segments, v_segments=props.shape_segments//2, radius=props.shape_radius*s)
    elif t == 'SHAPE_ICOSPHERE':
        bmesh.ops.create_icosphere(bm, subdivisions=props.shape_subdivisions, radius=props.shape_radius*s)
    elif t == 'SHAPE_CONE':
        bmesh.ops.create_cone(bm, cap_ends=True, radius1=props.shape_radius*s, radius2=0, depth=props.shape_height*s, segments=props.shape_vertices)
    elif t == 'SHAPE_TORUS':
        bmesh.ops.create_torus(bm, major_radius=props.shape_major_radius*s, minor_radius=props.shape_tube_radius*s, major_segments=props.shape_horizontal_segments, minor_segments=props.shape_vertical_segments)
    else:
        bmesh.ops.create_cube(bm, size=0.1*s)

def generate_architectural_mesh(bm: bmesh.types.BMesh, props, obj):
    unit_scale = bpy.context.scene.unit_settings.scale_length
    s = 1.0 / unit_scale if unit_scale > 0 else 1.0
    bmesh.ops.create_cube(bm, size=1.0)

def generate_vehicle_mesh(bm: bmesh.types.BMesh, props, obj):
    unit_scale = bpy.context.scene.unit_settings.scale_length
    s = 1.0 / unit_scale if unit_scale > 0 else 1.0
    bmesh.ops.create_cube(bm, size=1.0)

def generate_rope_mesh(bm, props):
    unit_scale = bpy.context.scene.unit_settings.scale_length
    s = 1.0 / unit_scale if unit_scale > 0 else 1.0
    r = props.rope_radius * s; l = props.rope_length * s
    bmesh.ops.create_cone(bm, cap_ends=True, radius1=r, radius2=r, depth=l, segments=12, matrix=mathutils.Matrix.Rotation(math.radians(90), 4, 'Y'))

def generate_chain_link_mesh(bm: bmesh.types.BMesh, props):
    unit_scale = bpy.context.scene.unit_settings.scale_length
    s = 1.0 / unit_scale if unit_scale > 0 else 1.0
    p = props.chain_pitch * s; r = props.chain_roller_radius * s
    bmesh.ops.create_cone(bm, cap_ends=True, radius1=r, radius2=r, depth=props.chain_roller_length*s, segments=16)

# ------------------------------------------------------------------------
#   POST-GENERATION HELPERS
# ------------------------------------------------------------------------

def finalize_modifiers(obj, props, context):
    if props.category == 'GEAR' and props.type_gear != 'INTERNAL' and props.gear_bore_radius > 0:
        setup_bore_hole(obj, props, context)
    else:
        m = obj.modifiers.get(f"{MOD_PREFIX}Bore")
        if m: obj.modifiers.remove(m)
        c = bpy.data.objects.get(f"{CUTTER_PREFIX}{obj.name}")
        if c: bpy.data.objects.remove(c, do_unlink=True)
    
    if props.category != 'BASIC_SHAPE':
        core.apply_auto_smooth(obj)

def setup_bore_hole(obj, props, context):
    cutter_name = f"{CUTTER_PREFIX}{obj.name}"
    cutter = bpy.data.objects.get(cutter_name)
    if not cutter:
        m = bpy.data.meshes.new(cutter_name)
        cutter = bpy.data.objects.new(cutter_name, m)
        context.collection.objects.link(cutter)
    cutter.parent = obj; cutter.hide_set(True)
    cutter.matrix_local = mathutils.Matrix.Identity(4)
    cutter.data.clear_geometry()
    
    u = context.scene.unit_settings.scale_length
    s = 1.0 / u if u > 0 else 1.0
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, radius1=props.gear_bore_radius*s, radius2=props.gear_bore_radius*s, depth=props.gear_width*4*s, segments=32)
    bm.to_mesh(cutter.data); bm.free(); cutter.data.update()
    for p in cutter.data.polygons: p.use_smooth = True
    
    mod = obj.modifiers.get(f"{MOD_PREFIX}Bore") or obj.modifiers.new(name=f"{MOD_PREFIX}Bore", type='BOOLEAN')
    mod.operation = 'DIFFERENCE'; mod.solver = 'EXACT'; mod.object = cutter

# ------------------------------------------------------------------------
#   NATIVE PROPERTY SYNC
# ------------------------------------------------------------------------

def update_native_spring_properties(obj, props, context):
    u = context.scene.unit_settings.scale_length
    s = 1.0 / u if u > 0 else 1.0
    obj["spring_teeth"] = props.spring_turns
    obj["spring_radius"] = props.spring_radius * s
    obj["spring_wire_thickness"] = props.spring_wire_thickness * s

def update_native_chain_properties(obj, props, context):
    u = context.scene.unit_settings.scale_length
    s = 1.0 / u if u > 0 else 1.0
    obj["fcd_native_chain_pitch"] = props.chain_pitch * s

def update_native_rope_properties(obj, props, context):
    obj["rope_radius"] = props.rope_radius
    obj["rope_strands"] = props.rope_strands
    obj["rope_twist"] = props.twist
