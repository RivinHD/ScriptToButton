import bpy
from bpy.types import Operator
from bpy.app.handlers import persistent
import requests
import base64
import zipfile
import json
import os
from io import BytesIO
import webbrowser

config = {
    "checkSource_URL": 'https://api.github.com/repos/RivinHD/ScriptToButton/contents/__init__.py',
    "repoSource_URL": 'https://github.com/RivinHD/ScriptToButton',
    "releasNotes_URL": "https://github.com/RivinHD/ScriptToButton/releases"
}
classes = []

# functions
def CheckForUpdate():
    try:
        updateSource = requests.get(config["checkSource_URL"])
        data = json.loads(updateSource.content.decode("utf-8"))
        updateContent = base64.b64decode(data["content"]).decode("utf-8")
        with open(os.path.join(os.path.dirname(__file__),"__init__.py"), 'r', encoding= "utf-8", errors='ignore') as currentFile:
            currentContext = currentFile.read()
            lines = currentContext.splitlines()
            for i in range(50):
                if lines[i].strip().startswith('"version"'):
                    currentVersion = GetVersion(lines[i])
                    lines = updateContent.splitlines()
                    for j in range(50):
                        if lines[j].strip().startswith('"version"'):
                            updateVersion = GetVersion(lines[j])
                            if updateVersion[0] > currentVersion[0] or (updateVersion[0] == currentVersion[0] and updateVersion[1] > currentVersion[1]) or (updateVersion[0] == currentVersion[0] and updateVersion[1] == currentVersion[1] and updateVersion[2] > currentVersion[2]):
                                return (True, updateVersion)
                            else:
                                return (False, currentVersion)          
    except Exception as e:
        print(e)
        return (False, "no Connection")                 
    return (False, "Error")

def GetVersion(line):
    return eval("(%s)" %line.split("(")[1].split(")")[0])

def Update():
    source = requests.get(config["repoSource_URL"] + "/archive/master.zip")
    with zipfile.ZipFile(BytesIO(source.content)) as extract:
        for exct in extract.namelist():
            tail, head = os.path.split(exct)
            dirpath = os.path.join(bpy.app.tempdir, "STB_Update")   
            if not os.path.exists(dirpath):
                os.mkdir(dirpath)
            temppath = os.path.join(dirpath, __package__)
            if not os.path.exists(temppath):
                os.mkdir(temppath)
            if len(tail.split('/')) == 1 and head.endswith(".py"):
                with open(os.path.join(temppath, head), 'w', encoding= 'utf8') as tempfile:
                    tempfile.write(extract.read(exct).decode("utf-8"))
        zippath = os.path.join(bpy.app.tempdir, "STB_Update/" + __package__ +".zip")
        with zipfile.ZipFile(zippath, 'w') as zip_it:
            for tempfile in os.listdir(temppath):
                if tempfile.endswith(".py"):
                    currentpath = os.path.join(temppath, tempfile)
                    zip_it.write(currentpath, os.path.join(__package__, tempfile))
                    os.remove(currentpath)
            else:
                os.rmdir(temppath)
        bpy.ops.preferences.addon_install(filepath= zippath)
        os.remove(zippath)
        os.rmdir(dirpath)

@persistent
def onStart(dummy = None):
    STB = bpy.context.preferences.addons[__package__].preferences
    STB.Update = False
    STB.Version = ''
    STB.Restart = False
    if STB.AutoUpdate:
        bpy.ops.STB.check_update('EXEC_DEFAULT')

# Operators
class STB_OT_CheckUpdate(Operator):
    bl_idname = "stb.check_update"
    bl_label = "Check for Update"
    bl_description = "check for available update"

    def execute(self, context):
        update = CheckForUpdate()
        STB = context.preferences.addons[__package__].preferences
        STB.Update = update[0]
        if isinstance(update[1], str):
            STB.Version = update[1]
        else:
            STB.Version = ".".join([str(i) for i in update[1]])
        return {"FINISHED"}
classes.append(STB_OT_CheckUpdate)

class STB_OT_Update(Operator):
    bl_idname = "stb.update"
    bl_label = "Update"
    bl_description = "install the new version"

    def execute(self, context):
        STB = bpy.context.preferences.addons[__package__].preferences
        STB.Update = False
        STB.Restart = True
        Update()
        bpy.ops.stb.restart('INVOKE_DEFAULT')
        return {"FINISHED"}
classes.append(STB_OT_Update)

class STB_OT_Restart(Operator):
    bl_idname = "stb.restart"
    bl_label = "Restart Blender"
    bl_description = "Restart Blender"

    def execute(self, context):
        path = bpy.data.filepath
        if path == '':
            os.startfile(bpy.app.binary_path)
        else:
            bpy.ops.wm.save_mainfile(filepath= path)
            os.startfile(path)
        bpy.ops.wm.quit_blender()
        return {"FINISHED"}
    
    def draw(self, context):
        layout = self.layout
        box = layout.box()
        box.label(text= "You need to restart Blender to complete the Update")

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)
classes.append(STB_OT_Restart)

class STB_OT_ReleaseNotes(Operator):
    bl_idname = "stb.releasenotes"
    bl_label = "Release Notes"
    bl_description = "open the Releas Notes in the Web-Browser"

    def execute(self, context):
        webbrowser.open(config['releasNotes_URL'])
        return {"FINISHED"}
classes.append(STB_OT_ReleaseNotes)

# def Registartion
def register():
    bpy.app.handlers.load_post.append(onStart)

def unregister():
    bpy.app.handlers.load_post.remove(onStart)
