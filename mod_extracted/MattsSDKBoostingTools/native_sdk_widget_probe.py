"""Opt-in detached final-widget research for Steam 25372571.

The SDK owns and releases the reflected widget. A native default owner runs
the original final consumer on a local model reference. No widget is attached
to the player's UI. This is not a player/loadout-context API.
"""
import ctypes as C
import struct
from .native_card_widget_read import read_widget

WIDGET_GATES=(
    (0x58CF8C4,0x58CF9AF,'ab40f436d65c9c3a2f61b79ead977c106d6d84e7fee392e8ef933aea2d8f2518'),
    (0xE95040,0xE951C2,'83cf31d4221c0c77bbff7daa6094fea31a557c7e225fe3c6db1643d447025b7a'),
    (0x11FC6BA,0x120184B,'fb86d5e63e7e052c5badaf1a09fdbbfcb8ed45faa37e9fa743ccf5b3cd7f10c9'),
    (0x575204C,0x5752072,'482279190c6ac5458d1017137810a2670fc207e692424eacbe5dff91ba0834cb'),
    (0x5752072,0x57520E4,'9a07ffab4f3eac413527b7553cefbea1289bd8a66c69f60c67e1fabe6669ec10'),
    (0x10F1BC6,0x10F2083,'9467c955bf42c217ba7a0acd98172b808f16bc9bc4d6d15b6bad168d67848601'),
    (0x167376E,0x1673F0E,'f464d4f455549b0f4859241a0696f1252abe11e550aa91f81b020b512b2b098c'),
    (0x10C71FE,0x10C7B09,'1bf67fc5592bd2e68edfc04a7ccbeaf3cee430cb47d89c443ea069bff2817156'),
    (0x16193F4,0x1619A12,'e1852cd6457b393abbb2051ebf026a303ae1a2747cba3913639b544d02339f2e'),
)


def project_default_widget(native, model, stage):
    """Caller must verify WIDGET_GATES, game thread/profile and solo context."""
    import unrealsdk
    owner_storage=C.create_string_buffer(0x3b0)
    owner=C.addressof(owner_storage)
    context=C.create_string_buffer(0x20)
    C.memmove(C.addressof(context)+0x10,struct.pack('<Q',model),8)
    if owner%16:raise RuntimeError('Widget owner storage alignment differs')
    guard=b'MSBT-owner-guard'
    C.memmove(owner+0x398,guard,len(guard))
    constructor=C.CFUNCTYPE(C.c_void_p,C.c_void_p)(native.base+0x58CF8C4)
    initialize=C.CFUNCTYPE(None,C.c_void_p,C.c_void_p)(native.base+0x167376E)
    consume=C.CFUNCTYPE(None,C.c_void_p,C.c_void_p,C.c_void_p)(native.base+0x11FC6BA)
    destroy=C.CFUNCTYPE(C.c_void_p,C.c_void_p,C.c_uint32)(native.base+0x575204C)
    text_string=C.CFUNCTYPE(C.c_void_p,C.c_void_p)(native.base+0x479623A)
    widget=None
    owner_ready=False
    try:
        widget=unrealsdk.make_struct('OakWidgetData_ItemCard')
        if widget._type.PropertySize!=0x608:
            raise RuntimeError('Native widget reflected size changed')
        pointer=widget._get_address()
        if native.read(pointer,0x608)!=bytes(0x608):
            raise RuntimeError('SDK widget initialization changed')
        fields=[]
        for prop in widget._type._properties():
            field=dict(name=str(prop.Name),type=type(prop).__name__,Offset_Internal=str(prop.Offset_Internal))
            if field['type']=='ZStructProperty':field['Struct']=str(prop.Struct)
            fields.append(field)
        stage('widget_owner_construct_begin')
        constructor(owner)
        owner_ready=True
        if native.u64(owner)!=native.base+0xB9B7700:
            raise RuntimeError('Unexpected native default owner')
        stage('widget_owner_initialize_begin')
        initialize(owner,None)  # Original type/skill-tree maps; no attached UI.
        stage('widget_owner_initialize_complete')
        stage('widget_consume_begin')
        consume(owner,pointer,C.addressof(context))
        if native.read(owner+0x398,len(guard))!=guard:
            raise RuntimeError('Widget owner allocation guard changed')
        result=read_widget(pointer,native.read,fields,
            lambda at:text_string(at) if native.u64(at) else None)
        stage('widget_export_complete')
        return result
    finally:
        try:
            if owner_ready:
                stage('widget_owner_destroy_begin')
                destroy(owner,0)  # Inner fields only; Python owns outer storage.
                stage('widget_owner_destroy_complete')
        finally:
            if widget is not None:
                del widget  # SDK WrappedStruct owns reflected field destruction.
                stage('widget_sdk_release_complete')
