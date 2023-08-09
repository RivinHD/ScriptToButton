import bpy
from bpy.types import Operator, Context, Event
from bpy_extras.io_utils import ExportHelper
from bpy.props import EnumProperty, BoolProperty
from bpy.app.handlers import persistent
import requests
import base64
import zipfile
import json
import os
from io import BytesIO
import sys
import subprocess
import webbrowser
from .functions import get_preferences

config = {
    "checkSource_URL": 'https://api.github.com/repos/RivinHD/ScriptToButton/contents/__init__.py',
    "repoSource_URL": 'https://github.com/RivinHD/ScriptToButton',
    "releaseNotes_URL": "https://github.com/RivinHD/ScriptToButton/releases"
}


def check_for_update():
    try:
        update_source = requests.get(config["checkSource_URL"])
    except requests.ConnectionError as e:
        print(e)
        return (False, "no Connection")

    data = json.loads(update_source.content.decode("utf-8"))
    update_content = base64.b64decode(data["content"]).decode("utf-8")
    path = os.path.join(os.path.dirname(__file__), "__init__.py")
    with open(path, 'r', encoding="utf-8", errors='ignore') as file:
        text = file.read()

    current_version = (0, 0, 0)
    lines = text.splitlines()
    for line in lines:
        if line.strip().startswith('"version"'):
            current_version = get_version(line)

    update_version = (0, 0, 0)
    lines = update_content.splitlines()
    for line in lines:
        if lines.strip().startswith('"version"'):
            update_version = getattr(line)

    if update_version > current_version:
        return (True, update_version)
    else:
        return (False, current_version)


def get_version(line):
    return eval("(%s)" % line.split("(")[1].split(")")[0])


def update():
    source = requests.get(os.path.join(
        config["repoSource_URL"], "/archive/master.zip"))
    with zipfile.ZipFile(BytesIO(source.content)) as extract:
        for file in extract.namelist():
            tail, head = os.path.split(file)

            dirpath = os.path.join(bpy.app.tempdir, "STB_Update")
            if not os.path.exists(dirpath):
                os.mkdir(dirpath)

            temp_path = os.path.join(dirpath, __package__)
            if not os.path.exists(temp_path):
                os.mkdir(temp_path)

            if len(tail.split('/')) == 1 and head.endswith(".py"):
                with open(os.path.join(temp_path, head), 'w', encoding='utf8') as tempfile:
                    tempfile.write(extract.read(file).decode("utf-8"))

        zip_path = os.path.join(
            bpy.app.tempdir,
            "STB_Update",
            "%s.zip" % __package__
        )

        with zipfile.ZipFile(zip_path, 'w') as zip_it:
            for tempfile in os.listdir(temp_path):
                if not tempfile.endswith(".py"):
                    continue
                current_path = os.path.join(temp_path, tempfile)
                zip_it.write(
                    current_path,
                    os.path.join(__package__, tempfile)
                )
                os.remove(current_path)
            else:
                os.rmdir(temp_path)

        bpy.ops.preferences.addon_install(filepath=zip_path)
        os.remove(zip_path)
        os.rmdir(dirpath)


@persistent
def on_start(dummy=None):
    STB_pref = get_preferences(bpy.context)
    STB_pref.update = False
    STB_pref.version = ''
    STB_pref.restart = False
    if STB_pref.auto_update:
        bpy.ops.stb.check_update('EXEC_DEFAULT')


class STB_OT_CheckUpdate(Operator):
    bl_idname = "stb.check_update"
    bl_label = "Check for Update"
    bl_description = "check for available update"

    def execute(self, context: Context):
        update = check_for_update()
        STB_pref = get_preferences(context)
        STB_pref.update = update[0]
        if isinstance(update[1], str):
            STB_pref.version = update[1]
        else:
            STB_pref.version = ".".join([str(i) for i in update[1]])
        return {"FINISHED"}


class STB_OT_Update(Operator):
    bl_idname = "stb.update"
    bl_label = "Update"
    bl_description = "install the new version"

    def execute(self, context):
        STB_pref = get_preferences(context)
        STB_pref.update = False
        STB_pref.restart = True
        update()
        bpy.ops.stb.show_restart_menu('INVOKE_DEFAULT')
        context.area.tag_redraw()
        return {"FINISHED"}


class STB_OT_Restart(Operator, ExportHelper):
    bl_idname = "stb.restart"
    bl_label = "Restart Blender"
    bl_description = "Restart Blender"
    bl_options = {"INTERNAL"}

    save: BoolProperty(default=False)
    filename_ext = ".blend"
    filter_folder: BoolProperty(default=True, options={'HIDDEN'})
    filter_blender: BoolProperty(default=True, options={'HIDDEN'})

    def draw(self, context: Context) -> None:
        pass

    def invoke(self, context: Context, event: Event) -> set[str]:
        if self.save and not bpy.data.filepath:
            return ExportHelper.invoke(self, context, event)
        else:
            return self.execute(context)

    def execute(self, context: Context) -> set[str]:
        STB_pref = get_preferences(context)
        path = bpy.data.filepath
        if self.save:
            if not path:
                path = self.filepath
                if not path:
                    return ExportHelper.invoke(self, context, None)
            bpy.ops.wm.save_mainfile(filepath=path)
        STB_pref.restart = False
        if os.path.exists(path):
            args = [*sys.argv, path]
        else:
            args = sys.argv
        subprocess.Popen(args)
        bpy.ops.wm.quit_blender()
        return {"FINISHED"}


class STB_OT_ShowRestartMenu(Operator):
    bl_idname = "stb.show_restart_menu"
    bl_label = "Restart Blender"
    bl_description = "Restart Blender"
    bl_options = {'REGISTER', 'UNDO'}

    restart_options: EnumProperty(
        items=[
            ("exit", "Don't Restart", "Don't restart and exit this window"),
            ("save", "Save & Restart", "Save & Restart Blender"),
            ("restart", "Restart", "Restart Blender")
        ])

    def invoke(self, context: Context, event: Event) -> set[str]:
        return context.window_manager.invoke_props_dialog(self)

    def execute(self, context: Context) -> set[str]:
        if self.restart_options == "save":
            bpy.ops.stb.restart(save=True)
        elif self.restart_options == "restart":
            bpy.ops.stb.restart()
        return {"FINISHED"}

    def cancel(self, context: Context) -> None:
        bpy.ops.stb.show_restart_menu("INVOKE_DEFAULT")

    def draw(self, context: Context) -> None:
        STB_pref = get_preferences(context)
        layout = self.layout
        if STB_pref.restart:
            layout.label(
                text="You need to restart Blender to complete the Update"
            )
        layout.prop(self, 'restart_options', expand=True)


class STB_OT_ReleaseNotes(Operator):
    bl_idname = "stb.release_notes"
    bl_label = "Release Notes"
    bl_description = "open the Release Notes in the Web-Browser"

    def execute(self, context: Context):
        webbrowser.open(config['releaseNotes_URL'])
        return {"FINISHED"}


classes = [
    STB_OT_CheckUpdate,
    STB_OT_Update,
    STB_OT_Restart,
    STB_OT_ShowRestartMenu,
    STB_OT_ReleaseNotes
]


def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.app.handlers.load_post.append(on_start)


def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)
    bpy.app.handlers.load_post.remove(on_start)
