import os
import base64
import shutil
import json
import util.handler


def handle(environ):

    #
    # Load.
    #

    # PATH_INFO
    params = {
        # URI /v2/gateway_metadata_parent/<gateway.metadata.id>
        'gateway.metadata.id': environ['PATH_INFO'][28:] if len(environ['PATH_INFO']) > 28 else None,
    }

    #
    # Validate.
    #

    #
    # Delegate.
    #

    delegate_func = '_{}{}'.format(
        environ['REQUEST_METHOD'].lower(),
        '_metadata_parent' if params['gateway.metadata.id'] else ''
    )
    if delegate_func in globals():
        return eval(delegate_func)(environ, params)

    # Unknown.
    return {
        'code': '404',
        'message': 'Not found.'
    }


# Move file or folder.
# PATCH /v2/gateway_metadata_parent/<gateway.metadata.id>
@util.handler.handle_unexpected_exception
@util.handler.limit_usage
@util.handler.check_authorization
@util.handler.load_path
@util.handler.check_write_permission
@util.handler.handle_file_system_io_error
def _patch_metadata_parent(environ, params):
    assert params.get('gateway.metadata.id')

    #
    # Load.
    #

    params.update({
        'new.gateway.metadata.parent.id': None,
    })

    # Load body.
    body = json.load(environ['wsgi.input'])
    params['new.gateway.metadata.parent.id'] = body.get('new.gateway.metadata.parent.id')

    #
    # Validate.
    #

    # Check new parent.
    if params['new.gateway.metadata.parent.id'] is None:
        return {
            'code': '400',
            'message': 'Missing new.gateway.metadata.parent.id.'
        }

    #
    # Execute.
    #

    # Move.
    content_name = os.path.basename(params['path'])
    destination_content_path = base64.urlsafe_b64decode(params['new.gateway.metadata.parent.id'].encode('utf-8')).decode('utf-8')
    new_path = os.path.join(params['authorization']['path'], destination_content_path, content_name)
    shutil.move(params['path'], new_path)

    # Success.
    metadata = util.handler.get_metadata(params['authorization']['path'], new_path)
    return {
        'code': '200',
        'message': 'OK',
        'contentType': 'application/json',
        'content': json.dumps(metadata)
    }

