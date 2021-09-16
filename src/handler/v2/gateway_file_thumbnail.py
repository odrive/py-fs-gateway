import os
import util.handler
import PIL.Image


def handle(environ):

    #
    # Load params.
    #

    params = {
        # From PATH_INFO:
        # /v2/gateway_file_thumbnail/<gateway.metadata.id>
        'gateway.metadata.id': environ['PATH_INFO'][19:] if len(environ['PATH_INFO']) > 19 else None,
    }

    #
    # Validate.
    #

    #
    # Delegate.
    #

    delegate_func = '_{}{}'.format(
        environ['REQUEST_METHOD'].lower(),
        '_file_thumbnail' if params['gateway.metadata.id'] else ''
    )
    if delegate_func in globals():
        return eval(delegate_func)(environ, params)

    # Unknown.
    return {
        'code': '404',
        'message': 'Not found.'
    }


# Download icon.
# GET /v2/gateway_file_thumbnail/<gateway.metadata.id>
@util.handler.handle_unexpected_exception
@util.handler.limit_usage
@util.handler.check_authorization
@util.handler.load_path
@util.handler.check_read_permission
@util.handler.handle_file_system_io_error
def _get_file_thumbnail(environ, params):
    return _get_content_custom_preview(environ, params, 512)


#
# Utility
#

def _get_content_custom_preview(start_response, params, height):

    ext = params['path'].split('.')[-1]
    if not ext or ext.lower() not in ('jpg', 'png', 'jpeg', 'gif', 'tif'):
        return {'code': '403', 'message': 'Unsupported'}

    # build path
    cache_path = os.path.join(_config['temp.dir'], 'cache', params['resourceId'], str(height) + '.' + ext)

    # todo skip if original is small enough

    # generate if not in cache or cache is old
    if not os.path.exists(cache_path) or os.path.getmtime(cache_path) < os.path.getmtime(params['path']):
        im = PIL.Image.open(params['path'])

        try:
            im.thumbnail((height, height), PIL.Image.ANTIALIAS)
        except IOError:
            # Failed.
            return {'code': '403', 'message': 'Unsupported'}

        # create cache folder
        if not os.path.exists(_config['temp.dir'] + os.sep + 'cache'):
            os.makedirs(_config['temp.dir'] + os.sep + 'cache')
        if not os.path.exists(os.path.dirname(cache_path)):
            os.makedirs(os.path.dirname(cache_path))

        # cache image
        im.save(cache_path)

    # send image
    f = open(cache_path, 'rb')
    return {
        'code': '200',
        'message': 'OK',
        'contentType': 'application/octet-stream',
        'contentIterator': iter(lambda: f.read(1024*8), b'')
    }


#
# Configuration
#

def update_config(config):
    assert config.get('temp.dir')
    assert os.path.exists(config['temp.dir'])
    _config.update(config)


_config = {
    'temp.dir': 'temp'
}
