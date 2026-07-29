import bpy

output = ""
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
    try:
        res = pbone.keyframe_insert("location", options={'INSERTKEY_NEEDED'})
        output += f"Success with options: {res}\n"
    except Exception as e:
        output += f"options failed: {e}\n"
except Exception as e:
    output += f"Fatal error: {e}\n"

with open(r"C:\Users\japzo\OneDrive\Desktop\Blender Add-on Workshop\Layouts-Systems-Draftsman-Toolkit-Addon\scratch\test_options_output.txt", "w") as f:
    f.write(output)
