import os
import shutil
import json
import fs_gateway.util.handler


def handle(environ):

    #
    # Load params.
    #

    params = {
        # From PATH_INFO: /v2/gateway_metadata/<gateway.metadata.id>
        'gateway.metadata.id': environ['PATH_INFO'][21:] if len(environ['PATH_INFO']) > 21 else None,
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


# Delete root folder.
# DELETE /v2/gateway_metadata
@fs_gateway.util.handler.handle_unexpected_exception
@fs_gateway.util.handler.limit_usage
@fs_gateway.util.handler.check_authorization
def _delete(environ, params):
    # Not allowed.
    return {
        'code': '403',
        'message': 'Not allowed.',
    }


# Delete file or folder.
# DELETE /v2/gateway_metadata/<gateway.metadata.id>
@fs_gateway.util.handler.handle_unexpected_exception
@fs_gateway.util.handler.limit_usage
@fs_gateway.util.handler.check_authorization
@fs_gateway.util.handler.load_path
@fs_gateway.util.handler.check_write_permission
@fs_gateway.util.handler.handle_file_system_io_error
def _delete_gateway_metadata(environ, params):
    assert params.get('gateway.metadata.id')

    #
    # Validate.
    #

    # Check path.
    if params['gateway.metadata.id'] is None:
        # handle root
        return {
            'code': '403',
            'message': 'Not Allowed'
        }

    #
    # Execute.
    #

    if os.path.isdir(params['server.path']):
        # delete folder
        shutil.rmtree(params['server.path'])
    else:
        # delete file
        os.remove(params['server.path'])

    # Success.
    return {
        'code': '200',
        'message': 'OK'
    }


# Get metadata for root folder.
# GET /v2/gateway_metadata
@fs_gateway.util.handler.handle_unexpected_exception
@fs_gateway.util.handler.limit_usage
@fs_gateway.util.handler.check_authorization
@fs_gateway.util.handler.load_path
@fs_gateway.util.handler.check_read_permission
def _get(environ, params):
    # Get root folder metadata.
    return {
        'code': '200',
        'message': 'ok',
        'contentType': 'application/json',
        'content': json.dumps({
            'gateway.metadata.id': '',
            'gateway.metadata.type': 'folder',
            'gateway.metadata.name': '',
            'gateway.metadata.modified': None,
        })
    }


# Get file or folder metadata.
# GET /v2/gateway_metadata/<gateway.metadata.id>
@fs_gateway.util.handler.handle_unexpected_exception
@fs_gateway.util.handler.limit_usage
@fs_gateway.util.handler.check_authorization
@fs_gateway.util.handler.load_path
@fs_gateway.util.handler.check_read_permission
@fs_gateway.util.handler.handle_file_system_io_error
def _get_gateway_metadata(environ, params):
    assert params.get('gateway.metadata.id')

    metadata = fs_gateway.util.handler.get_metadata(params['authorization']['gateway.auth.path'], params['server.path'])
    return {
        'code': '200',
        'message': 'OK',
        'contentType': 'application/json',
        'content': json.dumps(metadata)
    }
