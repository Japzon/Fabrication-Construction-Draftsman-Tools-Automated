import bpy

output = ""
try:
    action = bpy.data.actions.new("TestSlotAction")
    arm = bpy.data.armatures.new("Arm")
    obj = bpy.data.objects.new("ArmObj", arm)
    
    bpy.context.scene.collection.objects.link(obj)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.mode_set(mode='EDIT')
    b = arm.edit_bones.new("Bone")
    b.head = (0,0,0)
    b.tail = (0,0,1)
    bpy.ops.object.mode_set(mode='POSE')
    
    if hasattr(action, 'slots'):
        # CREATE THE SLOT
        slot = action.slots.new(name=obj.name, id_type=obj.id_type if hasattr(obj, 'id_type') else 'OBJECT')
        
        # ASSIGN ACTION AND SLOT
        obj.animation_data_create()
        obj.animation_data.action = action
        obj.animation_data.action_slot = slot
        
        # KEYFRAME
        pbone = obj.pose.bones["Bone"]
        res = pbone.keyframe_insert("location")
        output += f"bone.keyframe_insert result: {res}\n"
        
        # CHECK IF FCURVES EXIST
        try:
            import bpy_extras.anim_utils as anim_utils
            bag = anim_utils.action_get_channelbag_for_slot(action, slot)
            output += f"Bag FCurves length: {len(bag.fcurves)}\n"
        except Exception as e:
            output += f"Error checking fcurves: {e}\n"
            
    else:
        output += "No slots attribute on Action.\n"
except Exception as e:
    output += f"Fatal error: {e}\n"

with open(r"C:\Users\japzo\OneDrive\Desktop\Blender Add-on Workshop\Layouts-Systems-Draftsman-Toolkit-Addon\scratch\test_slots_output.txt", "w") as f:
    f.write(output)
