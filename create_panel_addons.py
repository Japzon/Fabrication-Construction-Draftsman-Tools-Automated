
import os
import shutil
import zipfile
import re
import sys
import argparse
import time

def package_panel(panel_name, base_dir, output_dir):
    panels_data = {
        "Generate": {"prop": "lsd_order_ai_factory", "cls": "LSD_PT_Generate", "module": "ui_ai_factory"},
        "Mechanical Presets": {"prop": "lsd_order_parts", "cls": "LSD_PT_Mechanical_Presets", "module": "ui_parts"},
        "Architectural Presets": {"prop": "lsd_order_architectural", "cls": "LSD_PT_Architectural_Presets", "module": "ui_architectural"},
        "Vehicle Presets": {"prop": "lsd_order_vehicle", "cls": "LSD_PT_Vehicle_Presets", "module": "ui_vehicle"},
        "Electronic Presets": {"prop": "lsd_order_electronics", "cls": "LSD_PT_Electronic_Presets", "module": "ui_electronics"},
        "Procedural Toolkit": {"prop": "lsd_order_procedural", "cls": "LSD_PT_Procedural_Toolkit", "module": "ui_parametric"},
        "Dimensions & Precision Transforms": {"prop": "lsd_order_dimensions", "cls": "LSD_PT_Dimensions_And_Precision_Transforms", "module": "ui_dimensions"},
        "Materials & Textures": {"prop": "lsd_order_materials", "cls": "LSD_PT_Materials_And_Textures", "module": "ui_materials"},
        "Environment & Lighting": {"prop": "lsd_order_lighting", "cls": "LSD_PT_Lighting_And_Atmosphere", "module": "ui_lighting"},
        "Kinematics Setup": {"prop": "lsd_order_kinematics", "cls": "LSD_PT_Kinematics_Setup", "module": "ui_kinematics"},
        "Camera Studio & Pathing": {"prop": "lsd_order_camera", "cls": "LSD_PT_Camera_Cinematography", "module": "ui_camera"},
        "Physics": {"prop": "lsd_order_physics", "cls": "LSD_PT_Physics", "module": "ui_physics"},
        "Transmission": {"prop": "lsd_order_transmission", "cls": "LSD_PT_Transmission", "module": "ui_transmission"},
        "Asset Library": {"prop": "lsd_order_assets", "cls": "LSD_PT_Asset_Library_System", "module": "ui_assets"},
        "Export System": {"prop": "lsd_order_export", "cls": "LSD_PT_Import_Export_System", "module": "ui_export"},
        "Preferences": {"prop": "lsd_order_preferences", "cls": "LSD_PT_Preferences", "module": "ui_preferences"}
    }

    if panel_name not in panels_data: return

    data = panels_data[panel_name]
    cls_name = data["cls"]
    module_name = data["module"]
    safe_name = panel_name.replace(" & ", "_").replace(" ", "_").replace("&", "_")
    namespace = f"lsd_{safe_name.lower()}"

    print(f"FIXING IDENTITY: {panel_name}")
    
    temp_panel_dir = os.path.join(output_dir, f"temp_{safe_name}")
    if os.path.exists(temp_panel_dir): shutil.rmtree(temp_panel_dir, ignore_errors=True)
    
    # Exclude everything that might collide or isn't needed
    shutil.copytree(base_dir, temp_panel_dir, ignore=lambda p, n: ['__pycache__', '.git', 'Panels as Add-ons', 'temp_', 'create_panel_addons.py'], dirs_exist_ok=True)
    
    # 1. Modify individual panel module
    module_path = os.path.join(temp_panel_dir, "panels", f"{module_name}.py")
    if os.path.exists(module_path):
        with open(module_path, 'r') as f: lines = f.readlines()
        new_lines = []
        skip_to_end_of_call = False
        stored_indent = ""
        for line in lines:
            # Fix class definition
            if f"class {cls_name}:" in line:
                line = line.replace(f"class {cls_name}:", f"class {cls_name}(bpy.types.Panel):")
                new_lines.append(line)
                new_lines.append(f'    bl_label = "{panel_name}"\n')
                new_lines.append(f'    bl_idname = "VIEW3D_PT_{namespace}"\n')
                new_lines.append(f"    bl_space_type = 'VIEW_3D'\n")
                new_lines.append(f"    bl_region_type = 'UI'\n")
                new_lines.append(f"    bl_category = '{panel_name}'\n")
                continue
            
            # Fix draw method
            if "@staticmethod" in line: continue
            if "def draw(layout" in line or "def draw(self, layout" in line:
                indent = line[:line.find("def")]
                new_lines.append(f"{indent}def draw(self, context):\n")
                new_lines.append(f"{indent}    layout = self.layout\n")
                continue

            # Fix header call
            if "ui_common.draw_panel_header" in line:
                stored_indent = line[:line.find(line.strip())]
                new_lines.append(f"{stored_indent}box = layout.box(); is_expanded = True\n")
                new_lines.append(f"{stored_indent}# {line.strip()}\n")
                if "(" in line and ")" not in line:
                    skip_to_end_of_call = True
                continue
            
            if skip_to_end_of_call:
                new_lines.append(f"{stored_indent}# {line.strip()}\n")
                if ")" in line: skip_to_end_of_call = False
                continue
            
            new_lines.append(line)
            
        with open(module_path, 'w') as f: f.writelines(new_lines)

    # 2. Rename BL_IDNAME in __init__.py potentially? 
    # Actually, we need to make sure the add-on name in bl_info is unique.
    init_path = os.path.join(temp_panel_dir, "__init__.py")
    with open(init_path, 'r') as f: content = f.read()
    content = re.sub(r'("name":\s*)"[^"]+"', rf'\1"{panel_name}"', content)
    # Give it a unique module name for Blender to avoid conflicts inRoamin/Addons folder
    with open(init_path, 'w') as f: f.write(content)

    # Clean up panels logic
    panels_init_path = os.path.join(temp_panel_dir, "panels", "__init__.py")
    with open(panels_init_path, 'w') as f:
        f.write(f"import bpy\nfrom . import ui_common\nfrom . import {module_name}\n")
        f.write(f"def register():\n    ui_common.register()\n    try: bpy.utils.register_class({module_name}.{cls_name})\n    except: pass\n")
        f.write(f"def unregister():\n    try: bpy.utils.unregister_class({module_name}.{cls_name})\n    except: pass\n    ui_common.unregister()\n")

    if os.path.exists(os.path.join(temp_panel_dir, "panels", "ui_main.py")):
        os.remove(os.path.join(temp_panel_dir, "panels", "ui_main.py"))

    # Create ZIP
    # Root folder in zip should be unique to avoid folder collision in Blender's scripts/addons/
    zip_root_name = namespace
    zip_filename = os.path.join(output_dir, f"{panel_name}.zip")
    with zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(temp_panel_dir):
            for file in files:
                fpath = os.path.join(root, file)
                zipf.write(fpath, os.path.join(zip_root_name, os.path.relpath(fpath, temp_panel_dir)))
    
    shutil.rmtree(temp_panel_dir, ignore_errors=True)
    print(f"IDENTITY SECURED: {zip_filename}")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--panel", help="Name of the panel to package")
    args = parser.parse_args()
    base_dir = os.path.dirname(os.path.abspath(__file__))
    out_dir = os.path.join(base_dir, "Panels as Add-ons")
    if not os.path.exists(out_dir): os.makedirs(out_dir)
    names = ["Generate", "Mechanical Presets", "Architectural Presets", "Vehicle Presets", "Electronic Presets", "Procedural Toolkit", "Dimensions & Precision Transforms", "Materials & Textures", "Environment & Lighting", "Kinematics Setup", "Camera Studio & Pathing", "Physics", "Transmission", "Asset Library", "Export System", "Preferences"]
    if args.panel: package_panel(args.panel, base_dir, out_dir)
    else:
        for n in names: package_panel(n, base_dir, out_dir)
        for n in names:
            with open(os.path.join(out_dir, f"{n}.bat"), 'w') as f:
                f.write(f'@echo off\necho "Securing {n}..."\npython "..\\create_panel_addons.py" --panel "{n}"\npause\n')

if __name__ == "__main__": main()
