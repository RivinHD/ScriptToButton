import os
import bpy
import zipfile
import uuid
from bpy.props import StringProperty, PointerProperty
from bpy.types import PropertyGroup, Context, UILayout, Text, AddonPreferences, Scene
from typing import TYPE_CHECKING, Union
import functools
from .import dynamic_panels as panels
if TYPE_CHECKING:
    from .preferences import STB_preferences
    from .properties import STB_button_properties
else:
    STB_button_properties = PropertyGroup
    STB_preferences = AddonPreferences


classes = []
NotOneStart = [False]
ALL_AREAS = [
    "3D_Viewport", "UV_Editor", "Compositor", "Video_Sequencer",
    "Movie_Clip_Editor", "Dope_Sheet", "Graph_Editor", "Nonlinear_Animation",
    "Text_Editor"
]


def get_preferences(context: Context) -> STB_preferences:
    return context.preferences.addons[__package__].preferences


def save_text(active_text: Text, script_name: str) -> None:
    text = active_text.as_string()
    storage_dir = os.path.join(os.path.dirname(
        os.path.abspath(__file__)), "Storage")
    if not os.path.isdir(storage_dir):
        os.mkdir(storage_dir)
    destination = os.path.join(storage_dir, "%s.py" % script_name)
    with open(destination, 'w', encoding='utf8') as outfile:
        outfile.write(text)


def get_text(script_name: str) -> None:
    destination = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "Storage",
        "%s.py" % script_name
    )
    if bpy.data.texts.find(script_name) == -1:
        bpy.data.texts.new(script_name)
    else:
        bpy.data.texts[script_name].clear()
    with open(destination, 'r', encoding='utf8') as file:
        bpy.data.texts[script_name].write(file.read())


def get_all_saved_scripts() -> list:
    storage_dir = os.path.join(os.path.dirname(
        os.path.abspath(__file__)), "Storage")
    if not os.path.isdir(storage_dir):
        os.mkdir(storage_dir)
    scripts = []
    for file in os.listdir(storage_dir):
        scripts.append(file.replace(".py", ""))
    scripts.sort()
    return scripts


def load(context: Context) -> tuple[list, list]:
    scene = context.scene
    scene.stb.clear()
    STB_pref = get_preferences(context)
    btnFails = ([], [])
    scripts = get_all_saved_scripts()
    for script in scripts:
        new = scene.stb.add()
        new.name = script
        get_text(script)
        btnFails[0].append(script)
        btnFails[1].append(add_areas_and_props(
            new,
            bpy.data.texts[script].as_string()
        ))
        if not STB_pref.autoload:
            bpy.data.texts.remove(bpy.data.texts[script])
    if len(scene.stb) > 0:
        scene.stb[0].selected = True
    panel_names = set(button.panel for button in scene.stb)
    for panel in set(panels.panel_names).difference(panel_names):
        panels.unregister_button_panel(panel)
    for panel in panel_names.difference(panels.panel_names):
        panels.register_button_panel(panel)
    return btnFails


def get_all_button_names(context: Context) -> set:
    return set(button.name for button in context.scene.stb)


def list_to_enum_items(data: list) -> list:
    enum_items = []
    for i in range(len(data)):
        enum_items.append((data[i], data[i], "", "", i))
    return enum_items


def get_panel(text: str) -> str:
    lines = text.splitlines()
    if not len(lines):
        return "Buttons"
    comments = (x.strip() for x in lines[0].split("///"))
    for comment in comments:
        if comment.startswith("#STB-Panel-"):
            return comment.split("-")[2]
    return "Buttons"


def get_areas(text: str) -> list:
    lines = text.splitlines()
    if not len(lines):
        return []
    comments = (x.strip() for x in lines[0].split("///"))
    area_types = []
    for comment in comments:
        if comment.startswith("#STB-Area-"):
            area_types.append(comment.split("-")[2])
    if len(area_types):
        return area_types
    return ALL_AREAS


AREA_PARSE_DICT = {
    "3D_Viewport": "VIEW_3D",
    "UV_Editor": "UV",
    "Image_Editor": "VIEW",
    "Compositor": "CompositorNodeTree",
    "Texture_Node_Editor": "TextureNodeTree",
    "Geomerty_Node_Editor": "GeometryNodeTree",
    "Shader_Editor": "ShaderNodeTree",
    "Video_Sequencer": "SEQUENCE_EDITOR",
    "Movie_Clip_Editor": "CLIP_EDITOR",
    "Dope_Sheet": "DOPESHEET",
    "Timeline": "TIMELINE",
    "Graph_Editor": "FCURVES",
    "Drivers": "DRIVERS",
    "Nonlinear_Animation": "NLA_EDITOR",
    "Text_Editor": "TEXT_EDITOR"
}


def area_parser(area: str) -> Union[str, bool]:
    return AREA_PARSE_DICT.get(area, False)


def get_props(text: str) -> list:
    lines = text.splitlines()
    props = []
    for i in range(len(lines)):
        current_line = lines[i].strip()
        if not current_line.startswith("#STB-") or current_line.startswith("#STB-Area"):
            continue
        next_line = lines[i + 1]
        if next_line.startswith("#"):
            continue
        inputs = current_line.replace(" ", "").split("///")
        line_name = next_line.split("=")[0]
        value = next_line.split("=")[1].split("#")[0]
        for input in inputs:
            if not input.startswith("#STB-Input"):
                continue
            split = input.split("-")
            props.append({
                "name": line_name.strip(),
                "line_name": line_name,
                "space": split[2],
                "type": split[3],
                "sort": split[4] if len(split) > 4 else "",
                "line": i + 1,
                "value": value
            })
    return props


BLENDER_TYPE_TO_PY_TYPE = {
    'String': str,
    'Int': int,
    'Float': float,
    'Bool': bool,
    'Enum': (list, tuple),
    'IntVector': (list, tuple),
    'FloatVector': (list, tuple),
    'BoolVector': (list, tuple),
    'List': (list, tuple),
    'Object': bpy.types.Object,
}
VECTOR_TYPE = {
    'IntVector': int,
    'FloatVector': float,
    'BoolVector': bool
}


def add_prop(button: STB_button_properties, property) -> bool:
    try:
        value = eval(property["value"])
    except Exception:
        return False

    property_type = property["type"]
    is_type = isinstance(
        value,
        BLENDER_TYPE_TO_PY_TYPE.get(property_type, None)
    )
    if ((property_type in {'String', 'Int', 'Float', 'Bool', 'List', 'Object'} and not is_type)
            or
            (property_type == 'Enum'
             and not (
                 is_type
                 and isinstance(value[1], (list, tuple))
                 and isinstance(value[0], str)
                 and all(map(lambda x: isinstance(x, str), value[1])))
             )
            or
            (property_type in {'IntVector', 'FloatVector', 'BoolVector'}
             and not (
                is_type
                and all(map(lambda x: isinstance(x, VECTOR_TYPE[property_type]), value))
                and len(value) >= 1
                and len(value) <= 32)
             )):  # Check types
        return False

    try:
        # Add element to the right property collection
        new_element = eval("button." + property_type + "Props.add()")
    except Exception:
        return False  # Add to fail stack

    name = property["name"]
    new_element.name = name  # parse data
    new_element.linename = property["line_name"]
    new_element.space = property["space"]
    new_element.line = property["line"]
    new_element.sort = property["sort"]
    if property_type == 'Enum':
        new_element.items.clear()
        for v in value[1]:
            item = new_element.items.add()
            item.name = v
            item.item = v
        try:
            new_element.prop = value[0]
        except Exception:
            new_element.prop = value[1][0]
    elif property_type in {'IntVector', 'FloatVector', 'BoolVector'}:
        new_element.address = create_vector_prop(
            len(value),
            ("%s_%s%s" % (
                button.name,
                name,
                str(new_element.line)
            )).replace(" ", ""),
            property_type,
            "bpy.context.scene.stb['%s'].%sProps['%s']" % (
                button.name,
                property_type,
                name
            )
        )
        exec("%s.prop = value" % new_element.address)
    elif property_type == 'List':
        new_element.prop.clear()
        for i in value:
            prop = new_element.prop.add()
            if not isinstance(i, (list, tuple)):
                if isinstance(i, (str, int, float, bool)):
                    exec("prop." + str(type(i).__name__) + "prop = i")
                    prop.ptype = str(type(i).__name__)
                else:
                    prop.strprop = str(i)
                    prop.ptype = 'str'
                continue

            if (isinstance(i, (list, tuple))
                    and (isinstance(i[1], list) or isinstance(i[1], tuple))
                    and isinstance(i[0], str)
                    and all(map(lambda x: isinstance(x, str), i[1]))):
                prop.enum_prop.items.clear()  # Enum
                prop.ptype = 'enum'
                for v in i[1]:
                    item = prop.enum_prop.items.add()
                    item.name = v
                    item.item = v
                try:
                    prop.enum_prop.prop = i[0]
                except Exception:
                    prop.enum_prop.prop = i[1][0]
            elif (isinstance(i, {list, tuple})
                  and all(map(lambda x: isinstance(x, bool), i))
                  and len(i) <= 32):  # BoolVector
                prop.boolvector_prop = create_vector_prop(
                    len(i),
                    ("%s_%s_list_%s" % (
                        button.name,
                        name,
                        str(len(new_element.prop)))
                     ).replace(" ", ""),
                    "BoolVector",
                    "bpy.context.scene.stb['%s'].ListProps['%s']" % (
                        button.name,
                        name
                    )
                )
                prop.ptype = 'boolvector'
                exec("%s.prop = i" % prop.boolvector_prop)
            elif (isinstance(i, {list, tuple})
                  and all(map(lambda x: isinstance(x, int), i))
                  and len(i) <= 32):  # IntVector
                prop.intvector_prop = create_vector_prop(
                    len(i),
                    ("%s_%s_list_%s" % (
                        button.name,
                        name,
                        str(len(new_element.prop)))
                     ).replace(" ", ""),
                    "IntVector",
                    "bpy.context.scene.stb['%s'].ListProps['%s']" % (
                        button.name,
                        name
                    )
                )
                prop.ptype = 'intvector'
                exec("%s.prop = i" % prop.intvector_prop)
            elif (isinstance(i, {list, tuple})
                  and all(map(lambda x: isinstance(x, float), i))
                  and len(i) <= 32):  # FloatVector
                prop.floatvector_prop = create_vector_prop(
                    len(i),
                    ("%s_%s_list_%s" % (
                        button.name,
                        name, str(len(new_element.prop)))
                     ).replace(" ", ""),
                    "FloatVector",
                    "bpy.context.scene.stb['%s'].ListProps['%s']" % (
                        button.name,
                        name
                    ),
                )
                prop.ptype = 'floatvector'
                exec("%s.prop = i" % prop.floatvector_prop)
            else:
                prop.strprop = str(i)
                prop.ptype = 'str'
    elif property_type == 'Object':
        new_element.prop = value.name
    else:
        new_element.prop = value
    return True


def add_button(context: Context, name: str, textname: str):
    STB_pref = get_preferences(context)
    texts = bpy.data.texts
    text = texts[textname].as_string()  # Get selected Text
    if STB_pref.autosave:
        save_text(texts[textname], name)
        if STB_pref.autoload:
            get_text(name)  # do same as lower, but with File
    elif STB_pref.autoload:
        if texts.find(textname) == -1:  # Create new text if not exist
            texts.new(textname)
        else:
            texts[textname].clear()
        texts[textname].write(text)  # Write to Text
    index = context.scene.stb.find(name)
    if index != -1:
        context.scene.stb.remove(index)
    new = context.scene.stb.add()  # Create new Instance
    new.name = check_for_duplicates(get_all_button_names(context), name)
    fails = add_areas_and_props(new, text)
    if new.panel not in panels.panel_names:
        panels.register_button_panel(new.panel)
    return fails


def remove_button(context: Context, delete_file: bool, delete_text: bool):
    STB_pref = get_preferences(context)
    name = STB_pref.selected_button
    stb = context.scene.stb
    button = stb[name]

    if delete_file:
        os.remove(os.path.join(
            os.path.dirname(__file__),
            "Storage",
            "%s.py" % name
        ))
    if delete_text:
        if (index := bpy.data.texts.find(name)) != -1:
            bpy.data.texts.remove(bpy.data.texts[index])
    delete_vector_props(button)
    delete_list_prop(button)
    index = stb.find(STB_pref.selected_button)
    stb.remove(index)
    if index - 1 >= 0:
        stb[index - 1].selected = True
    panel_names = set(button.panel for button in stb)
    for panel in set(panels.panel_names).difference(panel_names):
        panels.unregister_button_panel(panel)


def create_fail_message(fails: tuple[list, list]):
    message = "\n"
    if len(fails[0]):
        message += "   Areas: \n"
        for fail in fails[0]:
            message += "      Line: 0    #STB-Area-%s \n" % fail
    if len(fails[1]):
        message += "   Properties: \n"
        for fail in fails[1]:
            message += "      Line: %s    #STB-Input-%s-%s      %s \n" % (
                str(fail['line']),
                str(fail['space']),
                str(fail['type']),
                str(fail['value'])
            )
    return message


def load_from_texteditor(op, context: Context) -> tuple[list, list]:
    STB_pref = get_preferences(context)
    btnFails = ([], [])
    if op.all:
        for txt in op.texts:  # All Texts from Buttons
            btn_index = context.scene.stb.find(txt.txt_name)
            if btn_index != -1:
                btnFails[0].append(txt.txt_name)
                btnFails[1].append(reload_button_text(
                    context.scene.stb[btn_index],
                    bpy.data.texts[txt.txt_name].as_string(),
                    context.scene
                ))
                if STB_pref.autosave:
                    save_text(bpy.data.texts[txt.txt_name], txt.txt_name)
            else:
                load_add_button(txt.txt_name)
        return btnFails

    for txt in op.texts:
        if not txt.select:  # selected Texts from Buttons
            continue
        btn_index = context.scene.stb.find(txt.txt_name)
        if btn_index != -1:
            btnFails[0].append(txt.txt_name)
            btnFails[1].append(reload_button_text(
                context.scene.stb[btn_index],
                bpy.data.texts[txt.txt_name].as_string(),
                context.scene
            ))
            if STB_pref.autosave:
                save_text(bpy.data.texts[txt.txt_name], txt.txt_name)
        else:
            load_add_button(txt.txt_name)
    return btnFails


def load_add_button(name):
    bpy.ops.stb.addbutton(show_skip=True, name=name, text_list=name)


def reload_button_text(button: STB_button_properties, text: str, scene: Scene) -> tuple[list, list]:
    delete_vector_props(button)
    delete_list_prop(button)
    fails = add_areas_and_props(button, text)

    panel_names = set(button.panel for button in scene.stb)
    for panel in set(panels.panel_names).difference(panel_names):
        panels.unregister_button_panel(panel)
    for panel in panel_names.difference(panels.panel_names):
        panels.register_button_panel(panel)
    return fails


Property_type = {
    "String", "Int", "Float", "Bool", "Enum",
    "IntVector", "FloatVector", "BoolVector", "List", "Object"
}


def add_areas_and_props(button: STB_button_properties, text: str) -> tuple[list, list]:
    button.areas.clear()  # Clear Area and Prop
    for prop in Property_type:
        getattr(button, "%sProps" % prop).clear()

    button.panel = get_panel(text)

    areas = get_areas(text)  # Get Areas
    failed_areas = []
    for ele in areas:  # Add Areas
        pars = area_parser(ele)
        if pars is False:
            failed_areas.append(ele)
        else:
            new = button.areas.add()
            new.name = pars
            new.area = pars
    if len(areas) == len(failed_areas):  # failed to add areas
        for ele in ALL_AREAS:
            pars = area_parser(ele)
            new = button.areas.add()
            new.name = pars
            new.area = pars

    prop_list_dict = get_props(text)  # Get Props
    failed_props = []
    for ele in prop_list_dict:  # Add Props
        if not add_prop(button, ele):
            failed_props.append(ele)
    return (failed_areas, failed_props)


def update_vector_property(self, context):
    prop = eval(self.address)
    update_text(
        prop.line,
        prop.linename,
        [ele for ele in self.prop],
        eval("context.scene.%s" % prop.path_from_id().split(".")[0])
    )


def create_vector_prop(size: int, name: str, type: str, back_address: str):
    property_func = getattr(bpy.props, "%sProperty" % type)
    vec_id = uuid.uuid5(uuid.NAMESPACE_OID, name).hex

    class VectorProp(PropertyGroup):
        prop: property_func(size=size, update=update_vector_property)
        address: StringProperty(default=back_address)
    VectorProp.__name__ = "VectorProp_%s_%s" % (type, vec_id)
    bpy.utils.register_class(VectorProp)
    setattr(
        bpy.types.Scene,
        "stb_%sproperty_%s" % (type.lower(), vec_id),
        PointerProperty(type=VectorProp)
    )
    return "bpy.context.scene.stb_%sproperty_%s" % (type.lower(), vec_id)


def unregister_vector():
    for cls in classes:
        bpy.utils.unregister_class(cls)


def delete_vector_props(button: STB_button_properties):
    props = [
        *button.IntVectorProps,
        *button.FloatVectorProps,
        *button.BoolVectorProps
    ]
    for vec in props:
        name = vec.address.split(".")[-1]
        if hasattr(bpy.types.Scene, name):
            delattr(bpy.types.Scene, name)
            del bpy.context.scene[name]


def delete_list_prop(button: STB_button_properties):
    for ele in button.ListProps:
        for prop in ele.prop:
            if prop.ptype not in ("intvector", "floatvector", "boolvector"):
                continue
            name = getattr(prop, "%s_prop" % prop.ptype).split(".")[-1]
            if hasattr(bpy.types.Scene, name):
                delattr(bpy.types.Scene, name)
                del bpy.context.scene[name]


def update_text(linepos: int, varname: str, message: str, button: STB_button_properties):
    if NotOneStart[0] and bpy.data.texts.find(button.name) != -1:
        text = bpy.data.texts[button.name]
        text.lines[linepos].body = "%s= %s" % (varname, str(message))
        txt = text.as_string()
        text.clear()
        text.write(txt)


TYPE_GETTER = {
    'str': lambda v: v.str_prop,
    'int': lambda v: v.int_prop,
    'float': lambda v: v.float_prop,
    'bool': lambda v: v.bool_prop,
    'enum': lambda v: [v.enum_prop.prop, [item.item for item in v.enum_prop.items]],
    'intvector': lambda v: [i for i in eval("%s['prop']" % v.intvector_prop)],
    'floatvector': lambda v: [i for i in eval("%s['prop']" % v.floatvector_prop)],
    'boolvector': lambda v: [bool(i) for i in eval("%s['prop']" % v.boolvector_prop)]
}


def type_getter(value, vtype):
    func = TYPE_GETTER.get(vtype, None)
    if func is None:
        return
    return func(value)


def get_export_text(selection):
    text = bpy.data.texts.get(selection.name)
    if text:
        text = text.as_string()
    else:
        destination = "%s/Storage/%s.py" % (os.path.dirname(
            os.path.abspath(__file__)), selection.name)
        with open(destination, 'r', encoding="utf-8") as file:
            text = file.read()
    return text


def export(mode, selections: list, export_path: str) -> None:
    if mode == "py":
        for selection in selections:
            path = os.path.join(export_path, "%s.py" % selection.name)
            with open(path, 'w', encoding='utf8') as file:
                file.write(get_export_text(selection))
    else:
        folder_path = os.path.join(bpy.app.tempdir, "STB_Zip")
        if not os.path.exists(folder_path):
            os.mkdir(folder_path)
        with zipfile.ZipFile(export_path, 'w') as zip_it:
            for selection in selections:
                zip_path = os.path.join(folder_path, "%s.py" % selection.name)
                with open(zip_path, 'w', encoding='utf8') as file:
                    file.write(get_export_text(selection))
                zip_it.write(zip_path, "%s.py" % selection.name)
                os.remove(zip_path)
        os.rmdir(folder_path)


def import_zip(filepath: str, context: Context) -> tuple[list, list]:
    btnFails = ([], [])
    with zipfile.ZipFile(filepath, 'r') as zip_out:
        filepaths = []
        for i in zip_out.namelist():
            if i.endswith(".py"):
                filepaths.append(i)
        for filepath in filepaths:
            txt = zip_out.read(filepath).decode("utf-8").replace("\r", "")
            Fail = import_button(filepath, context, txt)
            btnFails[0].extend(Fail[0])
            btnFails[1].append(Fail[1])
        return btnFails


def import_py(filepath: str, context: Context) -> tuple[list[str], tuple[list, list]]:
    with open(filepath, 'r', encoding='utf8') as file:
        txt = file.read()
        return import_button(filepath, context, txt)


def import_button(
        filepath: str,
        context: Context,
        txt: str) -> tuple[list[str], tuple[list, list]]:
    STB_pref = get_preferences(context)
    stb = context.scene.stb
    name = check_for_duplicates(
        get_all_button_names(context),
        os.path.splitext(os.path.basename(filepath))[0]
    )
    bpy.data.texts.new(name)
    bpy.data.texts[name].write(txt)
    button: STB_button_properties = stb.add()
    button.name = name
    button.selected = True

    if STB_pref.autosave:
        save_text(bpy.data.texts[name], name)
    if not STB_pref.autoload:
        bpy.data.texts.remove(bpy.data.texts[name])
    Fails = add_areas_and_props(button, txt)
    return ([name], Fails)


def check_for_duplicates(check_list: set, name: str, num: int = 1) -> str:
    """
    Check for the same name in check_list and append .001, .002 etc. if found

    Args:
        check_list (set): list to check against
        name (str): name to check
        num (int, optional): starting number to append. Defaults to 1.

    Returns:
        str: name with expansion if necessary
    """
    split = name.split(".")
    base_name = name
    if split[-1].isnumeric():
        base_name = ".".join(split[:-1])
    while name in check_list:
        name = "{0}.{1:03d}".format(base_name, num)
        num += 1
    return name


def rename(context: Context, name: str):
    STB_pref = get_preferences(context)
    button: STB_button_properties = context.scene.stb[STB_pref.selected_button]
    if bpy.data.texts.find(STB_pref.selected_button) == -1:
        get_text(STB_pref.selected_button)
    text = bpy.data.texts[STB_pref.selected_button]
    directory = os.path.dirname(os.path.abspath(__file__))
    old_path = os.path.join(directory, "Storage", "%s.py" %
                            STB_pref.selected_button)
    if name != button.name:
        name = check_for_duplicates(get_all_button_names(context).difference([button.name]), name)
    button.name = name
    button.selected = True
    text.name = name
    os.rename(old_path, os.path.join(directory, "Storage", "%s.py" % name))
    if not STB_pref.autoload:
        bpy.data.texts.remove(text)


def update_all_props(button: STB_button_properties, context: Context):
    simple_props = [
        button.StringProps,
        button.IntProps,
        button.FloatProps,
        button.BoolProps,
        button.EnumProps,
        button.ObjectProps,
        button.ListProps
    ]
    for prop in simple_props:
        for item in prop:
            item.update_prop(context)
    vector_props = [
        *button.IntVectorProps,
        *button.FloatVectorProps,
        *button.BoolVectorProps
    ]
    for prop in vector_props:
        prop = eval(prop.address)
        update_vector_property(prop, context)


def sort_props(button: STB_button_properties, space: str) -> tuple[list, list]:
    sort_mapping = []
    simple_props = [
        *button.StringProps,
        *button.IntProps,
        *button.FloatProps,
        *button.BoolProps,
        *button.EnumProps
    ]
    for prop in simple_props:
        if prop.space != space:
            continue
        sort_mapping.append(
            [*parse_sort(prop.sort), functools.partial(draw_prop, prop=prop)])
    vector_props = [
        *button.IntVectorProps,
        *button.FloatVectorProps,
        *button.BoolVectorProps
    ]
    for prop in vector_props:
        if prop.space != space:
            continue
        sort_mapping.append([
            *parse_sort(prop.sort),
            functools.partial(draw_vector_prop, prop=prop)
        ])
    for prop in button.ListProps:
        if prop.space != space:
            continue
        sort_mapping.append([
            *parse_sort(prop.sort),
            functools.partial(draw_list_prop, props=prop)
        ])
    for prop in button.ObjectProps:
        if prop.space != space:
            continue
        sort_mapping.append([
            *parse_sort(prop.sort),
            functools.partial(
                draw_prop_search,
                prop=prop,
                context=bpy.data,
                context_prop="objects"
            )
        ])
    sort_mapping.sort(key=lambda x: [x[0], x[1]])
    back = []
    sort = []
    for ele in sort_mapping:
        if ele[0] == -1:
            back.append(ele)
        else:
            sort.append(ele)
    return (sort, back)


def draw_sort(sort: list, back: list, baseLayout: UILayout):
    lastIndex = 0
    lastRow = [-1, None, 0, 0]
    for ele in sort:
        layout = baseLayout
        skip_space(ele[0] - lastIndex, layout)
        lastIndex = ele[0] + 1
        if ele[0] == lastRow[0]:
            layout = lastRow[1]
            newRow = False
        else:
            if lastRow[2] > 0:
                skip_space(1, lastRow[1], lastRow[2])
                lastRow[3] = 0
            newRow = True
        row, skipBack, lastSpace = draw_row(
            ele[1],
            ele[-1],
            layout,
            lastRow[3],
            newRow
        )
        lastRow = [ele[0], row, skipBack, lastSpace]
    else:
        if lastRow[2] > 0:
            skip_space(1, lastRow[1], lastRow[2])
    for ele in back:
        ele[-1](layout=baseLayout)


def draw_row(eleParse: list, eleDraw, row: UILayout, lastSpace: int, newRow: bool) -> tuple:
    if newRow:
        row = row.row()
        space = eleParse[0]
    else:
        space = eleParse[0] - lastSpace
    lastSpace = 1
    if space > 0:
        skip_space(1, row, space)
    eleDraw(layout=row)
    if len(eleParse) > 1:
        back = eleParse[1]
    else:
        back = 0
    return (row, back, lastSpace)


def skip_space(skips: int, layout: UILayout, scale: float = 1):
    for i in range(skips):
        if scale <= 0:
            continue
        col = layout.column()
        col.scale_x = scale
        col.label(text="")


def parse_sort(sort: str):
    if sort.startswith("[") and sort.endswith("]") and (n.digit() or n == "/" or n == ',' for n in sort[1:-1]):
        sort = sort[1:-1].split(",")
        if len(sort) > 2 or len(sort) < 1:
            return [-1, [-1]]
        col = int(sort[0])
        if col < 0:
            col = -1
        if len(sort) > 1:
            split = sort[1].split("/")
            if len(split) > 2:
                split = split[:2]
            elif len(split) < 1:
                split.append('0')
            if "" in split:
                rows = [-1]
            else:
                rows = [float(i) for i in split]
                for row in rows:
                    if row < 0:
                        row = 0
        else:
            rows = [-1]
        return [col, rows]
    else:
        return [-1, [-1]]


def draw_prop(layout: UILayout, prop):
    layout.prop(prop, 'prop', text=prop.name)


def draw_vector_prop(layout: UILayout, prop):
    layout.prop(eval(prop.address), 'prop', text=prop.name)


def draw_list_prop(layout: UILayout, props):
    box = layout.box()
    box.label(text=props.name)
    for prop in props.prop:
        if prop.ptype.endswith("vector"):
            address = getattr(prop, "%s_prop" % prop.ptype)
            box.prop(eval(address), 'prop', text="")
        elif prop.ptype == 'enum':
            box.prop(getattr(prop, "%s_prop" % prop.ptype), 'prop', text="")
        else:
            box.prop(prop, "%s_prop" % prop.ptype, text="")


def draw_prop_search(layout: UILayout, prop, context: Context, context_prop):
    layout.prop_search(prop, 'prop', context, context_prop, text=prop.name)


PY_TYPE_TO_BLENDER_TYPE = {
    str: 'String',
    int: 'Int',
    float: 'Float',
    bool: 'Bool',
    bpy.types.Object: 'Object',
}


def get_all_variables(text: str) -> list:
    variables = []
    last_line = ""
    for i, line in enumerate(text.splitlines()):
        line = line.strip()
        split = line.split("=")
        if len(split) != 2 or line.startswith("#") or last_line.startswith("#STB-Input"):
            last_line = line
            continue

        name, value = split
        name = name.strip()
        if "," in name or " " in name or name == "":
            last_line = line
            continue

        value = value.strip()
        try:
            evaluated = eval(value)
        except Exception:
            last_line = line
            continue
        if isinstance(evaluated, (bool, str, int, float, bpy.types.Object)):
            variables.append((
                i,
                line,
                value,
                PY_TYPE_TO_BLENDER_TYPE[type(evaluated)]
            ))
        elif isinstance(evaluated, (tuple, list)) and len(evaluated) > 0 and value[0] in "[(":
            # ENUM
            if (len(evaluated) == 2
                    and isinstance(evaluated[1], (list, tuple))
                    and isinstance(evaluated[0], str)
                    and all(map(lambda x: isinstance(x, str), evaluated[1]))):
                variables.append((i, line, value, "Enum"))
                last_line = line
                continue
            # VECTOR
            is_vector = False
            for py_type, bl_type in {(bool, "BoolVector"), (int, "IntVector"), (float, "FloatVector")}:
                if (all(map(lambda x: isinstance(x, py_type), evaluated))
                        and len(evaluated) <= 32):
                    is_vector = True
                    variables.append((i, line, value, bl_type))
                    break
            if is_vector:
                last_line = line
                continue
            # LIST
            variables.append((i, line, value, "List"))
        last_line = line
    return variables


def get_all_properties(button: STB_button_properties) -> tuple:
    return sorted(
        (
            *button.StringProps,
            *button.IntProps,
            *button.FloatProps,
            *button.BoolProps,
            *button.EnumProps,
            *button.ObjectProps,
            *button.ListProps,
            *button.IntVectorProps,
            *button.FloatVectorProps,
            *button.BoolVectorProps
        ),
        key=lambda x: x.line
    )
