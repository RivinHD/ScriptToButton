import bpy
from bpy.types import Operator, Context, Event, PropertyGroup
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
            functions.update_all_props(stb[self.name])
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

    def draw(self, context: Context):
        STB_pref = get_preferences(context)
        layout = self.layout
        layout.prop(self, 'deleteFile', text="Delete File")
        row = layout.row()
        text_enabled = bpy.data.texts.find(STB_pref.selected_button) != -1
        row.enabled = text_enabled
        self.deleteText = text_enabled
        row.prop(self, 'deleteText', text="Delete Text", toggle=False)

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
        name="Load from ",
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
        type=properties.TextsProperty,
        name="Texts in Texteditor"
    )

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
            if self.All:
                for text in self.Texts:
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
        if self.Mode == "file":
            fails = functions.load(context)
        elif self.Mode == "texteditor":
            fails = functions.load_from_texteditor(self, context)
        mes = "\n"
        for name, fail in zip(fails[0], fails[1]):
            if len(fail[0]) or len(fail[1]):
                mes += "\n %s:" % name
                mes += functions.create_fail_message(fail)
        if mes != "\n":
            self.report(
                {'ERROR'},
                "Not all Areas or Properties could be added because the Syntax is invalid: %s" % mes
            )
        context.area.tag_redraw()
        return {"FINISHED"}


class STB_OT_Reload(Operator):
    bl_idname = "stb.reload"
    bl_label = "Reload"
    bl_description = "Reload the linked Text in the Texteditor of the selected Button"
    bl_options = {"REGISTER"}

    def execute(self, context: Context):
        STB_pref = get_preferences(context)
        stb = context.scene.stb
        text_index = bpy.data.texts.find(STB_pref.selected_button)
        if text_index != -1:
            if STB_pref.autosave:
                functions.save_text(
                    bpy.data.texts[text_index], STB_pref.selected_button)
            fails = functions.reload_button_text(
                stb[STB_pref.selected_button],
                bpy.data.texts[text_index].as_string()
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
                ("%s could not be reloaded, linked Text in Texteditor don't exist."
                 ""
                 "INFO: The linked Text must have the same name as the Button"
                 ) % STB_pref.selected_button
            )
        context.area.tag_redraw()
        return {"FINISHED"}


class STB_OT_Save(Operator):
    bl_idname = "stb.save"
    bl_label = "Save"
    bl_description = "Save all buttons to the Storage"

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
        return self.get("mode", "py")

    def set_mode(self, value):
        self["mode"] = value
        if value == "py":
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

    filename_ext: StringProperty(default=".", get=get_filename_ext)

    def get_use_filter_folder(self):
        return self.mode == "py"

    use_filter_folder: BoolProperty(default=True, get=get_use_filter_folder)
    filepath: StringProperty(name="File Path", maxlen=1024, default="")
    directory: StringProperty(name="Folder Path", maxlen=1024, default="")

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
            map(lambda x: x.use, self.export_buttons),
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


class STB_OT_Rename(Operator):
    bl_idname = "stb.rename"
    bl_label = "Rename"
    bl_description = "Rename the seleccted Button"
    bl_options = {"UNDO"}

    name: StringProperty(name="Name")

    def draw(self, context: Context):
        layout = self.layout
        layout.prop(self, 'name', text="Name")

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)

    def execute(self, context):
        functions.rename(context, self.name)
        context.area.tag_redraw()
        return {"FINISHED"}


class STB_OT_LoadSingleButton(Operator):
    bl_idname = "stb.load_single_button"
    bl_label = "Load Button"
    bl_description = "Load the script of the selected Button into the Texteditor"

    def execute(self, context):
        STB_pref = get_preferences(context)
        stb = context.scene.stb
        functions.get_text(STB_pref.selected_button)
        functions.update_all_props(stb[STB_pref.selected_button])
        return {"FINISHED"}


classes = [
    STB_OT_AddButton,
    STB_OT_ScriptButton,
    STB_OT_ScriptButton,
    STB_OT_Load,
    STB_OT_Reload,
    STB_OT_Save,
    STB_OT_Export,
    STB_OT_Import,
    STB_OT_Rename,
    STB_OT_LoadSingleButton
]


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)
