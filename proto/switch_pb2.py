from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from google.protobuf import reflection as _reflection
from google.protobuf import symbol_database as _symbol_database
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()

DESCRIPTOR = _descriptor.FileDescriptor(
  name='switch.proto',
  package='switch',
  syntax='proto3',
  serialized_options=b'\n\025io.grpc.examples.testB\013SwitchProtoP\001\242\002\006Switch',
  create_key=_descriptor._internal_create_key,
  serialized_pb=b'\n\x0cswitch.proto\x12\x06switch\"B\n\x07request\x12\r\n\x05srcip\x18\x01 \x01(\t\x12\r\n\x05\x64stip\x18\x02 \x01(\t\x12\x0e\n\x06status\x18\x03 \x01(\x05\x12\t\n\x01\x65\x18\x04 \x01(\x03\"\x19\n\x05reply\x12\x10\n\x08new_rate\x18\x01 \x01(\x03\x32\x34\n\x07\x43hannel\x12)\n\x05\x66\x65tch\x12\x0f.switch.request\x1a\r.switch.reply\"\x00\x42/\n\x15io.grpc.examples.testB\x0bSwitchProtoP\x01\xa2\x02\x06Switchb\x06proto3'
)

_REQUEST = _descriptor.Descriptor(
  name='request',
  full_name='switch.request',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  create_key=_descriptor._internal_create_key,
  fields=[
    _descriptor.FieldDescriptor(
      name='srcip', full_name='switch.request.srcip', index=0,
      number=1, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=b"".decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='dstip', full_name='switch.request.dstip', index=1,
      number=2, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=b"".decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='status', full_name='switch.request.status', index=2,
      number=3, type=5, cpp_type=1, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='e', full_name='switch.request.e', index=3,
      number=4, type=3, cpp_type=2, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  serialized_options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=24,
  serialized_end=90,
)


_REPLY = _descriptor.Descriptor(
  name='reply',
  full_name='switch.reply',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  create_key=_descriptor._internal_create_key,
  fields=[
    _descriptor.FieldDescriptor(
      name='new_rate', full_name='switch.reply.new_rate', index=0,
      number=1, type=3, cpp_type=2, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  serialized_options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=92,
  serialized_end=117,
)

DESCRIPTOR.message_types_by_name['request'] = _REQUEST
DESCRIPTOR.message_types_by_name['reply'] = _REPLY
_sym_db.RegisterFileDescriptor(DESCRIPTOR)

request = _reflection.GeneratedProtocolMessageType('request', (_message.Message,), {
  'DESCRIPTOR' : _REQUEST,
  '__module__' : 'switch_pb2'
  # @@protoc_insertion_point(class_scope:switch.request)
  })
_sym_db.RegisterMessage(request)

reply = _reflection.GeneratedProtocolMessageType('reply', (_message.Message,), {
  'DESCRIPTOR' : _REPLY,
  '__module__' : 'switch_pb2'
  # @@protoc_insertion_point(class_scope:switch.reply)
  })
_sym_db.RegisterMessage(reply)


DESCRIPTOR._options = None

_CHANNEL = _descriptor.ServiceDescriptor(
  name='Channel',
  full_name='switch.Channel',
  file=DESCRIPTOR,
  index=0,
  serialized_options=None,
  create_key=_descriptor._internal_create_key,
  serialized_start=119,
  serialized_end=171,
  methods=[
  _descriptor.MethodDescriptor(
    name='fetch',
    full_name='switch.Channel.fetch',
    index=0,
    containing_service=None,
    input_type=_REQUEST,
    output_type=_REPLY,
    serialized_options=None,
    create_key=_descriptor._internal_create_key,
  ),
])
_sym_db.RegisterServiceDescriptor(_CHANNEL)

DESCRIPTOR.services_by_name['Channel'] = _CHANNEL

# @@protoc_insertion_point(module_scope)
