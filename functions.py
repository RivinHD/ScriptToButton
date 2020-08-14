import os
import time
import bpy
import sys
import traceback
import zipfile
import threading
from bpy.props import IntVectorProperty, FloatVectorProperty, BoolVectorProperty, PointerProperty, StringProperty
from bpy.types import PropertyGroup

classes = []
NotOneStart = [False]
AllAreas = ["3D_Viewport", "UV_Editor", "Compositor", "Video_Sequencer", "Movie_Clip_Editor", "Dope_Sheet", "Graph_Editor", "Nonlinear_Animation", "Text_Editor"]

def SaveText(ActiveText, ScriptName):
    text = ActiveText.as_string()
    destination = os.path.dirname(os.path.abspath(__file__)) + "/Storage/" + ScriptName + ".py"
    with open(destination, 'w', encoding='utf8') as outfile:
        outfile.write(text)

def GetText(ScriptName):
    destination = os.path.dirname(os.path.abspath(__file__)) + "/Storage/" + ScriptName + ".py"
    if bpy.data.texts.find(ScriptName) == -1:
        bpy.data.texts.new(ScriptName)
    else:
        bpy.data.texts[ScriptName].clear()
    with open(destination, 'r', encoding='utf8') as infile:
        bpy.data.texts[ScriptName].write(infile.read())

def GetAllSavedScripts():
    path = os.path.dirname(os.path.abspath(__file__)) + "/Storage"
    if not os.path.exists(path):
        os.mkdir(path)
    l = []
    for file in os.listdir(path):
        l.append(file.replace(".py",""))
    return l

def Load():
    scene = bpy.context.scene
    scene.b_stb.clear()
    p_stb = bpy.context.preferences.addons[__package__].preferences
    p_stb.SelctedButtonEnum.clear()
    btnFails = ([],[])
    scripts = GetAllSavedScripts()
    for i in range(len(scripts)):
        script = scripts[i]
        new = scene.b_stb.add()
        new.name = script
        new.btn_name = script
        item = p_stb.SelctedButtonEnum.add()
        item.Index = i
        GetText(script)
        btnFails[0].append(script)
        btnFails[1].append(Add_AreasANDProps(new, bpy.data.texts[script].as_string()))
    if len(p_stb.SelctedButtonEnum):
        p_stb.SelctedButtonEnum[0].selected = True
    return btnFails

def GetAllButtonnames():
    l = []
    for btn in bpy.context.scene.b_stb:
        l.append(btn.btn_name)
    return l

def ListToEnumitems(datalist):
    l = []
    for i in range(len(datalist)):
        l.append((datalist[i], datalist[i], "", "", i))
    return l

def GetAreas(text):
    lines = text.splitlines()
    if len(lines):
        if lines[0].strip().startswith("#STB-Area-"):
            areas = lines[0].replace(" ", "").split("///")
            l = []
            for area in areas:
                if area.startswith("#STB-Area-"):
                    l.append(area.split("-")[2])
            return l
        else:
            return AllAreas
    else:
        return []

def AreaParser(stbArea):
    AreaParsDict = {
        "3D_Viewport": "VIEW_3D",
        "UV_Editor": "IMAGE_EDITOR",
        "Image_Editor": "IMAGE_EDITOR",
        "Compositor": "NODE_EDITOR",
        "Texture_Node_Editor": "NODE_EDITOR",
        "Shader_Editor": "NODE_EDITOR",
        "Video_Sequencer": "SEQUENCE_EDITOR",
        "Movie_Clip_Editor": "CLIP_EDITOR",
        "Dope_Sheet": "DOPESHEET_EDITOR",
        "Timeline": "DOPESHEET_EDITOR",
        "Graph_Editor": "GRAPH_EDITOR",
        "Drivers": "GRAPH_EDITOR",
        "Nonlinear_Animation": "NLA_EDITOR",
        "Text_Editor": "TEXT_EDITOR"
    }
    try:
        return AreaParsDict[stbArea]
    except:
        return False # Add to Failstack

def GetProps(text):
    lines = text.splitlines()
    props = []
    for i in range(len(lines)):
        currentline = lines[i]
        if currentline.strip().startswith("#STB-Input-"):
            nextline = lines[i + 1]
            if not nextline.startswith("#"):
                inputs = currentline.replace(" ", "").split("///")
                linename = nextline.split("=")[0]
                valuestring = nextline.split("=")[1].split("#")[0].replace(" ", "")
                for inp in inputs:
                    props.append({
                        "name": linename.strip(),
                        "linename": linename,
                        "space": inp.split("-")[2],
                        "type": inp.split("-")[3],
                        "line": i + 1,
                        "value": valuestring
                    })
    return props

def AddProp(btn, prop):
    try:
        value = eval(prop["value"])
        valuetype = type(value)
        proptype = prop["type"]
        if proptype == 'String': # Check types
            if not valuetype is str:
                return False
        elif proptype == 'Int':
            if not valuetype is int:
                return False
        elif proptype == 'Float':
            if not valuetype is float:
                return False
        elif proptype == 'Bool':
            if not valuetype is bool:
                return False
        elif proptype == 'Enum':
            if not((valuetype is list or valuetype is tuple) and (isinstance(value[1], list) or isinstance(value[1], tuple)) and isinstance(value[0], str) and all(map(lambda x: isinstance(x, str), value[1]))):
                return False
        elif proptype == 'IntVector':
            if not((valuetype is list or valuetype is tuple) and all(map(lambda x: isinstance(x, int), value)) and len(value) <= 32):
                return False
        elif proptype == 'FloatVector':
            if not((valuetype is list or valuetype is tuple) and all(map(lambda x: isinstance(x, float), value)) and len(value) <= 32):
                return False
        elif proptype == 'BoolVector':
            if not((valuetype is list or valuetype is tuple) and all(map(lambda x: isinstance(x, bool), value)) and len(value) <= 32):
                return False
        elif proptype == 'List':
            if not(valuetype is list or valuetype is tuple):
                return False
        elif proptype == 'Object':
            if not (valuetype is str or valuetype is bpy.types.Object):
                return False
        coll = eval("btn." + proptype + "Props.add()") # Add element to the right Propcollection
    except:
        return False # Add to Failstack
    name = prop["name"]
    coll.name = name # parse data
    coll.pname = name
    coll.linename = prop["linename"]
    coll.space = prop["space"]
    coll.line = prop["line"]
    if proptype == 'Enum':
        coll.items.clear()
        for v in value[1]:
            item = coll.items.add()
            item.name = v
            item.item = v
        try:
            coll.prop = value[0]
        except:
            coll.prop = value[1][0]
    elif proptype == 'IntVector' or proptype == 'FloatVector' or proptype == 'BoolVector':
        coll.address = Creat_VectorProp(len(value), (btn.btn_name + "_"+ name + str(coll.line)).replace(" ", ""), proptype, "bpy.context.scene.b_stb['%s'].%sProps['%s']" % (btn.name, proptype, name), proptype)
        exec("%s.prop = value" %coll.address)
    elif proptype == 'List':
        coll.prop.clear()
        for i in value:
            prop = coll.prop.add()
            itype = type(i)
            if itype is list or itype is tuple:
                if (itype is list or itype is tuple) and (isinstance(i[1], list) or isinstance(i[1], tuple)) and isinstance(i[0], str) and all(map(lambda x: isinstance(x, str), i[1])):
                    prop.enumprop.items.clear() #Enum
                    prop.ptype = 'enum'
                    for v in i[1]:
                        item = prop.enumprop.items.add()
                        item.name = v
                        item.item = v
                    try:
                        prop.enumprop.prop = i[0]
                    except:
                        prop.enumprop.prop = i[1][0]
                elif (itype is list or itype is tuple) and all(map(lambda x: isinstance(x, bool), i)) and len(i) <= 32: #BoolVector
                    prop.boolvectorprop = Creat_VectorProp(len(i), (btn.btn_name + "_"+ name + "_list_" + str(len(coll.prop))).replace(" ", ""), "BoolVector", "bpy.context.scene.b_stb['%s'].ListProps['%s']"% (btn.name, name), "List")
                    prop.ptype = 'boolvector'
                    exec("%s.prop = i" %prop.boolvectorprop)
                elif (itype is list or itype is tuple) and all(map(lambda x: isinstance(x, int), i)) and len(i) <= 32: #IntVector
                    prop.intvectorprop = Creat_VectorProp(len(i), (btn.btn_name + "_"+ name + "_list_" + str(len(coll.prop))).replace(" ", ""), "IntVector", "bpy.context.scene.b_stb['%s'].ListProps['%s']"% (btn.name, name), "List")
                    prop.ptype = 'intvector'
                    exec("%s.prop = i" %prop.intvectorprop)
                elif (itype is list or itype is tuple) and all(map(lambda x: isinstance(x, float), i)) and len(i) <= 32: # FloatVector
                    prop.floatvectorprop = Creat_VectorProp(len(i), (btn.btn_name + "_"+ name + "_list_" + str(len(coll.prop))).replace(" ", ""), "FloatVector", "bpy.context.scene.b_stb['%s'].ListProps['%s']"% (btn.name, name), "List")
                    prop.ptype = 'floatvector'
                    exec("%s.prop = i" %prop.floatvectorprop)
                else:
                    prop.strprop = str(i)
                    prop.ptype = 'str'
            else:
                exec("prop." + str(itype.__name__)+ "prop = i")
                prop.ptype = str(itype.__name__)
    elif proptype == 'Object':
        coll.prop = value.name
    else:
        coll.prop = value

def AddButton(p_stb, name, textname):
    texts = bpy.data.texts
    text = texts[textname].as_string() # Get selected Text
    if p_stb.Autosave:
        SaveText(texts[textname], name)
        GetText(name) # do same as lower, but with File
    else:
        if texts.find(textname) == -1: # Creat new text if not exist
            texts.new(textname)
        else:
            texts[textname].clear()
        texts[textname].write(text) # Write to Text
    index = bpy.context.scene.b_stb.find(name)
    if index != -1:
        bpy.context.scene.b_stb.remove(index)   
    new = bpy.context.scene.b_stb.add() # Create new Instance
    new.name = name
    new.btn_name = name
    item = p_stb.SelctedButtonEnum.add()
    item.Index = len(p_stb.SelctedButtonEnum) - 1
    return Add_AreasANDProps(new, text)

def RemoveButton(p_stb, deleteFile, deleteText):
    index = p_stb['SelectedButton']
    b_stb = bpy.context.scene.b_stb
    if deleteFile:
        os.remove(os.path.dirname(__file__) + "/Storage/" + p_stb.SelectedButton + ".py")
    if deleteText:
        bpy.data.texts.remove(bpy.data.texts[p_stb.SelectedButton])
    Delete_VectorProps(b_stb[p_stb.SelectedButton])
    Delet_ListProp(b_stb[p_stb.SelectedButton])
    b_stb.remove(b_stb.find(p_stb.SelectedButton))
    if index - 1 >= 0:
        p_stb.SelctedButtonEnum[index - 1].selected = index >= len(p_stb.SelctedButtonEnum) - 1
    p_stb.SelctedButtonEnum.remove(len(p_stb.SelctedButtonEnum) - 1)
    
def CreatFailmessage(Fails):
    mess = "\n"
    if len(Fails[0]):
        mess += "   Areas: \n"
        for fail in Fails[0]:
            mess += "      Line: 0    #STB-Area-%s \n" %fail
    if len(Fails[1]):
        mess += "   Properties: \n"
        for fail in Fails[1]:
            mfail = "Line: " + str(fail['line']) + "    #STB-Input-" + str(fail['space']) + "-" + str(fail['type'] + "      " + str(fail['value']))
            mess += "      %s \n" %mfail
    return mess

def LoadFromTexteditor(opt, p_stb):
    btnFails = ([],[])
    if opt.All:
        for txt in opt.Texts: # All Texts from Buttons
            btn_index = bpy.context.scene.b_stb.find(txt.txt_name)
            if btn_index != -1:
                btnFails[0].append(txt.txt_name)
                btnFails[1].append(ReloadButtonText(bpy.context.scene.b_stb[btn_index], bpy.data.texts[txt.txt_name].as_string()))
                if p_stb.Autosave:
                    SaveText(bpy.data.texts[txt.txt_name], txt.txt_name)
            else:
                LoadAddButton(p_stb, txt.txt_name)

    else:
        for txt in opt.Texts:
            if txt.select: # selected Texts from Buttons
                btn_index = bpy.context.scene.b_stb.find(txt.txt_name)
                if btn_index != -1:
                    btnFails[0].append(txt.txt_name)
                    btnFails[1].append(ReloadButtonText(bpy.context.scene.b_stb[btn_index], bpy.data.texts[txt.txt_name].as_string()))
                    if p_stb.Autosave:
                        SaveText(bpy.data.texts[txt.txt_name], txt.txt_name)
                else:
                    LoadAddButton(p_stb, txt.txt_name)
    return btnFails
Propdatatyp = ["String", "Int", "Float", "Bool", "Enum", "IntVector", "FloatVector", "BoolVector", "List", "Object"]

def LoadAddButton(p_stb, name):
    p_stb.ButtonName = name
    p_stb.TextsList = name
    end = bpy.ops.stb.addbutton('INVOKE_DEFAULT',ShowSkip=True)

def ReloadButtonText(btn,text):
    Delete_VectorProps(btn)
    Delet_ListProp(btn)
    return Add_AreasANDProps(btn, text)

def Add_AreasANDProps(btn, text):
    btn.Areas.clear() # Clear Area and Prop
    for prop in Propdatatyp:
        eval("btn." + prop + "Props.clear()")

    AreaList = GetAreas(text)# Get Areas
    FaildAreas = []
    for ele in AreaList: # Add Areas
        pars = AreaParser(ele)
        if pars is False:
            FaildAreas.append(ele)
        else:
            new = btn.Areas.add()
            new.name = pars
            new.area = pars
    if len(AreaList) == len(FaildAreas):
        for ele in AllAreas: # Add All Areas, when no writen rea has a vailid Syntax
            pars = AreaParser(ele)
            new = btn.Areas.add()
            new.name = pars
            new.area = pars

    PropListDict = GetProps(text) # Get Props
    FailedProps = []
    for ele in PropListDict: # Add Props
        if AddProp(btn, ele) is False:  
            FailedProps.append(ele)
    return (FaildAreas, FailedProps)

def Creat_VectorProp(vsize, name, vectortyp, backaddress, update):
    class VectorProp(PropertyGroup):
        exec("prop : %sProperty(size= %d, update= %sPropUpdate)" % (vectortyp, vsize, update))
        address : StringProperty(default= backaddress)
    VectorProp.__name__ = "VectorProp_%s_%s" % (vectortyp, name)
    bpy.utils.register_class(VectorProp)
    exec("bpy.types.Scene.stb_%sproperty_%s = PointerProperty(type= VectorProp)" % (vectortyp.lower(), name)) 
    return "bpy.context.scene.stb_%sproperty_%s" %(vectortyp.lower(), name)

def unregister_vector():
    for cls in classes:
        bpy.utils.unregister_class(cls)

def Delete_VectorProps(btn):
    for intvec in btn.IntVectorProps:
        name = intvec.address.split(".")[-1]
        exec("del bpy.types.Scene.%s" % name)
        exec("del bpy.context.scene['%s']" % name)
    for floatvec in btn.FloatVectorProps:
        name = floatvec.address.split(".")[-1]
        exec("del bpy.types.Scene.%s" % name)
        exec("del bpy.context.scene['%s']" % name)
    for boolvec in btn.BoolVectorProps:
        name = boolvec.address.split(".")[-1]
        exec("del bpy.types.Scene.%s" % name)
        exec("del bpy.context.scene['%s']" % name)

def Delet_ListProp(btn):
    for l in btn.ListProps:
        for prop in l.prop:
            if prop.ptype == 'intvector':
                name = prop.intvectorprop.split(".")[-1]
                exec("del bpy.types.Scene.%s" % name)
                exec("del bpy.context.scene['%s']" % name)
            elif prop.ptype == 'floatvector':
                name = prop.floatvectorprop.split(".")[-1]
                exec("del bpy.types.Scene.%s" % name)
                exec("del bpy.context.scene['%s']" % name)
            elif prop.ptype == 'boolvector':
                name = prop.boolvectorprop.split(".")[-1]
                exec("del bpy.types.Scene.%s" % name)
                exec("del bpy.context.scene['%s']" % name)

def StringPropUpdate(self, context):
    txt = self.prop.replace('"', '\\"').replace("'", "\\'")
    UpdateText(self.line, self.linename, '"%s"'% txt, eval("bpy.context.scene." + self.path_from_id().split(".")[0]))

def IntPropUpdate(self, context):
    UpdateText(self.line, self.linename, self.prop, eval("bpy.context.scene." + self.path_from_id().split(".")[0]))

def FloatPropUpdate(self, context):
    UpdateText(self.line, self.linename, self.prop, eval("bpy.context.scene." + self.path_from_id().split(".")[0]))

def BoolPropUpdate(self, context):
    UpdateText(self.line, self.linename, self.prop, eval("bpy.context.scene." + self.path_from_id().split(".")[0]))

def EnumPropUpdate(self, context):
    UpdateText(self.line, self.linename, [self.prop,[item.item for item in self.items]], eval("bpy.context.scene." + self.path_from_id().split(".")[0]))

def IntVectorPropUpdate(self, context):
    Prop = eval(self.address)
    UpdateText(Prop.line, Prop.linename, [ele for ele in self.prop], eval("bpy.context.scene." + Prop.path_from_id().split(".")[0]))

def FloatVectorPropUpdate(self, context):
    Prop = eval(self.address)
    UpdateText(Prop.line, Prop.linename, [ele for ele in self.prop], eval("bpy.context.scene." + Prop.path_from_id().split(".")[0]))

def BoolVectorPropUpdate(self, context):
    Prop = eval(self.address)
    UpdateText(Prop.line, Prop.linename, [ele for ele in self.prop], eval("bpy.context.scene." + Prop.path_from_id().split(".")[0]))

def ListPropUpdate(self, context):
    split = self.path_from_id().split(".")
    if len(split) > 1:
        Prop = eval("bpy.context.scene."  + ".".join(split[:2]))
    else:
        Prop = eval(self.address)
    UpdateText(Prop.line, Prop.linename, [TypeGetter(ele, ele.ptype) for ele in Prop.prop], eval("bpy.context.scene." + Prop.path_from_id().split(".")[0]))

def ObjectPropUpdate(self, context):
    UpdateText(self.line, self.linename, "bpy.data.objects['" +  self.prop + "']" if self.prop != '' else "''" , eval("bpy.context.scene." + self.path_from_id().split(".")[0]))

def UpdateText(linepos, varname, message, btn):
    if NotOneStart[0]:
        text = bpy.data.texts[btn.name]
        text.lines[linepos].body = varname + "= " + str(message)
        txt = text.as_string()
        text.clear()
        text.write(txt)

def TypeGetter(value, vtype):
    if vtype == 'str':
        return value.strprop
    elif vtype == 'int':
        return value.intprop
    elif vtype == 'float':
        return value.floatprop
    elif vtype == 'bool':
        return value.boolprop
    elif vtype == 'enum':
        return [value.enumprop.prop, [item.item for item in value.enumprop.items]]
    elif vtype == 'intvector':
        return [i for i in eval(value.intvectorprop + "['prop']")]
    elif vtype == 'floatvector':
        return [i for i in eval(value.floatvectorprop + "['prop']")]
    elif vtype == 'boolvector':
        return [bool(i) for i in eval(value.boolvectorprop + "['prop']")]

def GetConsoleError():
    lasttb = sys.last_traceback
    if lasttb is None:
        return False
    error = ""
    for tb in traceback.extract_tb(lasttb):
        error += '   File  "' + str(tb.filename) +'", line ' + str(tb.lineno) + ", in " + tb.name +"\n"
    return 'Traceback (most recent call last):\n'+ error + str(sys.last_type.__name__) + ": " + str(sys.last_value)

def Export(mode, selections, p_stb, context, dir_filepath):
    if mode == "py":
        for selc in selections:
            path = os.path.join(dir_filepath, selc.btn_name + ".py")
            with open(path, 'w', encoding='utf8') as pyfile:
                pyfile.write(bpy.data.texts[selc.name].as_string())
    else:
        folderpath = os.path.join(bpy.app.tempdir, "STB_Zip")
        if not os.path.exists(folderpath):
            os.mkdir(folderpath)
        with zipfile.ZipFile(dir_filepath, 'w') as zip_it:
            for selc in selections:
                zip_path = folderpath + "/" + selc.btn_name + ".py"
                with open(zip_path, 'w', encoding='utf8') as recfile:
                    recfile.write(bpy.data.texts[selc.name].as_string())
                zip_it.write(zip_path, selc.btn_name + ".py")
                os.remove(zip_path)
        os.rmdir(folderpath)

def ImportZip(filepath, context, p_stb):
    btnFails = ([],[])
    with zipfile.ZipFile(filepath, 'r') as zip_out:
        filepaths = []
        for i in zip_out.namelist():
            if i.endswith(".py"):
                filepaths.append(i)
        for filep in filepaths:
            txt = str(zip_out.read(filep))
            Fail = ImportButton(filep, context, p_stb, txt)
            btnFails[0].extend(Fail[0])
            btnFails[1].append(Fail[1])
        return btnFails
                
def ImportPy(filepath, context, p_stb):
    with open(filepath, 'r', encoding='utf8') as pyfile:
        txt = pyfile.read()
        return ImportButton(filepath, context, p_stb, txt)

def ImportButton(filepath, context, p_stb, txt):
    name = CheckForDublicates([i.name for i in bpy.data.texts], os.path.splitext(os.path.basename(filepath))[0])
    bpy.data.texts.new(name)
    bpy.data.texts[name].write(txt)
    btn = context.scene.b_stb.add()
    btn.name = name
    btn.btn_name = name
    item = p_stb.SelctedButtonEnum.add()
    item.Index = len(p_stb.SelctedButtonEnum) - 1
    if p_stb.Autosave:
        SaveText(bpy.data.texts[name], name)
    Fails = Add_AreasANDProps(btn, txt)
    return ([name],Fails)

def CheckForDublicates(l, name, num = 1): #Check for name dublicates and appen .001, .002 etc.
    if name in l:
        return CheckForDublicates(l, name.split("_")[0] +"_{0:03d}".format(num), num + 1)
    return name

def Rename(p_stb, name):
    btn = bpy.context.scene.b_stb[p_stb.SelectedButton]
    text = bpy.data.texts[p_stb.SelectedButton]
    os.remove(os.path.dirname(os.path.abspath(__file__)) + "/Storage/" + btn.btn_name + ".py")
    if name != btn.btn_name:
        name = CheckForDublicates(GetAllButtonnames(), name)
    btn.name = name
    btn.btn_name = name
    text.name = name
    if p_stb.Autosave:
        SaveText(text, name)