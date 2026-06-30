import sys
import re

filepath = r'c:\Users\japzo\OneDrive\Desktop\Blender Add-on Workshop\Layouts-Systems-Draftsman-Toolkit-Addon\operators.py'
with open(filepath, 'r', encoding='utf-8') as f:
    c = f.read()

new_operators = '''
class LSD_OT_Quick_SDF_Boolean(bpy.types.Operator):
    """Automatically assigns the cutter and executes the boolean."""
    bl_idname = "lsd.quick_sdf_boolean"
    bl_label = "Quick SDF Boolean"
    bl_options = {'REGISTER', 'UNDO'}
    
    operation: bpy.props.StringProperty(name="Operation", default='UNION')
    
    def execute(self, context):
        active = context.active_object
        selected = [o for o in context.selected_objects if o != active]
        if not active or not selected:
            return {'CANCELLED'}
        cutter = selected[0]
        
        # Prevent double triggering
        from . import properties
        properties._lsd_is_batch_updating = True
        try:
            active.lsd_pg_sdf_props.target_object = cutter
            active.lsd_pg_sdf_props.operation = self.operation
        finally:
            properties._lsd_is_batch_updating = False
            
        cutter.display_type = 'BOUNDS'
        
        from . import generators
        generators.setup_sdf_booleans(active)
        return {'FINISHED'}

class LSD_OT_Toggle_Cutter_Visibility(bpy.types.Operator):
    """Toggles the viewport display type of the cutter object"""
    bl_idname = "lsd.toggle_cutter_visibility"
    bl_label = "Toggle Cutter Visibility"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        obj = context.active_object
        if obj and obj.lsd_pg_sdf_props.target_object:
            cutter = obj.lsd_pg_sdf_props.target_object
            if cutter.display_type == 'BOUNDS':
                cutter.display_type = 'TEXTURED'
            else:
                cutter.display_type = 'BOUNDS'
        return {'FINISHED'}
'''

# Find the end of LSD_OT_Apply_SDF_Booleans
target = "        return {'FINISHED'}"
parts = c.split('class LSD_OT_Apply_SDF_Booleans', 1)
if len(parts) == 2:
    subparts = parts[1].split(target, 1)
    if len(subparts) == 2:
        new_c = parts[0] + 'class LSD_OT_Apply_SDF_Booleans' + subparts[0] + target + new_operators + subparts[1]
        
        # Also register the classes
        reg_target = "CLASSES = ["
        reg_replacement = "CLASSES = [\n        LSD_OT_Quick_SDF_Boolean, LSD_OT_Toggle_Cutter_Visibility,"
        new_c = new_c.replace(reg_target, reg_replacement, 1)
        
        with open(filepath, 'w', encoding='utf-8', newline='\r\n') as f:
            f.write(new_c)
        print('SUCCESS')
