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
        
        if context.scene.lsd_enable_directional_translate:
            box.label(text="Select object > Press G > Move mouse > Type distance", icon='INFO')
            box.label(text="Moves exactly in cursor direction.", icon='BLANK1')

classes = (
    LSD_PT_Workflow_Optimizer,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
