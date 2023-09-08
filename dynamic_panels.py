import typing
import bpy
from bpy.types import Panel, Context, Menu

button_classes = {}
panel_names = []

ui_space_types = [
    'CLIP_EDITOR', 'NODE_EDITOR', 'TEXT_EDITOR', 'SEQUENCE_EDITOR', 'NLA_EDITOR',
    'DOPESHEET_EDITOR', 'VIEW_3D', 'GRAPH_EDITOR', 'IMAGE_EDITOR'
]  # blender spaces with UI region


def register_button_panel(name: str):
    unregister_register_button_panel(name, True)


def unregister_button_panel(name: str):
    unregister_register_button_panel(name, False)


def unregister_register_button_panel(name: str, register: bool):
    index = len(panel_names) - (not register)
    for space_type in ui_space_types:
        class STB_PT_Buttons(Panel):
            bl_idname = "STB_PT_Buttons_%s_%s" % (index, space_type)
            bl_label = ""
            bl_space_type = space_type
            bl_region_type = "UI"
            bl_category = "Script To Button"
            bl_options = {"INSTANCED"}
            bl_parent_id = "STB_PT_ScriptToButton_%s" % space_type
            bl_order = index

            @classmethod
            def poll(self, context: Context) -> bool:
                stb = context.scene.stb
                area = context.area.ui_type
                panel = panel_names[self.bl_order]
                return any((button.panel == panel and area in button.areas) for button in stb)

            def draw_header(self, context: Context):
                layout = self.layout
                layout.label(text=panel_names[self.bl_order])

            def draw(self, context):
                layout = self.layout
                area = context.area.ui_type
                panel = panel_names[self.bl_order]
                buttons = filter(
                    lambda x: area in x.areas and x.panel == panel,
                    context.scene.stb
                )
                for button in sorted(buttons, key=lambda x: x.name):
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
        STB_PT_Buttons.__name__ = "STB_PT_Buttons_%s_%s" % (index, space_type)

        global button_classes
        if register:
            button_classes[STB_PT_Buttons.__name__] = STB_PT_Buttons
            bpy.utils.register_class(STB_PT_Buttons)
        else:
            bpy.utils.unregister_class(button_classes[STB_PT_Buttons.__name__])
            del button_classes[STB_PT_Buttons.__name__]

    class STB_MT_Buttons(Menu):
        bl_idname = "STB_MT_Buttons_%s" % index
        bl_label = "Category"
        bl_order = index

        @classmethod
        def poll(self, context: Context) -> bool:
            stb = context.scene.stb
            area = context.area
            if area is None:
                return False
            area = context.area.ui_type
            panel = panel_names[self.bl_order]
            return any((button.panel == panel and area in button.areas) for button in stb)

        def draw(self, context: Context):
            layout = self.layout
            area = context.area.ui_type
            panel = panel_names[self.bl_order]
            buttons = filter(
                lambda x: area in x.areas and x.panel == panel,
                context.scene.stb
            )
            for button in sorted(buttons, key=lambda x: x.name):
                layout.operator(
                    "stb.script_button",
                    text=button.name
                ).name = button.name
    STB_MT_Buttons.__name__ = "STB_MT_Buttons_%s" % index

    if register:
        bpy.utils.register_class(STB_MT_Buttons)
        panel_names.append(name)
        panel_names.sort()
    else:
        bpy.utils.register_class(getattr(bpy.types, STB_MT_Buttons.__name__))
        panel_names.remove(name)
        panel_names.sort()


def unregister():
    for cls in button_classes.values():
        bpy.utils.unregister_class(cls)
    panel_names.clear()
