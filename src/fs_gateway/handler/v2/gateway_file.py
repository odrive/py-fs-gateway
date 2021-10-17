import os
import fs_gateway.util.handler


def handle(environ):

    #
    # Load params.
    #

    params = {
        # From PATH_INFO
        # /v2/gateway_file/<gateway.metadata.id>
        'gateway.metadata.id': environ['PATH_INFO'][17:] if len(environ['PATH_INFO']) > 17 else None,
    }

    #
    # Validate.
    #

    #
    # Delegate.
    #

    delegate_func = '_{}{}'.format(
        environ['REQUEST_METHOD'].lower(),
        '_gateway_metadata' if params['gateway.metadata.id'] else ''
    )
    if delegate_func in globals():
        return eval(delegate_func)(environ, params)

    # Unknown.
    return {
        'code': '404',
        'message': 'Not found.'
    }


# Download file.
# GET /v2/gateway_file/<gateway.metadata.id>
@fs_gateway.util.handler.handle_unexpected_exception
@fs_gateway.util.handler.limit_usage
@fs_gateway.util.handler.check_authorization
@fs_gateway.util.handler.load_path
@fs_gateway.util.handler.check_read_permission
@fs_gateway.util.handler.handle_file_system_io_error
def _get_gateway_metadata(environ, params):
    assert params.get('gateway.metadata.id')

    #
    # Validate.
    #

    # Check file.
    if not os.path.isfile(params['server.path']):
        # Not file.
        return {
            'code': '400',
            'message': 'Not a file'
        }

    #
    # Execute.
    #

    # Stream file data.
    f = open(params['server.path'], 'rb')
    return {
        'code': '200',
        'message': 'OK',
        'contentType': 'application/octet-stream',
        'contentIterator': iter(lambda: f.read(1024*8), b'')
    }
