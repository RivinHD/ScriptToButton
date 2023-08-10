import bpy
from bpy.types import Panel, Context
from .functions import get_preferences
from . import functions

classes = []

ui_space_types = [
    'CLIP_EDITOR', 'NODE_EDITOR', 'TEXT_EDITOR', 'SEQUENCE_EDITOR', 'NLA_EDITOR',
    'DOPESHEET_EDITOR', 'VIEW_3D', 'GRAPH_EDITOR', 'IMAGE_EDITOR'
]  # blender spaces with UI region


def panel_factory(spaceType):
    class STB_PT_Controls(Panel):
        bl_idname = "STB_PT_Controls_%s" % spaceType
        bl_label = "Controls"
        bl_space_type = spaceType
        bl_region_type = "UI"
        bl_category = "Script To Button"

        def draw(self, context: Context):
            layout = self.layout
            STB_pref = get_preferences(context)
            if STB_pref.auto_update and STB_pref.update:
                box = layout.box()
                box.label(
                    text="A new Version is available (" + STB_pref.version + ")")
                box.operator("stb.update", text="Update")
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
                row2.operator("stb.rename", text="", icon='GREASEPENCIL')
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
                row.operator("stb.rename", text="Rename", icon='GREASEPENCIL')
            row = col.row(align=True)
            row.operator("stb.export", text="Export", icon='EXPORT')
            row.operator("stb.import", text="Import", icon='IMPORT')
    STB_PT_Controls.__name__ = "STB_PT_Controls_%s" % spaceType

    class STB_PT_Buttons(Panel):
        bl_idname = "STB_PT_Buttons_%s" % spaceType
        bl_label = "Buttons"
        bl_space_type = spaceType
        bl_region_type = "UI"
        bl_category = "Script To Button"

        def draw(self, context):
            layout = self.layout
            for button in context.scene.stb:
                area = context.area.ui_type
                if area not in button.areas:
                    continue
                row = layout.row(align=True)
                row.prop(
                    button, 'selected',
                    toggle=True,
                    text="",
                    icon='RADIOBUT_ON' if button.selected else 'RADIOBUT_OFF'
                )
                row.operator(
                    "stb.script_button",
                    text=button.name
                ).name = button.name
    STB_PT_Buttons.__name__ = "STB_PT_Buttons_%s" % spaceType

    class STB_PT_Properties(Panel):
        bl_idname = "STB_PT_Properties_%s" % spaceType
        bl_label = "Properties"
        bl_space_type = spaceType
        bl_region_type = "UI"
        bl_category = "Script To Button"

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
    STB_PT_Properties.__name__ = "STB_PT_Properties_%s" % spaceType

    global classes
    classes += [
        STB_PT_Controls,
        STB_PT_Buttons,
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
