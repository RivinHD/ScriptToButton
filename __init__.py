import bpy
from bpy.props import StringProperty, EnumProperty, PointerProperty, CollectionProperty, BoolProperty
import os
from bpy.app.handlers import persistent

bl_info = {
    "name" : "Scripts To Button",
    "author" : "RivinHD",
    "blender" : (2, 83, 0),
    "version" : (1, 0, 3),
    "location" : "View3D",
    "category" : "Generic"
}

def SaveText(ActiveText, ScriptName):
    #In real add-on: os.path.dirname(__file__) + "\Storage\mytxt.py"
    text = ActiveText.as_string()
    destination = os.path.dirname(__file__) + "/Storage/" + ScriptName + ".py"
    with open(destination, 'w', encoding='utf8') as outfile:
        outfile.write(text)

def GetText(ScriptName):
    destination = os.path.dirname(__file__) + "/Storage/" + ScriptName + ".py"
    if bpy.data.texts.find(ScriptName) == -1:
        bpy.data.texts.new(ScriptName)
    else:
        bpy.data.texts[ScriptName].clear()
    with open(destination, 'r', encoding='utf8') as infile:
        bpy.data.texts[ScriptName].write(infile.read())

def GetAllSavedScripts():
    path = os.path.dirname(__file__) + "/Storage"
    if not os.path.exists(path):
        os.mkdir(path)
    l = []
    for file in os.listdir(path):
        l.append(file.replace(".py",""))
    return l


classes = []
class AddButtonPanel(bpy.types.Panel):
    bl_idname = "stb.addpanel"
    bl_label = "Add Button"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Scripts To Button"

    def draw(self, context):
        stb = context.scene.p_stb
        layout = self.layout
        col = layout.column()
        col.prop(stb, "ButtonName")
        col.prop(stb, "TextsList")
        col.operator(AddButton.bl_idname)
classes.append(AddButtonPanel) 

class AddButton(bpy.types.Operator):
    bl_idname = "stb.addbutton"
    bl_label = "Add Button"
    bl_description = "button"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        stb = context.scene.p_stb
        if stb.ButtonName == '':
            self.report({'ERROR'}, "You need a name for the Button")
        elif stb.ButtonName in GetAllSavedScripts():
            self.report({'ERROR'}, "You need an other Button name, this name is already used")
        elif stb.TextsList == '':
            self.report({'ERROR'}, "You need to select a Text")
        else:
            SaveText(bpy.data.texts[stb.TextsList], stb.ButtonName)
            new = context.scene.c_stb.add()
            new.name = stb.ButtonName
            new.btn_name = stb.ButtonName
            new = context.scene.t_stb.add()
            new.name = stb.ButtonName
            new.btn_name = stb.ButtonName
            GetText(stb.ButtonName)
        return {"FINISHED"}

classes.append(AddButton)

def textlist(self, context):
    l = []
    for i in bpy.data.texts:
        st1 = i.name
        st2 = i.name
        st3 = ""
        l.append((st1,st2,st3))
    return l

class AddPropertys(bpy.types.PropertyGroup):
    ButtonName : StringProperty(name = "Button Name", description = "Set the name of the Button", default = "")
    TextsList : EnumProperty(name="Text", description = "Chose Text for converting into Bar", items = textlist)
classes.append(AddPropertys)

class ButtonPanle(bpy.types.Panel):
    bl_idname = "stb.panel"
    bl_label = "Buttons"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Scripts To Button"

    def draw(self, context):
        layout = self.layout
        for i in range(len(context.scene.c_stb)):
            row = layout.row().split(factor = 0.9)
            btn = context.scene.c_stb[i]
            tbtn = context.scene.t_stb[i]
            row.operator(ScriptButton.bl_idname, text= btn.name).btn_name = btn.name
            row.operator(TrashButton.bl_idname, text= '', icon= 'TRASH').trash_name = tbtn.name

classes.append(ButtonPanle)

class ScriptButton(bpy.types.Operator):
    bl_idname = "stb.scriptbutton"
    bl_label = "ScriptButton"
    bl_options = {"REGISTER","UNDO"}

    btn_name : StringProperty()

    def execute(self, context):
        text = bpy.data.texts[self.btn_name]
        ctx = bpy.context.copy()
        ctx['edit_text'] = text
        bpy.ops.text.run_script(ctx)
        return {"FINISHED"}
classes.append(ScriptButton)

@persistent
def LoadSaves(dummy):
    scene = bpy.context.scene
    for script in GetAllSavedScripts():
        new = scene.c_stb.add()
        new.name = script
        new.btn_name = script
        new = scene.t_stb.add()
        new.name = script
        new.btn_name = script
        GetText(script)

class ButtonPropertys(bpy.types.PropertyGroup):
    btn_name = StringProperty()
classes.append(ButtonPropertys)

class TrashButton(bpy.types.Operator):
    bl_idname = "stb.trashbutton"
    bl_label = ""
    bl_description = "Delet the Button next to it"
    bl_options = {"REGISTER"}

    trash_name = StringProperty()

    def execute(self, context):
        index = int(context.scene.t_stb[self.trash_name].path_from_id().replace("t_stb[","").replace("]",""))
        os.remove(os.path.dirname(__file__) + "/Storage/" + context.scene.c_stb[index].name + ".py")
        bpy.data.texts.remove(bpy.data.texts[context.scene.c_stb[index].name])
        context.scene.c_stb.remove(index)
        context.scene.t_stb.remove(index)
        return {"FINISHED"}
classes.append(TrashButton)

class TrashPropertys(bpy.types.PropertyGroup):
    trash_name = StringProperty()
classes.append(TrashPropertys)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.p_stb = PointerProperty(type = AddPropertys)
    bpy.types.Scene.c_stb = CollectionProperty(type = ButtonPropertys)
    bpy.types.Scene.t_stb = CollectionProperty(type = TrashPropertys)
    bpy.app.handlers.load_factory_startup_post.append(LoadSaves)

def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)
    del bpy.types.Scene.p_stb
    del bpy.types.Scene.c_stb
    del bpy.types.Scene.t_stb
    bpy.app.handlers.load_factory_startup_post.remove(LoadSaves)