import bpy
from bpy.app.handlers import persistent
from . import properties, preferences, update, operators, functions

bl_info = {
    "name": "Script To Button",
    "author": "RivinHD",
    "blender": (3, 0, 1),
    "version": (2, 1, 6),
    "location": "View3D",
    "category": "System",
    "doc_url": "https://github.com/RivinHD/ScriptToButton/wiki",
    "tracker_url": "https://github.com/RivinHD/ScriptToButton/issues"
}


@persistent
def load_saves(dummy=None):
    button_fails = functions.load(bpy.context)
    message = "'''"
    for name, fails in zip(button_fails[0], button_fails[1]):
        if len(fails[0]) or len(fails[1]):
            message += "\n %s: " % name
            message += functions.create_fail_message(fails)
    if bpy.data.texts.find('STB Fail Message') == -1:
        if message != "'''":
            bpy.data.texts.new('STB Fail Message')
    else:
        bpy.data.texts['STB Fail Message'].clear()
    if message != "'''":
        bpy.data.texts['STB Fail Message'].write("%s'''" % message)
    functions.NotOneStart[0] = True


def register():
    preferences.register()
    properties.register()
    operators.register()
    update.register()
    bpy.app.handlers.load_post.append(load_saves)


def unregister():
    preferences.unregister()
    properties.unregister()
    operators.unregister()
    update.unregister()
    bpy.app.handlers.load_post.remove(load_saves)
