import bpy
import addon_utils

old_names = [
    "fabrication_construction_draftsman_tools_automated",
    "Fabrication_Construction_Draftsman_Tools_Blender_Addon",
    "Fabrication-Construction-Draftsman-Tools-Blender-Addon",
    "auto_robot_cnc_dev_kit"
]

new_name = "fabrication_construction_draftsman_tools"
new_extension_name = f"bl_ext.blender_org.{new_name}"

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

# Enable the new one
print(f"\nChecking for new Extension addon: {new_extension_name}")
try:
    bpy.ops.preferences.addon_enable(module=new_extension_name)
    print(f"[SUCCESS] Enabled new Extension: {new_extension_name}")
except Exception as e:
    print(f"[INFO] Namespaced path failed, trying legacy path: {new_name}")
    try:
        bpy.ops.preferences.addon_enable(module=new_name)
        print(f"[SUCCESS] Enabled as Legacy: {new_name}")
    except Exception as e2:
        print(f"[CRITICAL ERROR] Could not enable {new_name}: {e2}")

# Save preferences to ensure it persists after restart
bpy.ops.wm.save_userpref()
print("\n[INFO] Blender user preferences saved.")
print("="*50 + "\n")
