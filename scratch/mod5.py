import sys
import re

filepath = r'c:\Users\japzo\OneDrive\Desktop\Blender Add-on Workshop\Layouts-Systems-Draftsman-Toolkit-Addon\generators.py'
with open(filepath, 'r', encoding='utf-8') as f:
    c = f.read()

# We need to replace the entire setup_sdf_booleans function
def_start = c.find('def setup_sdf_booleans(obj: bpy.types.Object):')

new_func = '''def setup_sdf_booleans(obj: bpy.types.Object):
    """
    Sets up a Geometry Nodes modifier for SDF-based smooth booleans.
    Emulates SDF by utilizing Mesh Boolean followed by Volume voxelization
    for smooth, adjustable welding.
    """
    props = obj.lsd_pg_sdf_props
    target = props.target_object
    if not target:
        return
        
    mod_name = "LSD_SDF_Boolean"
    mod = obj.modifiers.get(mod_name) or obj.modifiers.new(mod_name, 'NODES')
    
    group_name = "LSD_SDF_Boolean_Group"
    # To handle dynamic changes (UNION vs DIFFERENCE), we recreate or clear the group
    group = bpy.data.node_groups.get(group_name)
    if group:
        bpy.data.node_groups.remove(group)
        
    group = bpy.data.node_groups.new(group_name, 'GeometryNodeTree')
    group.interface.new_socket("Geometry", in_out='INPUT', socket_type='NodeSocketGeometry')
    group.interface.new_socket("Geometry", in_out='OUTPUT', socket_type='NodeSocketGeometry')
    
    nodes = group.nodes
    links = group.links
    
    input_node = nodes.new('NodeGroupInput')
    output_node = nodes.new('NodeGroupOutput')
    
    obj_info = nodes.new('GeometryNodeObjectInfo')
    obj_info.transform_space = 'RELATIVE'
    obj_info.inputs['Object'].default_value = target
    
    mesh_vol = nodes.new('GeometryNodeMeshToVolume')
    mesh_vol.resolution_mode = 'VOXEL_SIZE'
    mesh_vol.inputs['Voxel Size'].default_value = props.voxel_size
    mesh_vol.inputs['Interior Band Width'].default_value = 100.0
    
    vol_mesh = nodes.new('GeometryNodeVolumeToMesh')
    vol_mesh.inputs['Adaptivity'].default_value = 0.025
    
    smooth = nodes.new('GeometryNodeSetShadeSmooth')
    smooth.inputs['Shade Smooth'].default_value = True
    
    if props.operation == 'UNION':
        # UNION: Bypass the slow Mesh Boolean node entirely! Use Join Geometry instead.
        join = nodes.new('GeometryNodeJoinGeometry')
        links.new(input_node.outputs['Geometry'], join.inputs['Geometry'])
        links.new(obj_info.outputs['Geometry'], join.inputs['Geometry'])
        links.new(join.outputs['Geometry'], mesh_vol.inputs['Mesh'])
    else:
        # DIFFERENCE / INTERSECT: Must use Exact Mesh Boolean to prevent vanishing on coplanar geometry
        mesh_bool = nodes.new('GeometryNodeMeshBoolean')
        mesh_bool.operation = props.operation
        mesh_bool.solver = 'EXACT'
        links.new(input_node.outputs['Geometry'], mesh_bool.inputs['Mesh 1'])
        links.new(obj_info.outputs['Geometry'], mesh_bool.inputs['Mesh 2'])
        links.new(mesh_bool.outputs['Mesh'], mesh_vol.inputs['Mesh'])
        
    links.new(mesh_vol.outputs['Volume'], vol_mesh.inputs['Volume'])
    links.new(vol_mesh.outputs['Mesh'], smooth.inputs['Geometry'])
    links.new(smooth.outputs['Geometry'], output_node.inputs['Geometry'])
        
    mod.node_group = group
    
    # Surface projection omitted for stability (Shrinkwrap collapses entire mesh)
    sw = obj.modifiers.get("LSD_SDF_Project")
    if sw: obj.modifiers.remove(sw)
'''

c = c[:def_start] + new_func

with open(filepath, 'w', encoding='utf-8', newline='\r\n') as f:
    f.write(c)
