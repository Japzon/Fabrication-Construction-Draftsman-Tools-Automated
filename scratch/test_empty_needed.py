import bpy

output = ""
try:
    action = bpy.data.actions.new("TestSlotAction")
    arm = bpy.data.armatures.new("Arm")
    obj = bpy.data.objects.new("ArmObj", arm)
    
    bpy.context.scene.collection.objects.link(obj)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.mode_set(mode='EDIT')
    b = arm.edit_bones.new("Bone.001")
    b.head = (0,0,0)
    b.tail = (0,0,1)
    bpy.ops.object.mode_set(mode='POSE')
    
    if hasattr(action, 'slots'):
        slot = action.slots.new(name=obj.name, id_type='OBJECT')
        obj.animation_data_create()
        obj.animation_data.action = action
        obj.animation_data.action_slot = slot
        
        pbone = obj.pose.bones["Bone.001"]
        pbone.rotation_mode = 'QUATERNION'
        
        # Test 1: INSERTKEY_NEEDED on EMPTY action
        try:
            res = pbone.keyframe_insert("rotation_quaternion", options={'INSERTKEY_NEEDED'})
            output += f"1. rotation_quaternion with INSERTKEY_NEEDED on EMPTY action: {res}\n"
        except Exception as e:
            output += f"1. rotation_quaternion failed: {e}\n"
            
        import bpy_extras.anim_utils as anim_utils
        bag = anim_utils.action_get_channelbag_for_slot(action, slot)
        output += f"FCurves after test 1: {len(bag.fcurves) if bag else 0}\n"
        
    else:
        output += "No slots attribute on Action.\n"
except Exception as e:
    output += f"Fatal error: {e}\n"

with open(r"C:\Users\japzo\OneDrive\Desktop\Blender Add-on Workshop\Layouts-Systems-Draftsman-Toolkit-Addon\scratch\test_empty_needed_output.txt", "w") as f:
    f.write(output)
