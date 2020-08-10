import bpy
from bpy.props import StringProperty, EnumProperty, PointerProperty, CollectionProperty, BoolProperty, IntProperty, FloatProperty, BoolVectorProperty, IntVectorProperty, FloatVectorProperty
from bpy.types import Operator, Panel, PropertyGroup, AddonPreferences
import os
from bpy.app.handlers import persistent
from . import functions as imfc
from bpy_extras.io_utils import ImportHelper, ExportHelper

bl_info = {
    "name": "Script To Button",
    "author": "RivinHD",
    "blender": (2, 83, 3),
    "version": (1, 99, 0),
    "location": "View3D",
    "category": "System",
    "doc_url": "https://github.com/RivinHD/ScriptToButton/wiki",
    "tracker_url": "https://github.com/RivinHD/ScriptToButton/issues"
}

classes = []
SpaceTypes = ["VIEW_3D","IMAGE_EDITOR","NODE_EDITOR","SEQUENCE_EDITOR","CLIP_EDITOR","DOPESHEET_EDITOR","GRAPH_EDITOR","NLA_EDITOR","TEXT_EDITOR"]

# Functions ----------------------------------------------------
@persistent
def LoadSaves(dummy = None):
    try:
        bpy.app.timers.unregister(LoadSaves)
        bpy.app.handlers.depsgraph_update_pre.remove(LoadSaves)
    except:
        print("Already Loaded")
        return
    print("------------------Load-----------------")
    btnFails = imfc.Load()
    mes = "'''"
    for name, Fails in zip(btnFails[0], btnFails[1]) :
        if len(Fails[0]) or len(Fails[1]):
            mes += "\n %s: " %name
            mes += imfc.CreatFailmessage(Fails)
    if bpy.data.texts.find('STB Fail Message') == -1:
        if mes != "'''":
            bpy.data.texts.new('STB Fail Message')
    else:
        bpy.data.texts['STB Fail Message'].clear()
    if mes != "'''":
        bpy.data.texts['STB Fail Message'].write(mes + "'''")
    imfc.NotOneStart[0] = True

# Panles -------------------------------------------------------
def panelfactory(spaceType):
    class STB_PT_Controls(bpy.types.Panel):
        bl_idname = "STB_PT_Controls_%s" %spaceType
        bl_label = "Controls"
        bl_space_type = spaceType
        bl_region_type = "UI"
        bl_category = "Script To Button"

        def draw(self, context):
            layout = self.layout
            p_stb = context.preferences.addons[__name__].preferences
            col = layout.column()
            row = col.row(align= True)
            row.operator(STB_OT_AddButton.bl_idname, text= "Add", icon= 'ADD')
            row.operator(STB_OT_RemoveButton.bl_idname, text= "Remove", icon= 'REMOVE')
            if p_stb.Autosave:
                row = col.row()
                row.operator(STB_OT_Load.bl_idname, text= "Load")
                row2 = row.row(align= True)
                row2.scale_x = 1.2
                row2.operator(STB_OT_Reload.bl_idname, text= "", icon= 'FILE_REFRESH')
                row2.operator(SBT_OT_Rename.bl_idname, text= "", icon= 'GREASEPENCIL')
            else:
                row = col.row(align= True)
                row.operator(STB_OT_Load.bl_idname, text= "Load")
                row.operator(STB_OT_Save.bl_idname, text= "Save")
                row = col.row(align= True)
                row.operator(STB_OT_Reload.bl_idname, text= "Reload", icon= 'FILE_REFRESH')
                row.operator(SBT_OT_Rename.bl_idname, text= "Rename", icon= 'GREASEPENCIL')
            row = col.row(align= True)
            row.operator(STB_OT_Export.bl_idname, text= "Export", icon= 'EXPORT')
            row.operator(STB_OT_Import.bl_idname, text= "Import", icon= 'IMPORT')
    STB_PT_Controls.__name__ = "STB_PT_Controls_%s" %spaceType
    classes.append(STB_PT_Controls) 

    class STB_PT_Buttons(bpy.types.Panel):
        bl_idname = "STB_PT_Buttons_%s" %spaceType
        bl_label = "Buttons"
        bl_space_type = spaceType
        bl_region_type = "UI"
        bl_category = "Script To Button"

        def draw(self, context):
            p_stb = context.preferences.addons[__name__].preferences
            layout = self.layout
            for i in range(len(context.scene.b_stb)):
                btn = context.scene.b_stb[i]
                area = STB_PT_Buttons.bl_idname[15:]
                for A in btn.Areas:
                    if area == A.area:
                        row = layout.row(align= True)
                        row.prop(p_stb.SelctedButtonEnum[i], 'selected', toggle= True, text= "", icon= 'RADIOBUT_ON' if p_stb.SelctedButtonEnum[i].selected else 'RADIOBUT_OFF')
                        row.operator(STB_OT_ScriptButton.bl_idname, text= btn.name).btn_name = btn.name
                        break
    STB_PT_Buttons.__name__ = "STB_PT_Buttons_%s" %spaceType
    classes.append(STB_PT_Buttons)

    class STB_PT_Properties(bpy.types.Panel):
        bl_idname = "STB_PT_Properties_%s" %spaceType
        bl_label = "Properties"
        bl_space_type = spaceType
        bl_region_type = "UI"
        bl_category = "Script To Button"

        def draw(self, context):
            empty = True
            propdrawn = False
            layout = self.layout
            b_stb = context.scene.b_stb
            p_stb = context.preferences.addons[__name__].preferences
            if len(b_stb):
                btn = b_stb[p_stb['SelectedButton']]
                col = layout.column(align= True)
                for prop in btn.StringProps:
                    if prop.space == 'Panel':
                        col.prop(prop, 'prop', text= prop.pname)
                        empty = False
                if len(btn.StringProps):
                    col = layout.column(align= True)

                for prop in btn.IntProps:
                    if prop.space == 'Panel':
                        col.prop(prop, 'prop', text= prop.pname)
                        empty = False
                if len(btn.IntProps):
                    col = layout.column(align= True)

                for prop in btn.FloatProps:
                    if prop.space == 'Panel':
                        col.prop(prop, 'prop', text= prop.pname)
                        empty = False
                if len(btn.FloatProps):
                    col = layout.column(align= True)

                for prop in btn.BoolProps:
                    if prop.space == 'Panel':
                        col.prop(prop, 'prop', text= prop.pname)
                        empty = False
                if len(btn.BoolProps):
                    col = layout.column(align= True)

                for prop in btn.EnumProps:
                    if prop.space == 'Panel':
                        col.prop(prop, 'prop', text= prop.pname)
                        empty = False
                if len(btn.EnumProps):
                    col = layout.column(align= True)

                for prop in btn.IntVectorProps:
                    if prop.space == 'Panel':
                        col.prop(eval(prop.address), 'prop', text= prop.pname)
                        empty = False
                if len(btn.IntVectorProps):
                    col = layout.column(align= True)

                for prop in btn.FloatVectorProps:
                    if prop.space == 'Panel':
                        col.prop(eval(prop.address), 'prop', text= prop.pname)
                        empty = False
                if len(btn.FloatVectorProps):
                    col = layout.column(align= True)

                for prop in btn.BoolVectorProps:
                    if prop.space == 'Panel':
                        col.prop(eval(prop.address), 'prop', text= prop.pname)
                        empty = False

                if empty:
                    col.label(text= "No Properties")
    STB_PT_Properties.__name__ = "STB_PT_Properties_%s" %spaceType
    classes.append(STB_PT_Properties)

# Operators -----------------------------------------------------
def SkipTextList(self, context):
    return [(self.Text, self.Text, "")]

class STB_OT_AddButton(bpy.types.Operator):
    bl_idname = "stb.addbutton"
    bl_label = "Add Button"
    bl_description = 'Add a script as Button to the "Buttons" Panel'
    bl_options = {"REGISTER", "UNDO"}

    ShowSkip: BoolProperty(default= False, name= "Show Skip")
    Mode: EnumProperty(items= [("add", "Add", ""),("skip", "Skip", "")], name= "Change Mode", default= "add")
    AllNames = []
    Name : StringProperty(name= "Name")
    Text : StringProperty(name= "Text")
    TextList : EnumProperty(name= "Text", items= SkipTextList)

    def execute(self, context):
        p_stb = context.preferences.addons[__name__].preferences
        p_stb.ButtonName = self.Name
        txt = p_stb.TextsList
        if self.ShowSkip:
            txt = self.Text
        if self.Mode == 'add':
            if self.Name == '':
                self.report({'ERROR'}, "You need a name for the Button")
                return {"FINISHED"}
            elif self.Name in self.AllNames:
                self.report({'INFO'}, txt + " has been overwritten")
            elif p_stb.TextsList == '':
                self.report({'ERROR'}, "You need to select a Text")
                return {"FINISHED"}
            Fails = imfc.AddButton(p_stb, self.Name, txt)
            if len(Fails[0]) or len(Fails[1]):
                self.report({'ERROR'}, "Not all Areas or Properties could be added because the Syntax is invailid: %s" % imfc.CreatFailmessage(Fails))
            p_stb.SelectedButton # Update this Enum
        bpy.context.area.tag_redraw()
        return {"FINISHED"}
    
    def invoke(self, context, event):
        p_stb = context.preferences.addons[__name__].preferences
        self.AllNames = imfc.GetAllButtonnames()
        if self.ShowSkip:
            self.Name = p_stb.ButtonName
            self.Text = p_stb.TextsList
        return context.window_manager.invoke_props_dialog(self)

    def draw(self, context):
        p_stb = context.preferences.addons[__name__].preferences
        layout = self.layout
        if self.ShowSkip:
            layout.prop(self, 'Mode', expand= True)
        if self.Mode == 'add':
            if p_stb.ButtonName in self.AllNames:
                box = layout.box()
                box.alert = True
                box.label(text= '"' + p_stb.ButtonName + '" will be overwritten', icon= 'ERROR')
            col = layout.column()
            col.prop(self, 'Name')
            col = layout.column()
            if self.ShowSkip:
                col.enabled = False
                col.prop(self, 'TextList')
            else:
                col.prop(p_stb, 'TextsList')
classes.append(STB_OT_AddButton)

class STB_OT_ScriptButton(bpy.types.Operator):
    bl_idname = "stb.scriptbutton"
    bl_label = "ScriptButton"
    bl_options = {"UNDO","INTERNAL"}

    btn_name: StringProperty()

    def execute(self, context):
        text = bpy.data.texts[self.btn_name]
        ctx = bpy.context.copy()
        ctx['edit_text'] = text
        try:
            bpy.ops.text.run_script(ctx)
        except:
            error = imfc.GetConsoleError()
            if error:
                self.report({'ERROR'}, "The linked Script is not working\n\n%s" % error)
            return {'CANCELLED'}
        return {"FINISHED"}

    def draw(self, context):
        empty = True
        propdrawn = False
        layout = self.layout
        b_stb = context.scene.b_stb
        p_stb = context.preferences.addons[__name__].preferences
        if len(b_stb):
            btn = b_stb[p_stb['SelectedButton']]
            col = layout.column(align= True)
            for prop in btn.StringProps:
                if prop.space == 'Dialog':
                    col.prop(prop, 'prop', text= prop.pname)
                    empty = False
            if len(btn.StringProps):
                col = layout.column(align= True)

            for prop in btn.IntProps:
                if prop.space == 'Dialog':
                    col.prop(prop, 'prop', text= prop.pname)
                    empty = False
            if len(btn.IntProps):
                col = layout.column(align= True)

            for prop in btn.FloatProps:
                if prop.space == 'Dialog':
                    col.prop(prop, 'prop', text= prop.pname)
                    empty = False
            if len(btn.FloatProps):
                col = layout.column(align= True)

            for prop in btn.BoolProps:
                if prop.space == 'Dialog':
                    col.prop(prop, 'prop', text= prop.pname)
                    empty = False
            if len(btn.BoolProps):
                col = layout.column(align= True)

            for prop in btn.EnumProps:
                if prop.space == 'Dialog':
                    col.prop(prop, 'prop', text= prop.pname)
                    empty = False
            if len(btn.EnumProps):
                col = layout.column(align= True)

            for prop in btn.IntVectorProps:
                if prop.space == 'Dialog':
                    col.prop(eval(prop.address), 'prop', text= prop.pname)
                    empty = False
            if len(btn.IntVectorProps):
                col = layout.column(align= True)

            for prop in btn.FloatVectorProps:
                if prop.space == 'Dialog':
                    col.prop(eval(prop.address), 'prop', text= prop.pname)
                    empty = False
            if len(btn.FloatVectorProps):
                col = layout.column(align= True)

            for prop in btn.BoolVectorProps:
                if prop.space == 'Dialog':
                    col.prop(eval(prop.address), 'prop', text= prop.pname)
                    empty = False

            if empty:
                col.label(text= "No Properties")
        
    def invoke(self, context, event):
        notempty = False
        b_stb = context.scene.b_stb
        p_stb = context.preferences.addons[__name__].preferences
        if len(b_stb):
            btn = b_stb[p_stb['SelectedButton']]
            for prop in btn.StringProps:
                if prop.space == 'Dialog':
                    notempty = True
                    break
            if notempty:
                return context.window_manager.invoke_props_dialog(self)
            for prop in btn.IntProps:
                if prop.space == 'Dialog':
                    notempty = True
                    break
            if notempty:
                return context.window_manager.invoke_props_dialog(self)
            for prop in btn.FloatProps:
                if prop.space == 'Dialog':
                    notempty = True
                    break
            if notempty:
                return context.window_manager.invoke_props_dialog(self)
            for prop in btn.BoolProps:
                if prop.space == 'Dialog':
                    notempty = True
                    break
            if notempty:
                return context.window_manager.invoke_props_dialog(self)
            for prop in btn.EnumProps:
                if prop.space == 'Dialog':
                    notempty = True
                    break
            if notempty:
                return context.window_manager.invoke_props_dialog(self)
            for prop in btn.IntVectorProps:
                if prop.space == 'Dialog':
                    notempty = True
                    break
            if notempty:
                return context.window_manager.invoke_props_dialog(self)
            for prop in btn.FloatVectorProps:
                if prop.space == 'Dialog':
                    notempty = True
                    break
            if notempty:
                return context.window_manager.invoke_props_dialog(self)
            for prop in btn.BoolVectorProps:
                if prop.space == 'Dialog':
                    empty = False
                    break
            if notempty:
                return context.window_manager.invoke_props_dialog(self)
            else:
                return self.execute(context)

classes.append(STB_OT_ScriptButton)

class STB_OT_RemoveButton(bpy.types.Operator):
    bl_idname = "stb.removebutton"
    bl_label = "Remove"
    bl_description = "Delete the selected Button"
    bl_options = {"REGISTER", "UNDO"}

    deleteFile : BoolProperty(default= True, name= "Delete File", description= "Deletes the saved .py in the Storage")
    deleteText : BoolProperty(default= True, name= "Delete Text", description= "Deletes the linked Text in the Texteditor")

    def execute(self, context):
        p_stb = context.preferences.addons[__name__].preferences
        imfc.RemoveButton(p_stb, self.deleteFile, self.deleteText)
        bpy.context.area.tag_redraw()
        p_stb.SelectedButton # Update this Enum
        return {"FINISHED"}

    def draw(self, context):
        layout = self.layout
        layout.prop(self, 'deleteFile', text= "Delete File")
        layout.prop(self, 'deleteText', text= "Delete Text")

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)
classes.append(STB_OT_RemoveButton)


class TextsProperty(PropertyGroup):
    txt_name: StringProperty()
    select: BoolProperty(default= False)
classes.append(TextsProperty)

class STB_OT_Load(bpy.types.Operator):
    bl_idname = "stb.load"
    bl_label = "Load"
    bl_description = "Load all Buttons from File or Texteditor"
    bl_options = {"REGISTER", "UNDO"}

    Mode: EnumProperty(name= "Load from ", items=[("file", "Load from Disk", ""), ("texteditor", "Load from Texteditor", "")], description= "Change the Mode which to load")
    All: BoolProperty(name= "Load all", default= False, description= "Load all Buttons from the Texteditor")
    Texts: CollectionProperty(type= TextsProperty, name= "Texts in Texteditor")

    def execute(self, context):
        p_stb = context.preferences.addons[__name__].preferences
        if self.Mode == "file":
            btnFails = imfc.Load()
        elif self.Mode == "texteditor":
            btnFails = imfc.LoadFromTexteditor(self, p_stb)
        mes = "\n"
        for name, Fails in zip(btnFails[0], btnFails[1]):
            if len(Fails[0]) or len(Fails[1]):
                mes += "\n %s:" %name
                mes += imfc.CreatFailmessage(Fails)
        if mes != "\n":
            self.report({'ERROR'}, "Not all Areas or Properties could be added because the Syntax is invailid: %s" % mes)
        bpy.context.area.tag_redraw()
        p_stb.SelectedButton # Update this Enum
        return {"FINISHED"}

    def draw(self, context):
        layout = self.layout
        layout.prop(self, 'Mode', expand= True)
        if self.Mode == "file":
            # File -------------------------------------------
            box = layout.box()
            col = box.column()
            col.scale_y = 0.8
            col.label(text= "It will delete all your current Buttons", icon= "INFO")
            col.label(text= "and replace it with the Buttons from the Disk", icon= "BLANK1")
        else:
            # Texteditor -------------------------------------
            box = layout.box()
            box.prop(self, 'All', text= "Load All", toggle= True)
            if self.All:
                for txt in self.Texts:
                    box.label(text= txt.txt_name, icon= 'CHECKBOX_HLT')
            else:
                for txt in self.Texts:
                    box.prop(txt, 'select', text= txt.txt_name)

    def invoke(self, context, event):
        self.Texts.clear()
        for txt in bpy.data.texts:
            new = self.Texts.add()
            new.txt_name = txt.name
        return context.window_manager.invoke_props_dialog(self)
classes.append(STB_OT_Load)

class STB_OT_Reload(bpy.types.Operator):
    bl_idname = "stb.reload"
    bl_label = "Reload"
    bl_description = "Reload the linked Text in the Texteditor of the selected Button"
    bl_options = {"REGISTER"}

    def execute(self, context):
        p_stb = context.preferences.addons[__name__].preferences
        b_stb = context.scene.b_stb
        txt_index = bpy.data.texts.find(p_stb.SelectedButton)
        if txt_index != -1:
            if p_stb.Autosave:
                imfc.SaveText(bpy.data.texts[txt_index], p_stb.SelectedButton)
            Fails = imfc.ReloadButtonText(b_stb[p_stb.SelectedButton], bpy.data.texts[txt_index].as_string())
            if len(Fails[0]) or len(Fails[1]):
                self.report({'ERROR'}, "Not all Areas or Properties could be added because the Syntax is invailid: %s" % imfc.CreatFailmessage(Fails))
        else:
            self.report({'ERROR'}, p_stb.SelectedButton + " could not be reloaded, linked Text in Texteditor don't exist.\n\nINFO: The linked Text must have the same name as the Button")
        bpy.context.area.tag_redraw()
        return {"FINISHED"}
classes.append(STB_OT_Reload)

class STB_OT_Save(bpy.types.Operator):
    bl_idname = "stb.save"
    bl_label = "Save"
    bl_description = "Save all buttons to the Storage"

    def execute(self, context):
        for btn in context.scene.b_stb:
            imfc.Save(bpy.data.texts[btn.name], btn.btn_name)
        return {"FINISHED"}
classes.append(STB_OT_Save)

def get_filename_ext(self):
    if self.Mode == "zip":
        return ".zip"
    else:
        return "."

def get_use_filter_folder(self):
    return self.Mode == "py"

class STB_OT_Export(bpy.types.Operator, ExportHelper):
    bl_idname = "stb.export"
    bl_label = "Export"
    bl_description = "Export the selected Buttons"

    All : BoolProperty(name= "All", description= "Export all Buttons")
    Mode : EnumProperty(name= "Mode", items= [("py", "Export as .py Files", ""), ("zip", "Export as .zip File", "")])

    filter_glob: StringProperty( default='*.zip', options={'HIDDEN'})
    filename_ext : StringProperty(default= ".", get= get_filename_ext)
    use_filter_folder : BoolProperty(default= True, get= get_use_filter_folder)
    filepath : StringProperty(name= "File Path", maxlen= 1024, default= "")

    def execute(self, context):
        p_stb = context.preferences.addons[__name__].preferences
        if self.Mode == "py":
            if not os.path.isdir(self.filepath):
                self.report({'ERROR'}, "The given filepath is not a dirctory")
                return {'CANCELLED'}
        else:
            if not self.filepath.endswith(".zip"):
                self.report({'ERROR'}, "The given filepath is not a .zip file")
                return {'CANCELLED'}
        imfc.Export(self.Mode, p_stb.MultiButtonSelection, p_stb, context, self.filepath)
        return {"FINISHED"}
    
    def draw(self, context):
        p_stb = context.preferences.addons[__name__].preferences
        layout = self.layout
        layout.prop(self, 'Mode', expand= True)
        box = layout.box()
        box.prop(self, 'All')
        for btn in p_stb.MultiButtonSelection:
            if self.All:
                box.label(text= btn.btn_name, icon= 'CHECKBOX_HLT')
            else:
                box.prop(btn, 'selected', text= btn.btn_name)

    def invoke(self, context, invoke):
        p_stb = context.preferences.addons[__name__].preferences
        p_stb.MultiButtonSelection.clear()
        for btn in context.scene.b_stb:
            new = p_stb.MultiButtonSelection.add()
            new.name = btn.name
            new.btn_name = btn.btn_name
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}
classes.append(STB_OT_Export)

class STB_OT_Import(bpy.types.Operator, ImportHelper):
    bl_idname = "stb.import"
    bl_label = "Import"
    bl_description = "Import the seleceted Files"

    filter_glob: StringProperty( default='*.zip;*.py', options={'HIDDEN'} )
    files : CollectionProperty(type= PropertyGroup)

    def execute(self, context):
        p_stb = context.preferences.addons[__name__].preferences
        notaddedfile = []
        btnFails = ([],[])
        directory = os.path.dirname(self.filepath)
        for filep in self.files:
            if filep.name.endswith(".zip"):
                zipfails = imfc.ImportZip(os.path.join(directory, filep.name), context, p_stb)
                btnFails[0].extend(zipfails[0])
                btnFails[1].extend(zipfails[1])
            elif filep.name.endswith(".py"):
                pyfail = imfc.ImportPy(os.path.join(directory, filep.name), context, p_stb)
                btnFails[0].extend(pyfail[0])
                btnFails[1].append(pyfail[1])
            else:
                notaddedfile.append(filep)
        mes = "Not all Files could be added:\n"
        for notf in notaddedfile:
            mes += notf + "\n"
        mesFail = "Not all Areas or Properties could be added because the Syntax is invailid:\n"
        for name, Fails in zip(btnFails[0], btnFails[1]) :
            if len(Fails[0]) or len(Fails[1]):
                mesFail += "\n %s:" %name
                mesFail += imfc.CreatFailmessage(Fails)
        if mes != "Not all Files could be added:\n" and mesFail != "Not all Areas or Properties could be added because the Syntax is invailid:\n":
            self.report({'ERROR'}, mes + "\n\n" + mesFail)
        elif mes != "Not all Files could be added:\n":
            self.report({'ERROR'}, mes)
        elif mesFail != "Not all Areas or Properties could be added because the Syntax is invailid:\n":
            self.report({'ERROR'}, mesFail)
        return {"FINISHED"}
classes.append(STB_OT_Import)

class SBT_OT_Rename(bpy.types.Operator):
    bl_idname = "stb.rename"
    bl_label = "Rename"
    bl_description = "Rename the seleccted Button"
    bl_options = {"UNDO"}

    Name : StringProperty(name= "Name")

    def execute(self, context):
        p_stb = context.preferences.addons[__name__].preferences
        imfc.Rename(p_stb, self.Name)
        bpy.context.area.tag_redraw()
        p_stb.SelectedButton # Update this Enum
        return {"FINISHED"}
    
    def draw(self ,context):
        layout = self.layout
        layout.prop(self, 'Name', text= "Name")

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)
classes.append(SBT_OT_Rename)

# PropertyGroup ----------------------------------------------
class PropString(PropertyGroup):
    prop: StringProperty(update= imfc.StringPropUpdate)
    space: StringProperty()
    pname: StringProperty()
    linename: StringProperty()
    line: IntProperty()
    position: IntProperty()
classes.append(PropString)

class PropInt(PropertyGroup):
    prop: IntProperty(update= imfc.IntPropUpdate)
    space: StringProperty()
    pname: StringProperty()
    linename: StringProperty()
    line: IntProperty()
    position: IntProperty()
classes.append(PropInt)

class PropFloat(PropertyGroup):
    prop: FloatProperty(update= imfc.FloatPropUpdate)
    space: StringProperty()
    pname: StringProperty()
    linename: StringProperty()
    line: IntProperty()
    position: IntProperty()
classes.append(PropFloat)

class PropBool(PropertyGroup):
    prop: BoolProperty(update= imfc.BoolPropUpdate)
    space: StringProperty()
    pname: StringProperty()
    linename: StringProperty()
    line: IntProperty()
    position: IntProperty()
classes.append(PropBool)

class EnumItem(PropertyGroup):
    item : StringProperty()
classes.append(EnumItem)

def e_items(self, context):
    return imfc.ListToEnumitems([item.item for item in self.items])

class PropEnum(PropertyGroup):
    prop: EnumProperty(items=e_items, update= imfc.EnumPropUpdate)
    space: StringProperty()
    pname: StringProperty()
    linename: StringProperty()
    line: IntProperty()
    position: IntProperty()
    items : CollectionProperty(type= EnumItem)
classes.append(PropEnum)

class PropIntVector(PropertyGroup):
    address: StringProperty()
    space: StringProperty()
    pname: StringProperty()
    linename: StringProperty()
    line: IntProperty()
    position: IntProperty()
classes.append(PropIntVector)

class PropFloatVector(PropertyGroup):
    address: StringProperty()
    space: StringProperty()
    pname: StringProperty()
    linename: StringProperty()
    line: IntProperty()
    position: IntProperty()
classes.append(PropFloatVector)

class PropBoolVector(PropertyGroup):
    address: StringProperty()
    space: StringProperty()
    pname: StringProperty()
    linename: StringProperty()
    line: IntProperty()
    position: IntProperty()
classes.append(PropBoolVector)

class ButtonArea(PropertyGroup):
    area: StringProperty()
classes.append(ButtonArea)

class ButtonPropertys(PropertyGroup):
    btn_name: StringProperty()
    StringProps: CollectionProperty(type=PropString)
    IntProps: CollectionProperty(type=PropInt)
    FloatProps: CollectionProperty(type=PropFloat)
    BoolProps: CollectionProperty(type=PropBool)
    EnumProps: CollectionProperty(type=PropEnum)
    IntVectorProps: CollectionProperty(type=PropIntVector)
    FloatVectorProps: CollectionProperty(type=PropFloatVector)
    BoolVectorProps: CollectionProperty(type=PropBoolVector)
    Areas: CollectionProperty(type= ButtonArea)
classes.append(ButtonPropertys)

class ButtonSelection(PropertyGroup):
    selected : BoolProperty()
    btn_name : StringProperty()
classes.append(ButtonSelection)

Icurrentselected = [None]
Ilastselected = [0]
def Radiobutton(self, context):
    p_stb = context.preferences.addons[__name__].preferences
    if self.selected and self.Index != Icurrentselected[0]:
        Icurrentselected[0] = self.Index
        if Ilastselected[0] != self.Index:
            p_stb.SelctedButtonEnum[Ilastselected[0]].selected = False
        p_stb['SelectedButton'] = self.Index
        Ilastselected[0] = self.Index
    elif not self.selected and self.Index == Ilastselected[0] and self.Index == Icurrentselected[0]:
        self.selected = True

class ButtonEnum(PropertyGroup):
    Index : IntProperty()
    selected : BoolProperty(update=Radiobutton)
classes.append(ButtonEnum)

def textlist(self, context):
    l = []
    for i in bpy.data.texts:
        st1 = i.name
        st2 = i.name
        st3 = ""
        l.append((st1,st2,st3))
    return l

def buttonlist(self, context):
    print(imfc.GetAllButtonnames())
    return imfc.ListToEnumitems(imfc.GetAllButtonnames())

class STB_Properties(AddonPreferences):
    bl_idname = __name__

    ButtonName: StringProperty(name="Name", description="Set the name of the Button", default="")
    TextsList: EnumProperty(name="Text", description="Chose a Text to convert into a Button", items=textlist)
    Autosave: BoolProperty(name="Autosave", description="Save your changes automatically to the files", default=True)

    SelctedButtonEnum : CollectionProperty(type=ButtonEnum)
    SelectedButton: EnumProperty(items=buttonlist, name="INTERNAL")
    SelectedEnum: IntProperty(name="INTERNAL")
    MultiButtonSelection : CollectionProperty(type= ButtonSelection)

    def draw(self, context):
        layout = self.layout
        layout.prop(self, 'Autosave')
classes.append(STB_Properties)

# Registration ================================================================================================
for spaceType in SpaceTypes:
    panelfactory(spaceType)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.b_stb = CollectionProperty(type=ButtonPropertys)
    bpy.app.handlers.depsgraph_update_pre.append(LoadSaves)
    bpy.app.timers.register(LoadSaves, first_interval = 3)

def unregister():
    for ele in bpy.context.scene.b_stb:
        for intvec in ele.IntVectorProps:
            exec("del bpy.types.Scene.%s" % intvec.address.split(".")[-1])
        for floatvec in ele.FloatVectorProps:
            exec("del bpy.types.Scene.%s" % floatvec.address.split(".")[-1])
        for boolvec in ele.BoolVectorProps:
            exec("del bpy.types.Scene.%s" % boolvec.address.split(".")[-1])
    del bpy.types.Scene.b_stb
    try:
        bpy.app.handlers.depsgraph_update_pre.remove(LoadSaves)
    except:
        pass
    for cls in classes:
        bpy.utils.unregister_class(cls)