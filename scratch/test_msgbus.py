import bpy
output = ""

def msgbus_callback(*args):
    global output
    output += f"MsgBus triggered: {args}\n"
    
try:
    arm = bpy.data.armatures.new("Arm")
    obj = bpy.data.objects.new("ArmObj", arm)
    bpy.context.scene.collection.objects.link(obj)
    
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.mode_set(mode='EDIT')
    b = arm.edit_bones.new("Bone")
    b.head = (0,0,0)
    b.tail = (0,0,1)
    bpy.ops.object.mode_set(mode='POSE')
    
    pbone = obj.pose.bones["Bone"]
    
    owner = object()
    
    # Subscribe to ALL pose bones for this object
    subscribe_to = obj.pose.bones.path_resolve("['Bone'].location")
    output += f"Path: {subscribe_to}\n"
    
    # Wait, msgbus needs an exact RNA path.
    bpy.msgbus.subscribe_rna(
        key=pbone.path_resolve("location", False),
        owner=owner,
        args=(),
        notify=msgbus_callback,
    )
    
    # Simulate a change
    pbone.location = (1, 2, 3)
    bpy.context.view_layer.update()
    
    # Simulate a frame change (which shouldn't trigger msgbus for property edits)
    bpy.context.scene.frame_set(10)
    
    output += "Test complete.\n"
except Exception as e:
    output += f"Fatal error: {e}\n"

with open(r"C:\Users\japzo\OneDrive\Desktop\Blender Add-on Workshop\Layouts-Systems-Draftsman-Toolkit-Addon\scratch\test_msgbus_output.txt", "w") as f:
    f.write(output)
