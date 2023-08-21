import bpy
from bpy.types import Menu, Context
from . import dynamic_panels as panels


class STB_MT_ButtonMenu(bpy.types.Menu):
    bl_idname = "STB_MT_ButtonMenu"
    bl_label = "Script To Buttons"

    def draw(self, context: Context):
        layout = self.layout
        for index, name in enumerate(panels.panel_names):
            menu_name = "STB_MT_Buttons_%s" % index
            if getattr(bpy.types, menu_name).poll(context):
                layout.menu(menu_name, text=name)


def register():
    bpy.utils.register_class(STB_MT_ButtonMenu)


def unregister():
    bpy.utils.unregister_class(STB_MT_ButtonMenu)
