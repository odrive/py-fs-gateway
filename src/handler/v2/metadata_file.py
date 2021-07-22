import os
import time
import shutil
import tempfile
import json
import util.handler


def handle(environ):

    #
    # Load.
    #

    # PATH_INFO
    params = {
        # URI /v2/metadata.file/<content.id>
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
        '_metadata_file' if params['content.id'] else ''
    )
    if delegate_func in globals():
        return eval(delegate_func)(environ, params)

    # Unknown.
    return {
        'code': '404',
        'message': 'Not found.'
    }


# Upload file to root.
# POST /v2/metadata_file
def _post(environ, params):
    return _post_metadata_file(environ, params)


# Upload file to folder.
# POST /v2/metadata_file/<content.id>
@util.handler.handle_unexpected_exception
@util.handler.limit_usage
@util.handler.check_authorization
@util.handler.load_path
@util.handler.check_write_permission
@util.handler.handle_file_system_io_error
def _post_metadata_file(environ, params):

    #
    # Load params.
    #

    params.update({
        'content.name': None,
        'content.modified': None,
        'file.size': None,
    })

    # Load headers.
    if environ.get('HTTP_X_GATEWAY_UPLOAD'):  # wsgi adds HTTP to the header, so client should use X_UPLOAD_JSON
        header_params = json.loads(environ['HTTP_X_GATEWAY_UPLOAD'])
        if header_params:
            if header_params.get('content.name'):
                params['content.name'] = header_params['content.name'].encode('ISO-8859-1').decode('unicode-escape')
            params['file.size'] = header_params.get('file.size')
            params['content.modified'] = header_params.get('content.modified')

    #
    # Validate request.
    #

    # Validate create file params.
    if params['file.size'] is None:
        return {
            'code': '400',
            'message': 'Missing file.size.'
        }
    if not isinstance(params['file.size'], int):
        return {
            'code': '400',
            'message': 'Invalid size.'
        }
    if params['content.modified'] is None:
        return {
            'code': '400',
            'message': 'Missing content.modified.'
        }
    if not isinstance(params['content.modified'], int):
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
    mod_time = params['content.modified']/1000  # convert to seconds
    os.utime(temp_path, (time.time(), mod_time))

    # Move temp into position.
    shutil.move(temp_path, params['path'] + os.sep + params['content.name'])

    # Success.
    metadata = util.handler.get_metadata(params['authorization']['path'], params['path'] + os.sep + params['content.name'])
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
