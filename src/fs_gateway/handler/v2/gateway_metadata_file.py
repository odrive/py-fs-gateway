import os
import time
import shutil
import tempfile
import json
import urllib.parse
import fs_gateway.util.handler


def handle(environ):

    #
    # Load.
    #

    # PATH_INFO
    params = {
        # URI /v2/gateway_metadata_file/<gateway.metadata.id>
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
        '_gateway_metadata_file' if params['gateway.metadata.id'] else ''
    )
    if delegate_func in globals():
        return eval(delegate_func)(environ, params)

    # Unknown.
    return {
        'code': '400',
        'message': 'Not found.'
    }


# Upload file to root.
# POST /v2/gateway_metadata_file
def _post(environ, params):
    return _post_gateway_metadata_file(environ, params)


# Upload file to folder.
# POST /v2/gateway_metadata_file/<gateway.metadata.id>
@fs_gateway.util.handler.handle_unexpected_exception
@fs_gateway.util.handler.limit_usage
@fs_gateway.util.handler.check_authorization
@fs_gateway.util.handler.load_path
@fs_gateway.util.handler.check_write_permission
@fs_gateway.util.handler.handle_file_system_io_error
def _post_gateway_metadata_file(environ, params):

    #
    # Load params.
    #

    params.update({
        'gateway.metadata.name': None,
        'gateway.metadata.modified': None,
        'gateway.metadata.file.size': None,
    })

    # Load headers.
    if environ.get('HTTP_X_GATEWAY_UPLOAD'):  # wsgi adds HTTP to the header, so client should use X_UPLOAD_JSON
        header_params = json.loads(environ['HTTP_X_GATEWAY_UPLOAD'])
        if header_params:
            if header_params.get('gateway.metadata.name'):
                params['gateway.metadata.name'] = urllib.parse.unquote(header_params['gateway.metadata.name'])
            params['gateway.metadata.file.size'] = header_params.get('gateway.metadata.file.size')
            params['gateway.metadata.modified'] = header_params.get('gateway.metadata.modified')

    #
    # Validate request.
    #

    # Validate create file params.
    if params['gateway.metadata.file.size'] is None:
        return {
            'code': '400',
            'message': 'Missing file.size.'
        }
    if not isinstance(params['gateway.metadata.file.size'], int):
        return {
            'code': '400',
            'message': 'Invalid size.'
        }
    if params['gateway.metadata.modified'] is None:
        return {
            'code': '400',
            'message': 'Missing gateway.metdata.modified.'
        }
    if not isinstance(params['gateway.metadata.modified'], int):
        return {
            'code': '400',
            'message': 'Invalid gateway.metadata.modified.'
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

    # Move temp into position.
    shutil.move(temp_path, params['server.path'] + os.sep + params['gateway.metadata.name'])

    # Success.
    metadata = fs_gateway.util.handler.get_metadata(params['authorization']['gateway.auth.path'], params['server.path'] + os.sep + params['gateway.metadata.name'])
    return {
        'code': '200',
        'message': 'OK',
        'contentType': 'application/json',
        'content': json.dumps(metadata)
    }


# Update file.
# PUT /v2/gateway_metadata_file/<gateway.metadata.id>
@fs_gateway.util.handler.handle_unexpected_exception
@fs_gateway.util.handler.limit_usage
@fs_gateway.util.handler.check_authorization
@fs_gateway.util.handler.load_path
@fs_gateway.util.handler.check_write_permission
@fs_gateway.util.handler.handle_file_system_io_error
def _put_gateway_metadata_file(environ, params):
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
    shutil.move(temp_path, params['server.path'])

    # Success.
    metadata = fs_gateway.util.handler.get_metadata(params['authorization']['gateway.auth.path'], params['server.path'])
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
