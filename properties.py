import bpy
from bpy.types import PropertyGroup
from bpy.props import (
    StringProperty, IntProperty, FloatProperty, BoolProperty, EnumProperty, CollectionProperty,
    PointerProperty
)
from .functions import update_text
from . import functions

classes = []


class STB_property:
    space: StringProperty()
    linename: StringProperty()
    line: IntProperty()
    sort: StringProperty()


class STB_property_string(STB_property, PropertyGroup):

    def update_prop(self, context):
        txt = self.prop.replace('"', '\\"').replace("'", "\\'")
        update_text(
            self.line,
            self.linename,
            '"%s"' % txt,
            eval("context.scene.%s" % self.path_from_id().split(".")[0])
        )

    prop: StringProperty(update=update_prop)


class STB_property_int(STB_property, PropertyGroup):
    def update_prop(self, context):
        update_text(
            self.line,
            self.linename,
            self.prop,
            eval("context.scene.%s" % self.path_from_id().split(".")[0])
        )

    prop: IntProperty(update=update_prop)


class STB_property_float(STB_property, PropertyGroup):
    def update_prop(self, context):
        update_text(
            self.line,
            self.linename,
            self.prop,
            eval("context.scene.%s" % self.path_from_id().split(".")[0])
        )

    prop: FloatProperty(update=update_prop)


class STB_property_bool(STB_property, PropertyGroup):
    def update_prop(self, context):
        update_text(
            self.line,
            self.linename,
            self.prop,
            eval("context.scene.%s" % self.path_from_id().split(".")[0])
        )

    prop: BoolProperty(update=update_prop)


class STB_enum_item(PropertyGroup):
    item: StringProperty()


class STB_property_enum(STB_property, PropertyGroup):

    def prop_items(self, context):
        return functions.list_to_enum_items([item.item for item in self.items])

    def update_prop(self, context):
        update_text(
            self.line,
            self.linename,
            [self.prop, [item.item for item in self.items]],
            eval("context.scene.%s" % self.path_from_id().split(".")[0])
        )

    prop: EnumProperty(items=prop_items, update=update_prop)
    items: CollectionProperty(type=STB_enum_item)


class STB_vector_property(STB_property, PropertyGroup):
    address: StringProperty()


class STB_enum_property(PropertyGroup):
    def prop_items(self, context):
        return functions.list_to_enum_items([item.item for item in self.items])

    def prop_update(self, context):
        split = self.path_from_id().split(".")
        if len(split) > 1:
            prop = eval("context.scene.%s" % ".".join(split[:2]))
        else:
            prop = eval(self.address)
        update_text(
            prop.line,
            prop.linename,
            [functions.type_getter(ele, ele.ptype) for ele in prop.prop],
            eval("context.scene.%s" % self.path_from_id().split(".")[0])
        )

    prop: EnumProperty(items=prop_items, update=prop_update)
    items: CollectionProperty(type=STB_enum_item)


class STB_property_list_item(PropertyGroup):

    def update_prop(self, context):
        split = self.path_from_id().split(".")
        if len(split) > 1:
            prop = eval("bpy.context.scene." + ".".join(split[:2]))
        else:
            prop = eval(self.address)
        update_text(
            prop.line,
            prop.linename,
            [functions.type_getter(ele, ele.ptype) for ele in prop.prop],
            eval("context.scene.%s" % self.path_from_id().split(".")[0])
        )

    str_prop: StringProperty(update=update_prop)
    int_prop: IntProperty(update=update_prop)
    float_prop: FloatProperty(update=update_prop)
    bool_prop: BoolProperty(update=update_prop)
    enum_prop: PointerProperty(type=STB_enum_property)
    intvector_prop: StringProperty()
    floatvector_prop: StringProperty()
    boolvector_prop: StringProperty()
    ptype: StringProperty()


class STB_property_list(STB_property, PropertyGroup):
    prop: CollectionProperty(type=STB_property_list_item)


class STB_property_object(STB_property, PropertyGroup):
    def update_prop(self, context):
        update_text(
            self.line,
            self.linename,
            "bpy.data.objects['%s']" % self.prop if self.prop != '' else "''",
            eval("bpy.context.scene." + self.path_from_id().split(".")[0])
        )
    prop: StringProperty(update=update_prop)


class STB_button_area(PropertyGroup):
    area: StringProperty()


class STB_button_properties(PropertyGroup):

    def get_selected(self) -> bool:
        """
        default Blender property getter

        Returns:
            bool: selection state of the button
        """
        return self.get("selected", False)

    def set_selected(self, value: bool):
        """
        set the button as active, False will not change anything

        Args:
            value (bool): state of button
        """
        scene = bpy.context.scene
        selected_name = scene.get("stb_button.selected_name", "")
        # implementation similar to a UIList (only one selection of all can be active)
        if value:
            scene["stb_button.selected_name"] = self.name
            self['selected'] = value
            button = scene.stb.get(selected_name, None)
            if button:
                button.selected = False
        elif selected_name != self.name:
            self['selected'] = value

    selected: BoolProperty(
        name='Select',
        description='Select this Button',
        get=get_selected,
        set=set_selected
    )
    StringProps: CollectionProperty(type=STB_property_string)
    IntProps: CollectionProperty(type=STB_property_int)
    FloatProps: CollectionProperty(type=STB_property_float)
    BoolProps: CollectionProperty(type=STB_property_bool)
    EnumProps: CollectionProperty(type=STB_property_enum)
    IntVectorProps: CollectionProperty(type=STB_vector_property)
    FloatVectorProps: CollectionProperty(type=STB_vector_property)
    BoolVectorProps: CollectionProperty(type=STB_vector_property)
    ListProps: CollectionProperty(type=STB_property_list)
    ObjectProps: CollectionProperty(type=STB_property_object)
    areas: CollectionProperty(type=STB_button_area)
    panel: StringProperty(default="Button")


class STB_text_property(PropertyGroup):
    name: StringProperty()
    select: BoolProperty(default=False)


class STB_export_button(PropertyGroup):
    def get_use(self) -> bool:
        """
        get state whether the button will be used to export
        with extra check if export_all is active

        Returns:
            bool: button export state
        """
        return self.get("use", True) or self.get('export_all', False)

    def set_use(self, value: bool) -> None:
        """
        set state whether the button will be used to export

        Args:
            value (bool): button export state
        """
        if not self.get('export_all', False):
            self['use'] = value

    use: BoolProperty(
        default=True,
        name="Import Button",
        description="Decide whether to export the button",
        get=get_use,
        set=set_use
    )


class STB_add_property_item(PropertyGroup):
    position: IntProperty()
    line: StringProperty()
    value: StringProperty()
    type: StringProperty()
    
class STB_edit_property_item(PropertyGroup):
    name: StringProperty()
    line: IntProperty()
    linename: StringProperty()
    use_delete: BoolProperty(default=False)


classes = [
    STB_property_string,
    STB_property_int,
    STB_property_float,
    STB_property_bool,
    STB_enum_item,
    STB_property_enum,
    STB_vector_property,
    STB_enum_property,
    STB_property_list_item,
    STB_property_list,
    STB_property_object,
    STB_button_area,
    STB_button_properties,
    STB_text_property,
    STB_export_button,
    STB_add_property_item,
    STB_edit_property_item
]


def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.stb = CollectionProperty(type=STB_button_properties)


def unregister():
    for ele in bpy.context.scene.stb:
        for intvec in ele.IntVectorProps:
            exec("del bpy.types.Scene.%s" % intvec.address.split(".")[-1])
        for floatvec in ele.FloatVectorProps:
            exec("del bpy.types.Scene.%s" % floatvec.address.split(".")[-1])
        for boolvec in ele.BoolVectorProps:
            exec("del bpy.types.Scene.%s" % boolvec.address.split(".")[-1])
    for cls in classes:
        bpy.utils.unregister_class(cls)
    del bpy.types.Scene.stb
