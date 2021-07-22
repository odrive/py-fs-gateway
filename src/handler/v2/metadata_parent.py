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
        # URI /v2/metadata_parent/<content.id>
        'content.id': environ['PATH_INFO'][20:] if len(environ['PATH_INFO']) > 20 else None,
    }

    #
    # Validate.
    #

    #
    # Delegate.
    #

    delegate_func = '_{}{}'.format(
        environ['REQUEST_METHOD'].lower(),
        '_metadata_parent' if params['content.id'] else ''
    )
    if delegate_func in globals():
        return eval(delegate_func)(environ, params)

    # Unknown.
    return {
        'code': '404',
        'message': 'Not found.'
    }


# Move file or folder.
# PATCH /v2/metadata_parent/<content.id>
@util.handler.handle_unexpected_exception
@util.handler.limit_usage
@util.handler.check_authorization
@util.handler.load_path
@util.handler.check_write_permission
@util.handler.handle_file_system_io_error
def _patch_metadata_parent(environ, params):
    assert params.get('content.id')

    #
    # Load.
    #

    params.update({
        'parent.content.id': None,
    })

    # Load body.
    body = json.load(environ['wsgi.input'])
    params['parent.content.id'] = body.get('parent.content.id')

    #
    # Validate.
    #

    # Check new parent.
    if params['parent.content.id'] is None:
        return {
            'code': '400',
            'message': 'Missing parent.content.id.'
        }

    #
    # Execute.
    #

    # Move.
    content_name = os.path.basename(params['path'])
    destination_content_path = base64.urlsafe_b64decode(params['parent.content.id'].encode('utf-8')).decode('utf-8')
    new_path = f"{params['authorization']['path']}/{destination_content_path}/{content_name}"
    shutil.move(params['path'], new_path)

    # Success.
    metadata = util.handler.get_metadata(params['authorization']['path'], new_path)
    return {
        'code': '200',
        'message': 'OK',
        'contentType': 'application/json',
        'content': json.dumps(metadata)
    }

