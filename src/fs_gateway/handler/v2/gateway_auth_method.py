import json

import fs_gateway.util.handler


def handle(environ):

    #
    # Load params.
    #

    params = {
        # From PATH_INFO: /v2/gateway_auth_method
        'gateway.metadata.id': environ['PATH_INFO'][23:] if len(environ['PATH_INFO']) > 23 else None,
    }

    #
    # Delegate.
    #

    delegate_func = '_{}{}'.format(
        environ['REQUEST_METHOD'].lower(),
        '_gateway_auth_method' if params['gateway.metadata.id'] else ''
    )
    if delegate_func in globals():
        return eval(delegate_func)(environ, params)

    # Unknown.
    return {
        'code': '400',
        'message': 'Not found.'
    }


# Get supported gateway auth method.
# GET /v2/gateway_auth_method
@fs_gateway.util.handler.handle_unexpected_exception
@fs_gateway.util.handler.limit_usage
def _get(environ, params):
    return {
        'code': '200',
        'message': 'OK',
        'contentType': 'application/json',
        'content': json.dumps({
            'gateway.auth.method': 'form',
            'gateway.auth.form': [
                {
                    'gateway.auth.form.input.field.name': 'key',
                    'gateway.auth.form.input.field.prompt': 'Please enter the access key.',
                    'gateway.auth.form.input.field.required': True,
                    'gateway.auth.form.input.field.order': 1,
                }
            ]
        })
    }
