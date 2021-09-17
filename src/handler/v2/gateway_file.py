import os
import util.handler


def handle(environ):

    #
    # Load params.
    #

    params = {
        # From PATH_INFO
        # /v1/gateway_file/<gateway.metadata.id>
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
@util.handler.handle_unexpected_exception
@util.handler.limit_usage
@util.handler.check_authorization
@util.handler.load_path
@util.handler.check_read_permission
@util.handler.handle_file_system_io_error
def _get_gateway_metadata(environ, params):
    assert params.get('gateway.metadata.id')

    #
    # Validate.
    #

    # Check file.
    if not os.path.isfile(params['path']):
        # Not file.
        return {
            'code': '400',
            'message': 'Not a file'
        }

    #
    # Execute.
    #

    # Stream file data.
    f = open(params['path'], 'rb')
    return {
        'code': '200',
        'message': 'OK',
        'contentType': 'application/octet-stream',
        'contentIterator': iter(lambda: f.read(1024*8), b'')
    }
