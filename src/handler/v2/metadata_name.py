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
        # URI /v2/metadata_name/<content.id>
        'content.id': environ['PATH_INFO'][18:] if len(environ['PATH_INFO']) > 18 else None,
    }

    #
    # Validate.
    #

    #
    # Delegate.
    #

    delegate_func = '_{}{}'.format(
        environ['REQUEST_METHOD'].lower(),
        '_metadata_name' if params['content.id'] else ''
    )
    if delegate_func in globals():
        return eval(delegate_func)(environ, params)

    # Unknown.
    return {
        'code': '404',
        'message': 'Not found.'
    }


# Rename file or folder.
# PATCH /v2/metadata_name/<content.id>
@util.handler.handle_unexpected_exception
@util.handler.limit_usage
@util.handler.check_authorization
@util.handler.load_path
@util.handler.check_write_permission
@util.handler.handle_file_system_io_error
def _patch_metadata_name(environ, params):
    assert params.get('content.id')

    #
    # Load.
    #

    params.update({
        'content.name': None,
    })

    # Load body.
    body = json.load(environ['wsgi.input'])
    params['content.name'] = body.get('content.name')

    #
    # Validate.
    #

    # Validate name.
    if params['content.name'] is None:
        return {
            'code': '400',
            'message': 'Missing content.name'
        }

    #
    # Execute.
    #

    # Rename.
    new_path = os.path.dirname(params['path']) + os.sep + params['content.name']
    shutil.move(params['path'], new_path)

    # Success.
    metadata = util.handler.get_metadata(params['authorization']['path'], new_path)
    return {
        'code': '200',
        'message': 'OK',
        'contentType': 'application/json',
        'content': json.dumps(metadata)
    }
