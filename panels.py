import bpy
from bpy.types import Panel, Context
from .functions import get_preferences
from . import functions

classes = []

ui_space_types = [
    'CLIP_EDITOR', 'NODE_EDITOR', 'TEXT_EDITOR', 'SEQUENCE_EDITOR', 'NLA_EDITOR',
    'DOPESHEET_EDITOR', 'VIEW_3D', 'GRAPH_EDITOR', 'IMAGE_EDITOR'
]  # blender spaces with UI region


def panel_factory(space_type):
    class STB_PT_ScriptToButton(Panel):
        bl_idname = "STB_PT_ScriptToButton_%s" % space_type
        bl_label = "Script To Button"
        bl_space_type = space_type
        bl_region_type = "UI"
        bl_category = "Script To Button"

        def draw(self, context: Context):
            layout = self.layout
            STB_pref = get_preferences(context)
            col = layout.column()
            row = col.row(align=True)
            row.operator("stb.add_button", text="Add", icon='ADD')
            row.operator("stb.remove_button", text="Remove", icon='REMOVE')
            if STB_pref.autosave:
                row = col.row()
                row.operator("stb.load", text="Load")
                row2 = row.row(align=True)
                row2.scale_x = 1.2
                row2.operator("stb.load_single_button", text="", icon='TEXT')
                row2.operator("stb.reload", text="", icon='FILE_REFRESH')
                row2.operator("stb.edit", text="", icon='GREASEPENCIL')
            else:
                row = col.row(align=True)
                row.operator("stb.load", text="Load")
                row.operator("stb.save", text="Save")
                row = col.row(align=True)
                row.operator(
                    "stb.load_single_button",
                    text="Load Button",
                    icon='TEXT'
                )
                row = col.row(align=True)
                row.operator("stb.reload", text="Reload", icon='FILE_REFRESH')
                row.operator("stb.edit", text="Rename", icon='GREASEPENCIL')
            row = col.row(align=True)
            row.operator("stb.export", text="Export", icon='EXPORT')
            row.operator("stb.import", text="Import", icon='IMPORT')
    STB_PT_ScriptToButton.__name__ = "STB_PT_ScriptToButton_%s" % space_type

    class STB_PT_Properties(Panel):
        bl_idname = "STB_PT_Properties_%s" % space_type
        bl_label = "Properties"
        bl_space_type = space_type
        bl_region_type = "UI"
        bl_category = "Script To Button"
        bl_parent_id = "STB_PT_ScriptToButton_%s" % space_type
        bl_order = 2147483647  # max size

        def draw_header(self, context: Context):
            layout = self.layout
            layout.alignment = 'RIGHT'
            layout.operator('stb.add_property', text="", icon='ADD')

        def draw(self, context):
            layout = self.layout
            stb = context.scene.stb
            STB_pref = get_preferences(context)
            if len(stb):
                if STB_pref.selected_button == "":
                    layout.label(text="No Properties")
                    return
                button = stb[STB_pref.selected_button]
                sort, back = functions.sort_props(button, 'Panel')
                if not (len(sort) > 0 or len(back) > 0):
                    layout.label(text="No Properties")
                    return
                functions.draw_sort(sort, back, layout)
    STB_PT_Properties.__name__ = "STB_PT_Properties_%s" % space_type

    global classes
    classes += [
        STB_PT_ScriptToButton,
        STB_PT_Properties
    ]


for space in ui_space_types:
    panel_factory(space)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)
