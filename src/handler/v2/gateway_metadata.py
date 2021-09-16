import tempfile
import time
import os
import shutil
import json
import util.handler


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
        '_metadata' if params['gateway.metadata.id'] else ''
    )
    if delegate_func in globals():
        return eval(delegate_func)(environ, params)

    # Unknown.
    return {
        'code': '404',
        'message': 'Not found.'
    }


# Delete root folder.
# DELETE /v2/gateway_metadata
@util.handler.handle_unexpected_exception
@util.handler.limit_usage
@util.handler.check_authorization
def _delete(environ, params):
    # Not allowed.
    return {
        'code': '403',
        'message': 'Not allowed.',
    }


# Delete file or folder.
# DELETE /v2/gateway_metadata/<gateway.metadata.id>
@util.handler.handle_unexpected_exception
@util.handler.limit_usage
@util.handler.check_authorization
@util.handler.load_path
@util.handler.check_write_permission
@util.handler.handle_file_system_io_error
def _delete_metadata(environ, params):
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

    if os.path.isdir(params['path']):
        # delete folder
        shutil.rmtree(params['path'])
    else:
        # delete file
        os.remove(params['path'])

    # Success.
    return {
        'code': '200',
        'message': 'OK'
    }


# Get metadata for root folder.
# GET /v2/gateway_metadata
@util.handler.handle_unexpected_exception
@util.handler.limit_usage
@util.handler.check_authorization
@util.handler.load_path
@util.handler.check_read_permission
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
        })
    }


# Get file or folder metadata.
# GET /v2/gateway_metadata/<gateway.metadata.id>
@util.handler.handle_unexpected_exception
@util.handler.limit_usage
@util.handler.check_authorization
@util.handler.load_path
@util.handler.check_read_permission
@util.handler.handle_file_system_io_error
def _get_metadata(environ, params):
    assert params.get('gateway.metadata.id')

    metadata = util.handler.get_metadata(params['authorization']['path'], params['path'])
    return {
        'code': '200',
        'message': 'OK',
        'contentType': 'application/json',
        'content': json.dumps(metadata)
    }


# Update file.
# PUT /v2/gateway_metadata/<gateway.metadata.id>
@util.handler.handle_unexpected_exception
@util.handler.limit_usage
@util.handler.check_authorization
@util.handler.load_path
@util.handler.check_write_permission
@util.handler.handle_file_system_io_error
def _put_metadata(environ, params):
    assert params.get('gateway.metadata.id')

    #
    # Load.
    #

    params.update({
        'gateway.metadata.file.size': None,
        'gateway.metadata.modified': None,
    })

    # From headers.
    if environ.get('HTTP_X_GATEWAY_UPLOAD'):  # wsgi adds HTTP to the header, so client should use X_UPLOAD_JSON
        header_params = json.loads(environ['HTTP_X_GATEWAY_UPLOAD'])
        if header_params:
            params['gateway.metadata.modified'] = header_params.get('gateway.metadata.modified')
            params['gateway.metadata.file.size'] = header_params.get('gateway.metadata.file.size')

    #
    # Validate.
    #

    # Validate type.
    if params['gateway.metadata.file.size'] and not isinstance(params['gateway.metadata.file.size'], int):
        return {
            'code': '400',
            'message': 'Invalid size.'
        }
    if params['gateway.metadata.modified'] and not isinstance(params['gateway.metadata.modified'], int):
        return {
            'code': '400',
            'message': 'Invalid content.modified.'
        }

    #
    # Execute request.
    #

    # Stream upload to temp file.
    temp_file_descriptor, temp_path = tempfile.mkstemp(dir=_config['temp.dir'])
    with os.fdopen(temp_file_descriptor, 'wb') as out:
        for chunk in iter(lambda: environ['wsgi.input'].read(1024*8), b''):
            if chunk:
                out.write(chunk)

    # Preserve file modified time.
    mod_time = params['gateway.metadata.modified']/1000  # convert to seconds
    os.utime(temp_path, (time.time(), mod_time))

    # Replace file with temp.
    shutil.move(temp_path, params['path'])

    # Success.
    metadata = util.handler.get_metadata(params['authorization']['path'], params['path'])
    return {
        'code': '200',
        'message': 'OK',
        'contentType': 'application/json',
        'content': json.dumps(metadata)
    }


#
# configuration
#

def update_config(config):
    assert config.get('temp.dir')
    assert os.path.exists(config['temp.dir'])
    _config.update(config)


_config = {
    'temp.dir': None
}
