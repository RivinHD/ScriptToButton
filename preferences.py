import bpy
from bpy.types import AddonPreferences
from bpy.props import StringProperty, BoolProperty, EnumProperty, CollectionProperty, IntProperty


class STB_preferences(AddonPreferences):
    bl_idname = __package__

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
        return bpy.context.scene.get("button.selected_id", "")
    selected_button: StringProperty(get=get_selected_button, name="INTERNAL")

    update: BoolProperty()
    version: StringProperty()
    restart: BoolProperty()
    auto_update: BoolProperty(
        default=True,
        name="Auto Update",
        description="automatically search for a new update"
    )

    def draw(self, context):
        STB = bpy.context.preferences.addons[__name__].preferences
        layout = self.layout
        row = layout.row()
        row.prop(self, 'autosave')
        row.prop(self, 'autoload')
        row.prop(self, 'delete_script_after_run')
        layout.separator(factor=0.8)
        col = layout.column()
        col.prop(STB, 'auto_update')
        row = col.row()
        if STB.Update:
            row.operator(update.STB_OT_Update.bl_idname, text="Update")
            row.operator(update.STB_OT_ReleaseNotes.bl_idname,
                         text="Release Notes")
        else:
            row.operator(update.STB_OT_CheckUpdate.bl_idname,
                         text="Check For Updates")
            if STB.Restart:
                row.operator(update.STB_OT_Restart.bl_idname,
                             text="Restart to Finish")
        if STB.Version != '':
            if STB.Update:
                col.label(
                    text="A new Version is available (" + STB.Version + ")")
            else:
                col.label(
                    text="You are using the latest Version (" + STB.Version + ")")


def register():
    bpy.utils.register_module(STB_preferences)


def unregister():
    bpy.utils.unregister_module(STB_preferences)
