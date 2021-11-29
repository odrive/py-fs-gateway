import os
import json
import fs_gateway.util.handler


def handle(environ):

    #
    # Load.
    #

    # PATH_INFO
    params = {
        # URI /v2/gateway_metadata_children/<gateway.metadata.id>
        'gateway.metadata.id': environ['PATH_INFO'][30:] if len(environ['PATH_INFO']) > 30 else None,
    }

    #
    # Validate.
    #

    #
    # Delegate.
    #

    delegate_func = '_{}{}'.format(
        environ['REQUEST_METHOD'].lower(),
        '_gateway_metadata' if params['gateway.metadata.id'] else ''
    )
    if delegate_func in globals():
        return eval(delegate_func)(environ, params)

    # Unknown.
    return {
        'code': '400',
        'message': 'Not found.'
    }


# List root.
# GET /v2/gateway_metadata_children
@fs_gateway.util.handler.handle_unexpected_exception
@fs_gateway.util.handler.limit_usage
@fs_gateway.util.handler.check_authorization
@fs_gateway.util.handler.load_path
@fs_gateway.util.handler.check_read_permission
@fs_gateway.util.handler.handle_file_system_io_error
def _get(environ, params):
    return _list_folder(environ, params)


# List folder.
# GET /v2/gateway_metadata_children/<gateway.metadata.id>
@fs_gateway.util.handler.handle_unexpected_exception
@fs_gateway.util.handler.limit_usage
@fs_gateway.util.handler.check_authorization
@fs_gateway.util.handler.load_path
@fs_gateway.util.handler.check_read_permission
@fs_gateway.util.handler.handle_file_system_io_error
def _get_gateway_metadata(environ, params):
    return _list_folder(environ, params)


#
# Utility
#

def _list_folder(environ, params):
    listing = []
    for filename in os.listdir(params['server.path']):
        # map item metadata
        remapped_node = fs_gateway.util.handler.get_metadata(params['authorization']['gateway.auth.path'], params['server.path'] + os.sep + filename)
        listing.append(remapped_node)
    return {
        'code': '200',
        'message': 'ok',
        'contentType': 'application/json',
        'content': json.dumps(listing)
    }
