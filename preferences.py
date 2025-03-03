import bpy
from bpy.types import AddonPreferences, Context
from bpy.props import StringProperty, BoolProperty, EnumProperty, CollectionProperty, IntProperty
from .functions import get_preferences
import rna_keymap_ui
from . import __package__ as base_package

keymaps = {}
keymap_items = []


class STB_preferences(AddonPreferences):
    bl_idname = base_package

    button_name: StringProperty(
        name="Name",
        description="Set the name of the Button",
        default=""
    )

    def text_list_item(self, context):
        return [(i.name, i.name, "") for i in bpy.data.texts]
    texts_list: EnumProperty(
        name="Text",
        description="Chose a Text to convert into a Button",
        items=text_list_item
    )
    autosave: BoolProperty(
        name="Autosave",
        description="Save your changes automatically to the files",
        default=True
    )
    autoload: BoolProperty(
        name="Load to Texteditor",
        description="Load the script into the Texteditor on start, on add or on manuell load",
        default=False
    )
    delete_script_after_run: BoolProperty(
        name="Delete Script after Run",
        description="Delete the script in the editor after the linked script button was pressed",
        default=True
    )

    def get_selected_button(self):
        return bpy.context.scene.get("stb_button.selected_name", "")
    selected_button: StringProperty(get=get_selected_button, name="INTERNAL")

    def draw(self, context: Context) -> None:
        layout = self.layout
        row = layout.row()
        row.prop(self, 'autosave')
        row.prop(self, 'autoload')
        row.prop(self, 'delete_script_after_run')
        layout.separator(factor=0.8)
        col = layout.column()
        kc = bpy.context.window_manager.keyconfigs.user
        for addon_keymap in keymaps.values():
            km = kc.keymaps[addon_keymap.name].active()
            col.context_pointer_set("keymap", km)
            for kmi in km.keymap_items:
                if not any(kmi.name == item.name and kmi.idname == item.idname for item in keymap_items):
                    continue
                rna_keymap_ui.draw_kmi(kc.keymaps, kc, km, kmi, col, 0)


def register():
    bpy.utils.register_class(STB_preferences)

    addon = bpy.context.window_manager.keyconfigs.addon
    if addon:
        km = addon.keymaps.new(name='Screen')
        keymaps['default'] = km
        items = km.keymap_items
        kmi = items.new("wm.call_menu", 'Y', 'PRESS', shift=True, alt=True)
        kmi.properties.name = "STB_MT_ButtonMenu"
        keymap_items.append(kmi)


def unregister():
    bpy.utils.unregister_class(STB_preferences)
    addon = bpy.context.window_manager.keyconfigs.addon
    if not addon:
        return
    for km in keymaps.values():
        if addon.keymaps.get(km.name):
            addon.keymaps.remove(km)
