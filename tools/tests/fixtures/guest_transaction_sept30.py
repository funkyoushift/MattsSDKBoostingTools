# Preserved transaction function from the successful September 30 guest trial.
# No game imports or execution here; test supplies detached-memory doubles.
def transaction(pc,identity_address=None,handle=None,send=True):
 params=WrappedStruct(pc.ExecuteInventoryTransactionOnServer.func);t=params.Transaction;a=t._get_address();assert a%16==0
 initialize(a)
 try:
  name=WrappedStruct(pc.StructuredInteractableUserState.ClientSetCurrentInteractable.func,InteractionName='Backpack')
  prop=name._type._find_prop('InteractionName');assert prop.ElementSize==8
  if handle is None:
   t.TargetContainerOwner=pc;C.memmove(a+0x130,name._get_address()+prop.Offset_Internal,8)
   copy_identity(a+0x50,identity_address);C.c_uint8.from_address(a).value=15
   C.c_uint32.from_address(a+0x164).value=8 # Native op15 overflow flag, same as direct insertion.
   C.c_uint32.from_address(a+0x16c).value=1
  else:
   t.SourceContainerOwner=pc;C.memmove(a+0x128,name._get_address()+prop.Offset_Internal,8)
   C.c_int32.from_address(a+4).value=handle;C.c_uint8.from_address(a).value=6
   C.c_uint32.from_address(a+0x164).value=1;C.c_uint32.from_address(a+0x168).value=1
  assert validate(a),'Transaction rejected'
  if send:invoke(pc._get_address(),pc.ExecuteInventoryTransactionOnServer.func._get_address(),a)
 finally:destroy(None,a);C.memset(a,0,376)
