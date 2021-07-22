import os
import json
import util.handler


def handle(environ):

    #
    # Load.
    #

    # PATH_INFO
    params = {
        # URI /v2/metadata.folder/<content.id>
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
        '_metadata_folder' if params['content.id'] else ''
    )
    if delegate_func in globals():
        return eval(delegate_func)(environ, params)

    # Unknown.
    return {
        'code': '404',
        'message': 'Not found.'
    }


# Create root sub folder.
# POST /v2/metadata_folder
@util.handler.handle_unexpected_exception
@util.handler.limit_usage
@util.handler.check_authorization
@util.handler.load_path
@util.handler.check_write_permission
@util.handler.handle_file_system_io_error
def _post(environ, params):
    return _create_folder(environ, params)


# Create sub folder.
# POST /v2/metadata_folder/<content.id>
@util.handler.handle_unexpected_exception
@util.handler.limit_usage
@util.handler.check_authorization
@util.handler.load_path
@util.handler.check_write_permission
@util.handler.handle_file_system_io_error
def _post_metadata_folder(environ, params):
    return _create_folder(environ, params)


#
# Utility
#

def _create_folder(environ, params):

    #
    # Load.
    #

    params.update({
        'content.name': None,
        'content.modified': None,
    })

    # Load body.
    body = json.load(environ['wsgi.input'])
    params['content.name'] = body.get('content.name')
    params['content.modified'] = body.get('content.modified')

    #
    # Validate.
    #

    # Validate name.
    if params['content.name'] is None:
        return {
            'code': '400',
            'message': 'Missing folder.name.'
        }

    # Create new folder
    new_folder_path = params['path'] + os.sep + params['content.name']
    os.mkdir(new_folder_path)

    # Preserve modified
    # todo - preserve the folder modified

    # send new content
    metadata = util.handler.get_metadata(params['authorization']['path'], new_folder_path)
    return {
        'code': '200',
        'message': 'OK',
        'contentType': 'application/json',
        'content': json.dumps(metadata)
    }
