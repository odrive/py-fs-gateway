import os
import shutil
import json
import util.handler


def handle(environ):

    #
    # Load.
    #

    # PATH_INFO
    params = {
        # URI /v2/gateway_metadata_content_name/<gateway.metadata.id>
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
        '_metadata_content_name' if params['gateway.metadata.id'] else ''
    )
    if delegate_func in globals():
        return eval(delegate_func)(environ, params)

    # Unknown.
    return {
        'code': '404',
        'message': 'Not found.'
    }


# Rename file or folder.
# PATCH /v2/gateway_metadata_content_name/<gateway.metadata.id>
@util.handler.handle_unexpected_exception
@util.handler.limit_usage
@util.handler.check_authorization
@util.handler.load_path
@util.handler.check_write_permission
@util.handler.handle_file_system_io_error
def _patch_metadata_content_name(environ, params):
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
    if params['old.gateway.metadata.name'] and params['old.gateway.metadata.name'] != os.path.basename(params['path']):
        return {
            'code': '400',
            'message': 'Not expected name.'
        }

    #
    # Execute.
    #

    # Rename.
    new_path = os.path.dirname(params['path']) + os.sep + params['new.gateway.metadata.name']
    shutil.move(params['path'], new_path)

    # Success.
    metadata = util.handler.get_metadata(params['authorization']['path'], new_path)
    return {
        'code': '200',
        'message': 'OK',
        'contentType': 'application/json',
        'content': json.dumps(metadata)
    }
