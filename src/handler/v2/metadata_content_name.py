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
        # URI /v2/metadata_content_name/<content.id>
        'metadata.content.id': environ['PATH_INFO'][18:] if len(environ['PATH_INFO']) > 18 else None,
    }

    #
    # Validate.
    #

    #
    # Delegate.
    #

    delegate_func = '_{}{}'.format(
        environ['REQUEST_METHOD'].lower(),
        '_metadata_content_name' if params['metadata.content.id'] else ''
    )
    if delegate_func in globals():
        return eval(delegate_func)(environ, params)

    # Unknown.
    return {
        'code': '404',
        'message': 'Not found.'
    }


# Rename file or folder.
# PATCH /v2/metadata_content_name/<content.id>
@util.handler.handle_unexpected_exception
@util.handler.limit_usage
@util.handler.check_authorization
@util.handler.load_path
@util.handler.check_write_permission
@util.handler.handle_file_system_io_error
def _patch_metadata_content_name(environ, params):
    assert params.get('metadata.content.id')

    #
    # Load.
    #

    params.update({
        'new.metadata.content.name': None,
        'old.metadata.content.name': None,
    })

    # Load body.
    body = json.load(environ['wsgi.input'])
    params['new.metadata.content.name'] = body.get('new.metadata.content.name')
    params['old.metadata.content.name'] = body.get('old.metadata.content.name')

    #
    # Validate.
    #

    # Validate name.
    if params['new.metadata.content.name'] is None:
        return {
            'code': '400',
            'message': 'Missing new.metadata.content.name'
        }
    if params['old.metadata.content.name'] != os.path.basename(params['path']):
        return {
            'code': '400',
            'message': 'Not expected name.'
        }

    #
    # Execute.
    #

    # Rename.
    new_path = os.path.dirname(params['path']) + os.sep + params['new.metadata.content.name']
    shutil.move(params['path'], new_path)

    # Success.
    metadata = util.handler.get_metadata(params['authorization']['path'], new_path)
    return {
        'code': '200',
        'message': 'OK',
        'contentType': 'application/json',
        'content': json.dumps(metadata)
    }
