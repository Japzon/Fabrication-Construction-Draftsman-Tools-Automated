
import bpy
import sys
import traceback

print("="*50)
print("  FCD ADDON REGISTRATION TEST (RETRY)")
print("="*50)

addon_name = "fabrication_construction_draftsman_tools_automated"

try:
    print(f"Enabling addon: {addon_name}")
    bpy.ops.preferences.addon_enable(module=addon_name)
    print("\n[SUCCESS] Addon enabled without errors!")
    sys.exit(0)
    
except Exception as e:
    print("\n" + "!"*50)
    print(f"  [ERROR] REGISTRATION FAILED!")
    print("!"*50)
    traceback.print_exc()
    sys.exit(1)
