#Author-Henrique Hafner Ferreira

import adsk.core, adsk.fusion, traceback
import os
import json
from typing import List

def run(context):
    app = adsk.core.Application.get()
    ui  = app.userInterface
    try:
        core(context)
    except Exception as e:
        None
        ui.messageBox(str(e))

def core(context):
    app = adsk.core.Application.get()

    ui  = app.userInterface
    # Get active product in Fusion360
    product = app.activeProduct
    design = adsk.fusion.Design.cast(product) # see Fusion360 API, why to use 'cast' in python environment.
    if not design:
        ui.messageBox('ActiveProduct is not Design. Switch to design tab.')

    rootComponent = design.rootComponent # Top level assembly component;
    all_components_list = get_all_components(rootComponent)
    properties_components = get_properties_from_components(all_components_list)
    reference_position  = get_reference_component_positions(rootComponent)
    root_joints = get_root_joints(rootComponent)
    data = [reference_position,root_joints,properties_components]

    abs_path = os.path.abspath('')
    directory_name = str(rootComponent.name)+'_exported_properties'
    directory_path = os.path.join(abs_path,directory_name)
    exporting_message = export(data,directory_path)
    ui.messageBox(exporting_message)
    return True


# The diference between occurence and component is in Fusion360 API documentation.
def get_reference_component_positions(root_component:adsk.fusion.Component):
    sublevel_occurrences = root_component.occurrences # take component_ocorruences in sub level of the assembly
    reference_component_positions = []
    for occurence in sublevel_occurrences:
        name = occurence.name
        position = occurence.transform.asArray()
        reference_component_positions.append([name,position])
    return reference_component_positions

def get_all_components(root_component:adsk.fusion.Component) -> List[adsk.fusion.Component]:
    all_occurrences = root_component.allOccurrences
    index_occurrences = range(root_component.allOccurrences.count)
    components_list = []
    components_list_name = []
    for index in index_occurrences:
        occurrence = all_occurrences.item(index)
        component = occurrence.component
        name = component.name
        if components_list_name.count(name) == 0:
            components_list.append(component)
            components_list_name.append(name)
    return components_list   

def get_root_joints(rootComponent:adsk.fusion.Component):
    root_joints = rootComponent.allJoints
    joints = []
    joint_type_name = ['fixed', 'revolute', 'prismatic', 'cylinderical','pinslot', 'planner', 'ball']
    for joint in root_joints:
        properties = dict()
        properties['joint_name'] = joint.name
        try:
            properties['reference1'] = joint.occurrenceOne.name
            properties['reference2'] = joint.occurrenceTwo.name
            properties['jointType_index'] = int(joint.jointMotion.jointType)
            properties['jointType_expression'] = joint_type_name[properties['jointType_index']]
            properties['supression_state'] = joint.isSuppressed
            properties['origin']    = joint.geometryOrOriginOne.origin.asArray()
            properties['axis']      = joint.geometryOrOriginOne.primaryAxisVector.asArray()
            properties['error'] = False 
        except:
            properties['error'] = True
        joints.append(properties)
    return joints

def get_properties_from_components(components_list:List[adsk.fusion.Component]):
    properties_from_components = []
    for component in components_list:
        properties = dict()
        properties['name'] = component.name
        properties['material'] = get_material(component)
        properties['mass_center'] = component.physicalProperties.centerOfMass.asArray()
        intertia = list(component.physicalProperties.getXYZMomentsOfInertia())
        intertia.pop(0)
        intertia.append('ixx ixy ixz iyy iyz izz [kg/cm^2]')
        'xx, yy, zz, xy, yz, xz'
        intertia_representation = intertia.copy()
        intertia_representation[0] = intertia[0]
        intertia_representation[1] = intertia[3]
        intertia_representation[2] = intertia[5]
        intertia_representation[3] = intertia[1]
        intertia_representation[4] = intertia[4]
        intertia_representation[5] = intertia[2]
        properties['inertia;global'] = intertia_representation
        properties_from_components.append(properties)
    return properties_from_components

def get_material(component):
    material = component.material
    if material:
        material_name = material.name
    else:
        material_name = 'Missing definition'
    return material_name

def stringfy_list(data:list):
    stringfied_list = ''
    for i in data:
        stringfied_list += str(i) + '\n'
    return stringfied_list

def export(data,directory_path):
    reference_position,root_joints,properties_components = data
    if not os.path.isdir(directory_path):
        os.mkdir(directory_path)
    json_file_path = os.path.join(directory_path,'Data exported from Fusion.json')

    data_json = json.dumps(data)
    with open(json_file_path, 'w') as output_file:
        output_file.write(data_json)

    text_file =  '#################################\n'
    text_file += '### Reference Position ##########\n'
    text_file += stringfy_list(reference_position)
    text_file += '### Root Joints #################\n'
    text_file += stringfy_list(root_joints)
    text_file += '### Properties of Components ####\n'
    text_file += stringfy_list(properties_components)
    text_file += '#################################\n'
    txt_file_path = os.path.join(directory_path,'Data exported from Fusion.txt')
    with open(txt_file_path, 'w') as output_file:
        output_file.write(text_file)
    message = 'Files suscefully exported in '+directory_path
    return message