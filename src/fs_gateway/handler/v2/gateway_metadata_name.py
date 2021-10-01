import os
import shutil
import json
import fs_gateway.util.handler


def handle(environ):

    #
    # Load.
    #

    # PATH_INFO
    params = {
        # URI /v2/gateway_metadata_name/<gateway.metadata.id>
        'gateway.metadata.id': environ['PATH_INFO'][26:] if len(environ['PATH_INFO']) > 26 else None,
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
        'code': '404',
        'message': 'Not found.'
    }


# Rename file or folder.
# PUT /v2/gateway_metadata_name/<gateway.metadata.id>
@fs_gateway.util.handler.handle_unexpected_exception
@fs_gateway.util.handler.limit_usage
@fs_gateway.util.handler.check_authorization
@fs_gateway.util.handler.load_path
@fs_gateway.util.handler.check_write_permission
@fs_gateway.util.handler.handle_file_system_io_error
def _put_gateway_metadata(environ, params):
    assert params.get('gateway.metadata.id')

    #
    # Load.
    #

    params.update({
        'new.gateway.metadata.name': None,
        'old.gateway.metadata.name': None,
    })

    # Load body.
    body = json.load(environ['wsgi.input'])
    params['new.gateway.metadata.name'] = body.get('new.gateway.metadata.name')
    params['old.gateway.metadata.name'] = body.get('old.gateway.metadata.name')

    #
    # Validate.
    #

    # Validate name.
    if params['new.gateway.metadata.name'] is None:
        return {
            'code': '400',
            'message': 'Missing new.gateway.metadata.name'
        }
    if params['old.gateway.metadata.name'] and params['old.gateway.metadata.name'] != os.path.basename(params['server.path']):
        return {
            'code': '400',
            'message': 'Not expected name.'
        }

    #
    # Execute.
    #

    # Rename.
    new_path = os.path.dirname(params['server.path']) + os.sep + params['new.gateway.metadata.name']
    shutil.move(params['server.path'], new_path)

    # Success.
    metadata = util.handler.get_metadata(params['authorization']['gateway.auth.path'], new_path)
    return {
        'code': '200',
        'message': 'OK',
        'contentType': 'application/json',
        'content': json.dumps({
            'gateway.metadata.id': metadata['gateway.metadata.id'],
            'gateway.metadata.name': metadata['gateway.metadata.name'],
        })
    }
