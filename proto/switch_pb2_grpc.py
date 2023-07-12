"""Client and server classes corresponding to protobuf-defined services."""
import grpc

import switch_pb2 as switch__pb2


class ChannelStub(object):
    def __init__(self, channel):
        """Constructor.

        Args:
            channel: A grpc.Channel.
        """
        self.fetch = channel.unary_unary(
                '/switch.Channel/fetch',
                request_serializer=switch__pb2.request.SerializeToString,
                response_deserializer=switch__pb2.reply.FromString,
                )

class ChannelServicer(object):
    def fetch(self, request, context):
        """ccp agent fetches new rate
        """
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')


def add_ChannelServicer_to_server(servicer, server):
    rpc_method_handlers = {
            'fetch': grpc.unary_unary_rpc_method_handler(
                    servicer.fetch,
                    request_deserializer=switch__pb2.request.FromString,
                    response_serializer=switch__pb2.reply.SerializeToString,
            ),
    }
    generic_handler = grpc.method_handlers_generic_handler(
            'switch.Channel', rpc_method_handlers)
    server.add_generic_rpc_handlers((generic_handler,))


 # This class is part of an EXPERIMENTAL API.
class Channel(object):
    @staticmethod
    def fetch(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/switch.Channel/fetch',
            switch__pb2.request.SerializeToString,
            switch__pb2.reply.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)
