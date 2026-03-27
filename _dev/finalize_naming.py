import os
import re

def overhauled_file(filepath):
    if not os.path.exists(filepath):
        print(f"Skipping: {filepath} (Not found)")
        return
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # Replacements based on project_management.txt Rules 15 & 16
    replacements = [
        (r'FCD_PT_Mechanical_Presets', 'FCD_PT_Mechanical_Presets'),
        (r'FCD_PT_Electronic_Presets', 'FCD_PT_Electronic_Presets'),
        (r'FCD_PT_Parametric_Toolkit', 'FCD_PT_Parametric_Toolkit'),
        (r'FCD_PT_Materials_And_Textures', 'FCD_PT_Materials_And_Textures'),
        (r'FCD_PT_Lighting_And_Atmosphere', 'FCD_PT_Lighting_And_Atmosphere'),
        (r'FCD_PT_Dimensions_And_Measuring', 'FCD_PT_Dimensions_And_Measuring'),
        (r'FCD_PT_Architectural_Presets', 'FCD_PT_Architectural_Presets'),
        (r'FCD_PT_Vehicle_Presets', 'FCD_PT_Vehicle_Presets'),
        (r'FCD_PT_Physics_Inertial', 'FCD_PT_Physics_Inertial'),
        (r'FCD_PT_Physics_Collision', 'FCD_PT_Physics_Collision'),
        (r'FCD_PT_Kinematics_Setup', 'FCD_PT_Kinematics_Setup'),
        (r'FCD_PT_Asset_Library_System', 'FCD_PT_Asset_Library_System'),
        (r'FCD_PT_Import_Export_System', 'FCD_PT_Import_Export_System'),
        (r'FCD_PT_Generate', 'FCD_PT_Generate'), 
        
        # Operators
        (r'FCD_OT_Open_Asset_Browser', 'FCD_OT_Open_Asset_Browser'),
        (r'FCD_OT_Add_Asset_Library', 'FCD_OT_Add_Asset_Library'),
        (r'FCD_OT_Register_Asset_Catalog', 'FCD_OT_Register_Asset_Catalog'),
        (r'FCD_OT_Mark_And_Upload_Asset', 'FCD_OT_Mark_And_Upload_Asset'),
        (r'FCD_OT_Generate_Robot_With_AI', 'FCD_OT_Generate_Robot_With_AI'),
        (r'FCD_OT_Setup_Example_Rover', 'FCD_OT_Setup_Example_Rover'),
        (r'FCD_OT_Setup_Example_Arm', 'FCD_OT_Setup_Example_Arm'),
        (r'FCD_OT_Setup_Mobile_Base', 'FCD_OT_Setup_Mobile_Base'),
        (r'FCD_OT_Setup_Quadruped', 'FCD_OT_Setup_Quadruped'),
        (r'FCD_OT_Clear_Physics', 'FCD_OT_Clear_Physics'),
        (r'FCD_OT_Rig_Parametric_Joint', 'FCD_OT_Rig_Parametric_Joint'),
        (r'FCD_OT_Create_Parametric_Chain', 'FCD_OT_Create_Parametric_Chain'),
        (r'FCD_OT_Add_Dimension', 'FCD_OT_Add_Dimension'),
        (r'FCD_OT_Remove_Dimension', 'FCD_OT_Remove_Dimension'),
        (r'FCD_OT_Apply_Material_Preset', 'FCD_OT_Apply_Material_Preset'),
        (r'FCD_OT_Reset_Part_Scale', 'FCD_OT_Reset_Part_Scale'),
        (r'FCD_OT_Spawn_Parametric_Part', 'FCD_OT_Spawn_Parametric_Part'),
    ]

    new_content = content
    for old, new in replacements:
        new_content = re.sub(old, new, new_content)

    if new_content != content:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print(f"Update: {filepath}")

def main():
    base_dir = r"c:\Users\japzo\OneDrive\Desktop\Blender Add-on Workshop\Fabrication-Construction-Draftsman-Tools-Automated"
    for root, _, files in os.walk(base_dir):
        for file in files:
            if file.endswith('.py'):
                overhauled_file(os.path.join(root, file))

if __name__ == "__main__":
    main()
