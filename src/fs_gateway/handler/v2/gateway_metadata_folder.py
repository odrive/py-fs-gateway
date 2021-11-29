import os
import json
import fs_gateway.util.handler


def handle(environ):

    #
    # Load.
    #

    # PATH_INFO
    params = {
        # URI /v2/gateway_metadata_folder/<gateway.metadata.id>
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
        '_gateway_metadata_folder' if params['gateway.metadata.id'] else ''
    )
    if delegate_func in globals():
        return eval(delegate_func)(environ, params)

    # Unknown.
    return {
        'code': '400',
        'message': 'Not found.'
    }


# Create root sub folder.
# POST /v2/gateway_metadata_folder
@fs_gateway.util.handler.handle_unexpected_exception
@fs_gateway.util.handler.limit_usage
@fs_gateway.util.handler.check_authorization
@fs_gateway.util.handler.load_path
@fs_gateway.util.handler.check_write_permission
@fs_gateway.util.handler.handle_file_system_io_error
def _post(environ, params):
    return _create_folder(environ, params)


# Create sub folder.
# POST /v2/gateway_metadata_folder/<gateway.metadata.id>
@fs_gateway.util.handler.handle_unexpected_exception
@fs_gateway.util.handler.limit_usage
@fs_gateway.util.handler.check_authorization
@fs_gateway.util.handler.load_path
@fs_gateway.util.handler.check_write_permission
@fs_gateway.util.handler.handle_file_system_io_error
def _post_gateway_metadata_folder(environ, params):
    return _create_folder(environ, params)


#
# Utility
#

def _create_folder(environ, params):

    #
    # Load.
    #

    params.update({
        'gateway.metadata.name': None,
        'gateway.metadata.modified': None,
    })

    # Load body.
    body = json.load(environ['wsgi.input'])
    params['gateway.metadata.name'] = body.get('gateway.metadata.name')
    params['gateway.metadata.modified'] = body.get('gateway.metadata.modified')

    #
    # Validate.
    #

    # Validate name.
    if params['gateway.metadata.name'] is None:
        return {
            'code': '400',
            'message': 'Missing gateway.metadata.name.'
        }

    # Create new folder
    new_folder_path = params['server.path'] + os.sep + params['gateway.metadata.name']
    os.mkdir(new_folder_path)

    # Preserve modified
    # todo - preserve the folder modified

    # send new content
    metadata = fs_gateway.util.handler.get_metadata(params['authorization']['gateway.auth.path'], new_folder_path)
    return {
        'code': '200',
        'message': 'OK',
        'contentType': 'application/json',
        'content': json.dumps(metadata)
    }
