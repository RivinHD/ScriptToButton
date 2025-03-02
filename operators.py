import typing
import bpy
from bpy.types import Operator, Context, Event, PropertyGroup, UILayout
from bpy.props import StringProperty, EnumProperty, BoolProperty, CollectionProperty
from bpy_extras.io_utils import ImportHelper, ExportHelper
from . functions import get_preferences
from . import functions
from . import properties
import traceback
import sys
from os.path import splitext, join
from types import ModuleType
import os


class STB_OT_AddButton(Operator):
    bl_idname = "stb.add_button"
    bl_label = "Add Button"
    bl_description = 'Add a script as Button to the "Buttons" Panel'
    bl_options = {"REGISTER", "UNDO"}

    show_skip: BoolProperty(default=False, name="Show Skip")
    mode: EnumProperty(
        name="Change Mode",
        default="add",
        items=[
            ("add", "Add", ""),
            ("skip", "Skip", "")
        ]
    )
    name: StringProperty(name="Name")
    text: StringProperty(name="Text")

    def items_text_list(self, context: Context):
        return [(self.text, self.text, "")]
    text_list: EnumProperty(name="Text", items=items_text_list)

    all_names = []

    def draw(self, context: Context):
        STB_pref = get_preferences(context)
        layout = self.layout
        if self.show_skip:
            layout.prop(self, 'mode', expand=True)
        if self.mode == 'skip':
            return
        if self.name in self.all_names:
            box = layout.box()
            box.alert = True
            box.label(
                text="\"%s\" will be overwritten" % self.name,
                icon='ERROR'
            )
        col = layout.column()
        col.prop(self, 'name')
        col = layout.column()
        if self.show_skip:
            col.enabled = False
            col.prop(self, 'text_list')
        else:
            if len(bpy.data.texts):
                col.prop(STB_pref, 'texts_list')
            else:
                col.label(text="No Text available", icon="ERROR")

    def invoke(self, context: Context, event: Event):
        self.all_names = functions.get_all_button_names(context)
        return context.window_manager.invoke_props_dialog(self)

    def execute(self, context: Context) -> set[str]:
        STB_pref = get_preferences(context)
        STB_pref.button_name = self.name
        self.all_names = functions.get_all_button_names(context)
        txt = STB_pref.texts_list
        if self.show_skip:
            txt = self.text
        if self.mode == 'skip':
            return {"FINISHED"}
        if self.name == '':
            self.report({'ERROR'}, "You need a name for the Button")
            return {"FINISHED"}
        elif self.name in self.all_names:
            self.report({'INFO'}, "%s has been overwritten" % txt)
        elif STB_pref.texts_list == '':
            self.report({'ERROR'}, "You need to select a Text")
            return {"FINISHED"}
        fails = functions.add_button(context, self.name, txt)
        if len(fails[0]) or len(fails[1]):
            self.report(
                {'ERROR'},
                "Not all Areas or Properties could be added because the Syntax is invalid: %s" % (
                    functions.create_fail_message(fails))
            )
        context.area.tag_redraw()
        return {"FINISHED"}


class STB_OT_ScriptButton(Operator):
    bl_idname = "stb.script_button"
    bl_label = "ScriptButton"
    bl_options = {"UNDO", "INTERNAL"}

    name: StringProperty()

    def draw(self, context: Context):
        layout = self.layout
        stb = context.scene.stb
        STB_pref = get_preferences(context)
        if len(stb):
            button = stb[STB_pref.selected_button]
            sort, back = functions.sort_props(button, 'Dialog')
            if len(sort) > 0 or len(back) > 0:
                functions.draw_sort(sort, back, layout)
            else:
                layout.label(text="No Properties")

    def invoke(self, context: Context, event: Event):
        stb = context.scene.stb
        if len(stb):
            button = stb[self.name]
            sort, back = functions.sort_props(button, 'Dialog')
            if len(sort) > 0 or len(back) > 0:
                return bpy.context.window_manager.invoke_props_dialog(self)
            else:
                return self.execute(context)

    def execute(self, context: Context):
        STb_pref = get_preferences(context)
        stb = context.scene.stb
        if bpy.data.texts.find(self.name) == -1:
            functions.get_text(self.name)
            functions.update_all_props(stb[self.name], context)
        text = bpy.data.texts[self.name]
        try:
            # similar to text.as_module() -> internal Blender function see ..\scripts\modules\bpy_types.py
            name = text.name
            mod = ModuleType(splitext(name)[0])
            mod.__dict__.update({
                "__file__": join(bpy.data.filepath, name),
                "__name__": "__main__"
            })
            exec(text.as_string(), mod.__dict__)

            if STb_pref.delete_script_after_run:
                bpy.data.texts.remove(text)
        except Exception:
            error = traceback.format_exception(*sys.exc_info())
            # corrects the filename of the exception to the text name, otherwise "<string>"
            error_split = error[3].replace('"<string>"', '').split(',')
            error[3] = '%s "%s",%s' % (
                error_split[0], text.name, error_split[1])
            # removes exec(self.as_string(), mod.__dict__)
            error.pop(1)
            error = "".join(error)
            if error:
                self.report(
                    {'ERROR'}, "The linked Script is not working\n\n%s" % error)
            if STb_pref.delete_script_after_run:
                bpy.data.texts.remove(text)
            return {'CANCELLED'}
        return {"FINISHED"}


class STB_OT_RemoveButton(Operator):
    bl_idname = "stb.remove_button"
    bl_label = "Remove"
    bl_description = "Delete the selected Button"
    bl_options = {"REGISTER", "UNDO"}

    delete_file: BoolProperty(
        name="Delete File",
        description="Deletes the saved .py in the Storage",
        default=True
    )
    delete_text: BoolProperty(
        name="Delete Text",
        description="Deletes the linked Text in the Texteditor",
        default=True
    )

    @classmethod
    def poll(cls, context: Context):
        STB_pref = get_preferences(context)
        return STB_pref.selected_button != ""

    def draw(self, context: Context):
        STB_pref = get_preferences(context)
        layout = self.layout
        layout.prop(self, 'delete_file', text="Delete File")
        row = layout.row()
        text_enabled = bpy.data.texts.find(STB_pref.selected_button) != -1
        row.enabled = text_enabled
        self.deleteText = text_enabled
        row.prop(self, 'delete_text', text="Delete Text", toggle=False)

    def invoke(self, context: Context, event: Event):
        return context.window_manager.invoke_props_dialog(self)

    def execute(self, context):
        functions.remove_button(context, self.delete_file, self.delete_text)
        context.area.tag_redraw()
        return {"FINISHED"}


class STB_OT_Load(Operator):
    bl_idname = "stb.load"
    bl_label = "Load"
    bl_description = "Load all Buttons from File or Texteditor"
    bl_options = {"REGISTER", "UNDO"}

    mode: EnumProperty(
        name="Load from",
        description="Change the Mode which to load",
        items=[
            ("file", "Load from Disk", ""),
            ("texteditor", "Load from Texteditor", "")
        ]
    )
    all: BoolProperty(
        name="Load all",
        description="Load all Buttons from the Texteditor",
        default=False
    )
    texts: CollectionProperty(
        type=properties.STB_text_property,
        name="Texts in Texteditor"
    )

    @classmethod
    def poll(cls, context: Context):
        STB_pref = get_preferences(context)
        return STB_pref.selected_button != ""

    def draw(self, context: Context):
        layout = self.layout
        layout.prop(self, 'mode', expand=True)
        if self.mode == "file":
            # File -------------------------------------------
            box = layout.box()
            col = box.column()
            col.scale_y = 0.8
            col.label(text="It will delete all your current Buttons", icon="INFO")
            col.label(
                text="and replace it with the Buttons from the Disk",
                icon="BLANK1"
            )
        else:
            # Texteditor -------------------------------------
            box = layout.box()
            box.prop(self, 'all', text="Load All", toggle=True)
            if self.all:
                for text in self.texts:
                    box.label(text=text.name, icon='CHECKBOX_HLT')
            else:
                for text in self.Texts:
                    box.prop(text, 'select', text=text.name)

    def invoke(self, context: Context, event: Event):
        self.texts.clear()
        for text in bpy.data.texts:
            new = self.texts.add()
            new.name = text.name
        return context.window_manager.invoke_props_dialog(self)

    def execute(self, context: Context):
        if self.mode == "file":
            fails = functions.load(context)
        elif self.mode == "texteditor":
            fails = functions.load_from_texteditor(self, context)
        message = "\n"
        for name, fail in zip(fails[0], fails[1]):
            if len(fail[0]) or len(fail[1]):
                message += "\n %s:" % name
                message += functions.create_fail_message(fail)
        if message != "\n":
            self.report(
                {'ERROR'},
                "Not all Areas or Properties could be added because the Syntax is invalid: %s" % message
            )
        context.area.tag_redraw()
        return {"FINISHED"}


class STB_OT_Reload(Operator):
    bl_idname = "stb.reload"
    bl_label = "Reload"
    bl_description = "Reload the linked Text in the Texteditor of the selected Button"
    bl_options = {"REGISTER"}

    @classmethod
    def poll(cls, context: Context):
        STB_pref = get_preferences(context)
        return STB_pref.selected_button != ""

    def execute(self, context: Context):
        STB_pref = get_preferences(context)
        stb = context.scene.stb
        text_index = bpy.data.texts.find(STB_pref.selected_button)
        if text_index != -1:
            if STB_pref.autosave:
                functions.save_text(
                    bpy.data.texts[text_index],
                    STB_pref.selected_button
                )
            fails = functions.reload_button_text(
                stb[STB_pref.selected_button],
                bpy.data.texts[text_index].as_string(),
                context.scene
            )
            if len(fails[0]) or len(fails[1]):
                self.report(
                    {'ERROR'},
                    "Not all Areas or Properties could be added because the Syntax is invalid: %s" % (
                        functions.create_fail_message(fails))
                )
        else:
            self.report(
                {'ERROR'},
                ("%s could not be reloaded, linked Text in Texteditor don't exist.\n"
                 "\n"
                 "INFO: The linked Text must have the same name as the Button"
                 ) % STB_pref.selected_button
            )
        context.area.tag_redraw()
        return {"FINISHED"}


class STB_OT_Save(Operator):
    bl_idname = "stb.save"
    bl_label = "Save"
    bl_description = "Save all buttons to the Storage"

    @classmethod
    def poll(cls, context: Context):
        STB_pref = get_preferences(context)
        return STB_pref.selected_button != ""

    def execute(self, context):
        Fails = []
        for button in context.scene.stb:
            if bpy.data.texts.find(button.name) != -1:
                functions.save_text(bpy.data.texts[button.name], button.name)
            else:
                Fails.append(button.name)
        if len(Fails) > 0:
            error_text = "Not all Scripts could be saved:"
            for fail in Fails:
                error_text += "\n%s could not be saved, linked Text is missing" % fail
            self.report({'ERROR'}, error_text)
        return {"FINISHED"}


class STB_OT_Export(Operator, ExportHelper):
    bl_idname = "stb.export"
    bl_label = "Export"
    bl_description = "Export the selected Buttons"

    export_buttons: CollectionProperty(type=properties.STB_export_button)

    def get_all(self):
        return self.get("all", False)

    def set_all(self, value):
        if value == self.get("all", False):
            return
        self["all"] = value
        for button in self.export_buttons:
            button["export_all"] = value

    all: BoolProperty(
        name="All",
        description="Export all Buttons",
        get=get_all,
        set=set_all
    )

    def get_mode(self):
        return self.get("mode", 0)

    def set_mode(self, value):
        self["mode"] = value
        if value == 0:
            self.filepath = self.directory

    mode: EnumProperty(
        name="Mode",
        items=[
            ("py", "Export as .py Files", ""),
            ("zip", "Export as .zip File", "")
        ],
        get=get_mode,
        set=set_mode
    )

    def get_filter_glob(self):
        return "*.zip" * (self.mode == "zip")

    filter_glob: StringProperty(
        default='*.zip',
        options={'HIDDEN'},
        maxlen=255,
        get=get_filter_glob
    )

    def get_filename_ext(self):
        return ".zip" * (self.mode == "zip")

    filename = ""
    filename_ext: StringProperty(default=".", get=get_filename_ext)

    def get_use_filter_folder(self):
        return self.mode == "py"

    use_filter_folder: BoolProperty(default=True, get=get_use_filter_folder)
    filepath: StringProperty(name="File Path", maxlen=1024, default="")
    directory: StringProperty(name="Folder Path", maxlen=1024, default="")

    @classmethod
    def poll(cls, context: Context):
        STB_pref = get_preferences(context)
        return STB_pref.selected_button != ""

    def draw(self, context: Context):
        layout = self.layout
        layout.prop(self, 'mode', expand=True)
        box = layout.box()
        box.prop(self, 'all')
        for button in self.export_buttons:
            box.prop(button, 'use', text=button.name)

    def invoke(self, context: Context, event: Event):
        super().invoke(context, event)
        self.export_buttons.clear()
        for button in context.scene.stb:
            new = self.export_buttons.add()
            new.name = button.name
        return {'RUNNING_MODAL'}

    def execute(self, context: Context):
        if self.mode == "py":
            if not os.path.isdir(self.directory):
                self.report({'ERROR'}, "The given directory does not exists")
                return {'CANCELLED'}
            self.filepath = self.directory
        else:
            if not self.filepath.endswith(".zip"):
                self.report({'ERROR'}, "The given filepath is not a .zip file")
                return {'CANCELLED'}
        functions.export(
            self.mode,
            filter(lambda x: x.use, self.export_buttons),
            self.filepath
        )
        return {"FINISHED"}


class STB_OT_Import(Operator, ImportHelper):
    bl_idname = "stb.import"
    bl_label = "Import"
    bl_description = "Import the selected Files"

    filter_glob: StringProperty(
        default='*.zip;*.py',
        options={'HIDDEN'},
        maxlen=255
    )
    files: CollectionProperty(type=PropertyGroup)

    @classmethod
    def poll(cls, context: Context):
        STB_pref = get_preferences(context)
        return STB_pref.selected_button != ""

    def execute(self, context: Context):
        not_added_file = []
        button_fails = ([], [])
        directory = os.path.dirname(self.filepath)
        for file in self.files:
            if file.name.endswith(".zip"):
                zip_fails = functions.import_zip(
                    os.path.join(directory, file.name),
                    context
                )
                button_fails[0].extend(zip_fails[0])
                button_fails[1].extend(zip_fails[1])
            elif file.name.endswith(".py"):
                py_fail = functions.import_py(
                    os.path.join(directory, file.name),
                    context
                )
                button_fails[0].extend(py_fail[0])
                button_fails[1].append(py_fail[1])
            else:
                not_added_file.append(file)

        has_message = False
        message = "Not all Files could be added:\n"
        for file in not_added_file:
            message += "%s\n" % file
            has_message = True

        has_fail_message = False
        fail_message = "Not all Areas or Properties could be added because the Syntax is invalid:\n"
        for name, fails in zip(button_fails[0], button_fails[1]):
            if len(fails[0]) or len(fails[1]):
                fail_message += "\n %s:" % name
                fail_message += functions.create_fail_message(fails)
                has_fail_message = True

        if has_message and has_fail_message:
            self.report({'ERROR'}, "%s\n\n%s" % (message, fail_message))
        elif has_message:
            self.report({'ERROR'}, message)
        elif has_fail_message:
            self.report({'ERROR'}, fail_message)
        context.area.tag_redraw()
        return {"FINISHED"}


class STB_OT_Edit(Operator):
    bl_idname = "stb.edit"
    bl_label = "Edit"
    bl_description = "Edit the selected Button"
    bl_options = {"UNDO"}

    area_items = [  # (identifier, name, description, icon, value)
        ('', 'General', '', ''),
        ('3D_Viewport', '3D Viewport', '', 'VIEW3D'),
        ('Image_Editor', 'Image Editor', '', 'IMAGE'),
        ('UV_Editor', 'UV Editor', '', 'UV'),
        ('Compositor', 'Compositor', '', 'NODE_COMPOSITING'),
        ('Texture_Node_Editor', 'Texture Node Editor', '', 'NODE_TEXTURE'),
        ('Geomerty_Node_Editor', 'Geomerty Node Editor', '', 'NODETREE'),
        ('Shader_Editor', 'Shader Editor', '', 'NODE_MATERIAL'),
        ('Video_Sequencer', 'Video Sequencer', '', 'SEQUENCE'),
        ('Movie_Clip_Editor', 'Movie Clip Editor', '', 'TRACKER'),

        ('', 'Animation', '', ''),
        ('Dope_Sheet', 'Dope Sheet', '', 'ACTION'),
        ('Timeline', 'Timeline', '', 'TIME'),
        ('Graph_Editor', 'Graph Editor', '', 'GRAPH'),
        ('Drivers', 'Drivers', '', 'DRIVER'),
        ('Nonlinear_Animation', 'Nonlinear Animation', '', 'NLA'),

        ('', 'Scripting', '', ''),
        ('Text_Editor', 'Text Editor', '', 'TEXT')
    ]

    name: StringProperty(name="Name")
    stb_properties: CollectionProperty(type=properties.STB_edit_property_item)

    @classmethod
    def poll(cls, context: Context):
        STB_pref = get_preferences(context)
        return STB_pref.selected_button != ""

    def items_stb_select_area(self, context: Context):
        for item in self.stb_areas:
            if item.delete:
                self.stb_areas.remove(self.stb_areas.find(item.name))
        used_areas = set(area.name for area in self.stb_areas)
        areas = []
        for i, (identifier, name, description, icon) in enumerate(STB_OT_Edit.area_items):
            if identifier in used_areas:
                continue
            areas.append((
                identifier,
                name,
                description,
                icon,
                i * (identifier != '') - 1
            ))
        return areas
    stb_select_area: EnumProperty(items=items_stb_select_area, default=0)
    stb_areas: CollectionProperty(type=properties.STB_edit_area_item)

    def get_add_area(self):
        return False

    def set_add_area(self, value):
        identifier = self.stb_select_area
        icon = UILayout.enum_item_icon(self, 'stb_select_area', identifier)
        label = UILayout.enum_item_name(self, 'stb_select_area', identifier)
        if identifier == '':
            return
        new = self.stb_areas.add()
        new.name = identifier
        new.label = label
        new.icon = icon
        items = STB_OT_Edit.items_stb_select_area(self, bpy.context)
        for item in items:
            if item[0] == '':
                continue
            self.stb_select_area = item[0]
            break
    add_area: BoolProperty(default=False, get=get_add_area, set=set_add_area)

    def draw(self, context: Context):
        layout = self.layout
        layout.prop(self, 'name')

        layout.separator(factor=0.5)
        layout.label(text="Areas")
        row = layout.row(align=True)
        row.prop(self, 'stb_select_area')
        row.prop(self, 'add_area', icon="ADD", icon_only=True)
        box = layout.box()
        if len(self.stb_areas):
            for area in filter(lambda x: not x.delete, self.stb_areas):
                row = box.row()
                row.label(text=area.label, icon_value=area.icon)
                row.prop(area, 'delete', icon='X', icon_only=True, emboss=False)
        else:
            box.label(text="All Areas", icon='RESTRICT_COLOR_ON')

        properties = list(filter(lambda x: not x.use_delete, self.stb_properties))
        if len(properties):
            layout.separator(factor=0.5)
            layout.label(text="Properties")
            box = layout.box()
            for prop in properties:
                row = box.row()
                row.label(text=f"{prop.name} [Ln {prop.line}]")
                row.prop(prop, 'use_delete', icon='X', icon_only=True, emboss=False)

    def invoke(self, context, event):
        STB_pref = get_preferences(context)
        stb = context.scene.stb
        button = stb[STB_pref.selected_button]
        self.name = button.name
        self.stb_properties.clear()
        self.stb_areas.clear()
        for prop in functions.get_all_properties(button):
            new = self.stb_properties.add()
            new.name = prop.name
            new.line = prop.line
            new.linename = prop.linename
        return context.window_manager.invoke_props_dialog(self, width=250)

    def execute(self, context):
        functions.rename(context, self.name)

        STB_pref = get_preferences(context)
        property_changed = False

        text_index = bpy.data.texts.find(STB_pref.selected_button)
        if text_index == -1:
            functions.get_text(STB_pref.selected_button)
            text = bpy.data.texts[STB_pref.selected_button]
        else:
            text = bpy.data.texts[text_index]
        lines = [line.body for line in text.lines]

        if len(self.stb_areas):
            property_changed = True
            if lines[0].strip().startswith("#STB"):
                line = lines[0]
                line += " /// "
            else:
                line = ""
                lines.insert(0, line)
            line += " /// ".join(map(lambda x: "#STB-Area-%s" % x.name, self.stb_areas))
            lines[0] = line

        edited_lines = []
        for prop in filter(lambda x: x.use_delete, self.stb_properties):
            property_changed = True
            line: str = lines[prop.line - 1]
            line_start = line.find("#STB")
            if line_start == -1:
                continue

            if (init_start_position := line.find("#STB-InitValue-")) != -1:
                init_start_position += len("#STB-InitValue-")
                init_end_position = line.find("-END", init_start_position)
                init_value = line[init_start_position: init_end_position]
                lines[prop.line] = "%s= %s" % (prop.linename, init_value)

            and_position = line.find("///", line_start)
            end_position = line.find("#STB", and_position)
            while ((and_next := line.find("///", end_position)) != -1
                   and (end_next := line.find("#STB", and_next)) != -1):
                and_position = and_next
                end_position = end_next

            if and_position != -1 and end_position != -1:
                line_end = line.find(" ", end_position)
            else:
                line_end = line.find(" ", line_start)

            if line_end == -1:
                line = ""
            else:
                line = line[:line_start] + line[line_end:]

            lines[prop.line - 1] = line
            edited_lines.append(prop.line - 1)

        for i in sorted(edited_lines, reverse=True):
            line = lines[i]
            if line.strip() == "":
                lines.pop(i)

        if property_changed:
            text.clear()
            text.write("\n".join(lines))
            bpy.ops.stb.reload()
        context.area.tag_redraw()
        return {"FINISHED"}


class STB_OT_LoadSingleButton(Operator):
    bl_idname = "stb.load_single_button"
    bl_label = "Load Button"
    bl_description = "Load the script of the selected Button into the Texteditor"

    @classmethod
    def poll(cls, context: Context):
        STB_pref = get_preferences(context)
        return STB_pref.selected_button != ""

    def execute(self, context: Context):
        STB_pref = get_preferences(context)
        stb = context.scene.stb
        functions.get_text(STB_pref.selected_button)
        functions.update_all_props(stb[STB_pref.selected_button], context)
        return {"FINISHED"}


class STB_OT_AddProperty(Operator):
    bl_idname = "stb.add_property"
    bl_label = "Add Property"
    bl_description = "Add a variable from the script as a property"

    text_variables: CollectionProperty(
        type=properties.STB_add_property_item,
        options={'HIDDEN'}
    )

    def text_properties_items(self, context):
        return [
            (str(i), f"{item.line} [Ln {item.position}]", "")
            for i, item in enumerate(self.text_variables)
        ]
    text_properties: EnumProperty(
        items=text_properties_items,
        options={'HIDDEN'}
    )
    space: EnumProperty(
        items=[
            ("Panel", "Panel", "Show this property in the Panel"),
            ("Dialog", "Dialog",
             "Show this property in a Dialog when the script is executed"),
            ("PanelDialog", "Panel & Dialog",
             "Show this property in the Panel and Dialog")
        ],
        options={'HIDDEN'}
    )

    @classmethod
    def poll(cls, context: Context):
        STB_pref = get_preferences(context)
        return STB_pref.selected_button != ""

    def invoke(self, context: Context, event: Event):
        STB_pref = get_preferences(context)
        text_index = bpy.data.texts.find(STB_pref.selected_button)
        if text_index == -1:
            functions.get_text(STB_pref.selected_button)
            text = bpy.data.texts[STB_pref.selected_button]
        else:
            text = bpy.data.texts[text_index]
        items = self.text_properties_items(context)
        if len(items) != 0:
            self.text_properties = items[0][0]
        self.text_variables.clear()
        for position, line, value, bl_type in functions.get_all_variables(text.as_string()):
            var = self.text_variables.add()
            var.position = position
            var.line = line
            var.value = value
            var.type = bl_type
        return context.window_manager.invoke_props_dialog(self)

    def draw(self, context: Context):
        layout = self.layout
        if len(self.text_properties_items(context)) == 0:
            layout.label(text="No Property to add")
            return
        layout.prop(self, 'text_properties', text="Property")
        layout.prop(self, 'space', text="Space")

    def execute(self, context: Context):
        if self.text_properties == "":
            return {'CANCELLED'}
        STB_pref = get_preferences(context)
        text = bpy.data.texts[STB_pref.selected_button]
        index = int(self.text_properties)
        item = self.text_variables[index]
        lines = [line.body for line in text.lines]
        if self.space == "PanelDialog":
            insert_comment = (
                f"#STB-Input-Panel-{item.type} /// #STB-Input-Dialog-{item.type} /// #STB-InitValue-"
                + f"{item.value}-END")
        else:
            insert_comment = f"#STB-Input-{self.space}-{item.type} /// #STB-InitValue-{item.value}-END"
        lines.insert(item.position, insert_comment)
        text.clear()
        text.write("\n".join(lines))
        bpy.ops.stb.reload()
        return {'FINISHED'}


classes = [
    STB_OT_AddButton,
    STB_OT_ScriptButton,
    STB_OT_RemoveButton,
    STB_OT_Load,
    STB_OT_Reload,
    STB_OT_Save,
    STB_OT_Export,
    STB_OT_Import,
    STB_OT_Edit,
    STB_OT_LoadSingleButton,
    STB_OT_AddProperty
]


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)
