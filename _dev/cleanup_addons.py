import bpy
import addon_utils

old_names = [
    "fabrication_construction_draftsman_tools_automated",
    "Fabrication_Construction_Draftsman_Tools_Blender_Addon",
    "Fabrication-Construction-Draftsman-Tools-Blender-Addon",
    "auto_robot_cnc_dev_kit"
]

new_name = "fabrication_construction_draftsman_tools"
new_extension_name = f"bl_ext.user_default.{new_name}"

print("\n" + "="*50)
print("  FCD ADDON REGISTRY CLEANUP")
print("="*50)

# Unregister ALL old variations to clear the 'No module named' errors
for name in old_names:
    try:
        # Check if it's currently loaded
        if name in bpy.context.preferences.addons:
            print(f"[INFO] Disabling legacy addon: {name}")
            bpy.ops.preferences.addon_disable(module=name)
    except Exception as e:
        pass # Silently fail

# The new one is expected to be enabled automatically by Blender 4.2+ extensions
if new_extension_name in bpy.context.preferences.addons:
    print(f"[INFO] New Extension active: {new_extension_name}")
elif new_name in bpy.context.preferences.addons:
     print(f"[INFO] New extension active (legacy-style): {new_name}")
else:
     print(f"[WARNING] Draftsman extension not yet enabled in this Blender instance.")

# Save preferences only if we disabled old ones
if any(name in bpy.context.preferences.addons for name in old_names):
    bpy.ops.wm.save_userpref()
    print("\n[INFO] Cleanup finished. Blender user preferences updated.")

# Signal to the dev_tool that setup is done
print("---FCD_BLENDER_READY---")
print("="*50 + "\n")
