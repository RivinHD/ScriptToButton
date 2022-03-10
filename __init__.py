import bpy
from bpy.props import StringProperty, EnumProperty, PointerProperty, CollectionProperty, BoolProperty, IntProperty, FloatProperty, BoolVectorProperty, IntVectorProperty, FloatVectorProperty
from bpy.types import Operator, Panel, PropertyGroup, AddonPreferences
import os
from bpy.app.handlers import persistent
from . import functions as imfc
from bpy_extras.io_utils import ImportHelper, ExportHelper
from . import update
import traceback
import sys

bl_info = {
    "name": "Script To Button",
    "author": "RivinHD",
    "blender": (3, 0, 1),
    "version": (2, 1, 4),
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
            STB = context.preferences.addons[__name__].preferences
            if STB.AutoUpdate and STB.Update:
                box = layout.box()
                box.label(text= "A new Version is available (" + STB.Version + ")")
                box.operator(update.STB_OT_Update.bl_idname, text= "Update")
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
                row2.operator(STB_OT_LoadSingelButton.bl_idname, text="", icon= 'TEXT')
                row2.operator(STB_OT_Reload.bl_idname, text= "", icon= 'FILE_REFRESH')
                row2.operator(SBT_OT_Rename.bl_idname, text= "", icon= 'GREASEPENCIL')
            else:
                row = col.row(align= True)
                row.operator(STB_OT_Load.bl_idname, text= "Load")
                row.operator(STB_OT_Save.bl_idname, text= "Save")
                row = col.row(align= True)
                row.operator(STB_OT_LoadSingelButton.bl_idname, text= "Load Button", icon= 'TEXT')
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
                area = bpy.context.area.ui_type
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
                sort, back = imfc.SortProps(btn, 'Panel')
                if len(sort) > 0 or len(back) > 0:
                    imfc.drawSort(sort, back, layout)
                else :
                    layout.label(text= "No Properties")
    STB_PT_Properties.__name__ = "STB_PT_Properties_%s" %spaceType
    classes.append(STB_PT_Properties)

#region Operators
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
                if len(bpy.data.texts):
                    col.prop(p_stb, 'TextsList')
                else:
                    col.label(text= "No Text available", icon= "ERROR")
classes.append(STB_OT_AddButton)

class STB_OT_ScriptButton(bpy.types.Operator):
    bl_idname = "stb.scriptbutton"
    bl_label = "ScriptButton"
    bl_options = {"UNDO","INTERNAL"}

    btn_name: StringProperty()

    def execute(self, context):
        p_stb = context.preferences.addons[__name__].preferences
        b_stb = context.scene.b_stb
        if bpy.data.texts.find(self.btn_name) == -1:
            imfc.GetText(self.btn_name)
            imfc.UpdateAllProps(b_stb[self.btn_name])
        text = bpy.data.texts[self.btn_name]
        try:
            exec(compile(text.as_string(), text.name, 'exec'))
            if p_stb.DelteScriptAfterRun:
                bpy.data.texts.remove(text)
        except Exception:
            if p_stb.DelteScriptAfterRun:
                bpy.data.texts.remove(text)
            error = traceback.format_exception(*sys.exc_info())
            error.pop(1)
            error = "".join(error)
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
            sort, back = imfc.SortProps(btn, 'Dialog')
            if len(sort) > 0 or len(back) > 0:
                imfc.drawSort(sort, back, layout)
            else :
                layout.label(text= "No Properties")
        
    def invoke(self, context, event):
        notempty = False
        b_stb = context.scene.b_stb
        p_stb = context.preferences.addons[__name__].preferences
        if len(b_stb):
            btn = b_stb[self.btn_name]
            sort, back = imfc.SortProps(btn, 'Dialog')
            if len(sort) > 0 or len(back) > 0:
                return bpy.context.window_manager.invoke_props_dialog(self)
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
        p_stb = context.preferences.addons[__name__].preferences
        layout = self.layout
        layout.prop(self, 'deleteFile', text= "Delete File")
        row = layout.row()
        textenabled = bpy.data.texts.find(p_stb.SelectedButton) != -1
        row.enabled = textenabled
        self.deleteText = textenabled
        row.prop(self, 'deleteText', text= "Delete Text", toggle= False)

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
        Fails = []
        for btn in context.scene.b_stb:
            if bpy.data.texts.find(btn.name) != -1:
                imfc.Save(bpy.data.texts[btn.name], btn.btn_name)
            else:
                Fails.append(btn.name)
        if len(Fails) > 0:
            errtext = "Not all Scrpits could be saved:"
            for fail in Fails:
                errtext += "\n" + fail + " could not be saved, linked Text is missing"
            self.report({'ERROR'}, errtext)
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
                self.filepath = os.path.dirname(self.filepath)
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
        bpy.context.area.tag_redraw()
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

class STB_OT_LoadSingelButton(bpy.types.Operator):
    bl_idname = "stb.loadsingelbutton"
    bl_label = "Load Button"
    bl_description = "Load the script of the selected Button into the Texteditor"

    def execute(self, context):
        p_stb = context.preferences.addons[__name__].preferences
        b_stb = context.scene.b_stb
        imfc.GetText(p_stb.SelectedButton)
        imfc.UpdateAllProps(b_stb[p_stb.SelectedButton])
        return {"FINISHED"}
classes.append(STB_OT_LoadSingelButton)

#endregion

#region PropertyGroups
class PropString(PropertyGroup):
    prop: StringProperty(update= imfc.StringPropUpdate)
    space: StringProperty()
    pname: StringProperty()
    linename: StringProperty()
    line: IntProperty()
    sort: StringProperty()
classes.append(PropString)

class PropInt(PropertyGroup):
    prop: IntProperty(update= imfc.IntPropUpdate)
    space: StringProperty()
    pname: StringProperty()
    linename: StringProperty()
    line: IntProperty()
    sort: StringProperty()
classes.append(PropInt)

class PropFloat(PropertyGroup):
    prop: FloatProperty(update= imfc.FloatPropUpdate)
    space: StringProperty()
    pname: StringProperty()
    linename: StringProperty()
    line: IntProperty()
    sort: StringProperty()
classes.append(PropFloat)

class PropBool(PropertyGroup):
    prop: BoolProperty(update= imfc.BoolPropUpdate)
    space: StringProperty()
    pname: StringProperty()
    linename: StringProperty()
    line: IntProperty()
    sort: StringProperty()
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
    items : CollectionProperty(type= EnumItem)
    sort: StringProperty()
classes.append(PropEnum)

class PropIntVector(PropertyGroup):
    address: StringProperty()
    space: StringProperty()
    pname: StringProperty()
    linename: StringProperty()
    line: IntProperty()
    sort: StringProperty()
classes.append(PropIntVector)

class PropFloatVector(PropertyGroup):
    address: StringProperty()
    space: StringProperty()
    pname: StringProperty()
    linename: StringProperty()
    line: IntProperty()
    sort: StringProperty()
classes.append(PropFloatVector)

class PropBoolVector(PropertyGroup):
    address: StringProperty()
    space: StringProperty()
    pname: StringProperty()
    linename: StringProperty()
    line: IntProperty()
    sort: StringProperty()
classes.append(PropBoolVector)

class EnumProp(PropertyGroup):
    prop : EnumProperty(items= e_items, update= imfc.ListPropUpdate)
    items : CollectionProperty(type= EnumItem)
classes.append(EnumProp)

class PropListProp(PropertyGroup):
    strprop: StringProperty(update= imfc.ListPropUpdate)
    intprop: IntProperty(update= imfc.ListPropUpdate)
    floatprop: FloatProperty(update= imfc.ListPropUpdate)
    boolprop: BoolProperty(update= imfc.ListPropUpdate)
    enumprop: PointerProperty(type= EnumProp)
    intvectorprop: StringProperty()
    floatvectorprop: StringProperty()
    boolvectorprop: StringProperty()
    ptype: StringProperty()
classes.append(PropListProp)

class PropList(PropertyGroup):
    prop: CollectionProperty(type= PropListProp)
    space: StringProperty()
    pname: StringProperty()
    linename: StringProperty()
    line: IntProperty()
    sort: StringProperty()
classes.append(PropList)

class PropObject(PropertyGroup):
    prop: StringProperty(update= imfc.ObjectPropUpdate)
    space: StringProperty()
    pname: StringProperty()
    linename: StringProperty()
    line: IntProperty()
    sort: StringProperty()
classes.append(PropObject)

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
    ListProps: CollectionProperty(type= PropList)
    ObjectProps: CollectionProperty(type= PropObject)
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
#endregion

def textlist(self, context):
    return [(i.name, i.name, "") for i in bpy.data.texts]

def buttonlist(self, context):
    return imfc.ListToEnumitems(imfc.GetAllButtonnames())

class STB_Properties(AddonPreferences):
    bl_idname = __name__

    ButtonName : StringProperty(name="Name", description="Set the name of the Button", default="")
    TextsList : EnumProperty(name="Text", description="Chose a Text to convert into a Button", items=textlist)
    Autosave : BoolProperty(name="Autosave", description="Save your changes automatically to the files", default=True)
    AutoLoad : BoolProperty(name= "Load to Texteditor", description= "Load the script into the Texteditor on start, on add or on manuel load", default= False)
    DelteScriptAfterRun : BoolProperty(name= "Delete Script after Run", description= "Delete the script in the Editor after the linked Scriptbutton was pressed", default= True)

    SelctedButtonEnum : CollectionProperty(type=ButtonEnum)
    SelectedButton : EnumProperty(items=buttonlist, name="INTERNAL")
    SelectedEnum : IntProperty(name="INTERNAL")
    MultiButtonSelection : CollectionProperty(type= ButtonSelection)

    Update : BoolProperty()
    Version : StringProperty()
    Restart : BoolProperty()
    AutoUpdate : BoolProperty(default= True, name= "Auto Update", description= "automatically search for a new Update")

    def draw(self, context):
        STB = bpy.context.preferences.addons[__name__].preferences
        layout = self.layout
        row = layout.row()
        row.prop(self, 'Autosave')
        row.prop(self, 'AutoLoad')
        row.prop(self, 'DelteScriptAfterRun')
        layout.separator(factor= 0.8)
        col = layout.column()
        col.prop(STB, 'AutoUpdate')
        row = col.row()
        if STB.Update:
            row.operator(update.STB_OT_Update.bl_idname, text= "Update")
            row.operator(update.STB_OT_ReleaseNotes.bl_idname, text= "Release Notes")
        else:
            row.operator(update.STB_OT_CheckUpdate.bl_idname, text= "Check For Updates")
            if STB.Restart:
                row.operator(update.STB_OT_Restart.bl_idname, text= "Restart to Finsih")
        if STB.Version != '':
            if STB.Update:
                col.label(text= "A new Version is available (" + STB.Version + ")")
            else:
                col.label(text= "You are using the latest Vesion (" + STB.Version + ")")
classes.append(STB_Properties)

# region Registration
for spaceType in SpaceTypes:
    panelfactory(spaceType)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    for cls in update.classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.b_stb = CollectionProperty(type=ButtonPropertys)
    bpy.app.handlers.load_post.append(LoadSaves)
    update.register()

def unregister():
    for ele in bpy.context.scene.b_stb:
        for intvec in ele.IntVectorProps:
            exec("del bpy.types.Scene.%s" % intvec.address.split(".")[-1])
        for floatvec in ele.FloatVectorProps:
            exec("del bpy.types.Scene.%s" % floatvec.address.split(".")[-1])
        for boolvec in ele.BoolVectorProps:
            exec("del bpy.types.Scene.%s" % boolvec.address.split(".")[-1])
    del bpy.types.Scene.b_stb
    update.unregister()
    for cls in classes:
        bpy.utils.unregister_class(cls)
    for cls in update.classes:
        bpy.utils.unregister_class(cls)

#endregion