import os
import json
import random
import string
import fs_gateway.util.handler
import fs_gateway.controller.datastore


def handle(environ):

    #
    # Delegate.
    #

    delegate_func = '_{}'.format(
        environ['REQUEST_METHOD'].lower()
    )
    if delegate_func in globals():
        return eval(delegate_func)(environ)

    # Unknown.
    return {
        'code': '400',
        'message': 'Invalid endpoint.'
    }


# Refresh access token.
# POST /v2/gateway_auth_access
@fs_gateway.util.handler.handle_unexpected_exception
@fs_gateway.util.handler.limit_usage
@fs_gateway.util.handler.handle_requests_exception
def _post(environ, params):
    #
    # Params.
    #

    params.update({
        # From body.
        'gateway.auth.refresh.token': None,
    })

    # Load body.
    params.update(json.load(environ['wsgi.input']) if environ.get('wsgi.input') else {})

    #
    # Validate.
    #

    # Required params.
    if not params['gateway.auth.refresh.token']:
        return {
            'code': '400',
            'message': 'Missing refresh token.'
        }

    #
    # Execute.
    #

    # Refresh access.token.
    if params['gateway.auth.refresh.token']:
        fresh_auth = _refresh(params['gateway.auth.refresh.token'])
        if fresh_auth is None:
            return {
                'code': '403',
                'message': 'Unauthorized'
            }

        return {
            'code': '200',
            'message': 'OK',
            'contentType': 'application/json',
            'content': json.dumps({
                'gateway.auth.access.token': fresh_auth.get('gateway.auth.access.token'),
                'gateway.auth.refresh.token': fresh_auth.get('gateway.auth.refresh.token'),
            }),
        }

    # handle unexpected
    assert False


def _refresh(refresh_token):
    # Load authorization to refresh.
    refresh_auth = fs_gateway.controller.datastore.get(refresh_token, 'refresh')
    if refresh_auth is None:
        # Not allowed.
        return None

    # Create session.
    access_token = ''.join(
        random.SystemRandom().choice(
            string.ascii_uppercase + string.ascii_lowercase + string.digits) for _ in range(32))

    # Persist session.
    fs_gateway.controller.datastore.put(
        access_token,
        {
            'gateway.auth.path': refresh_auth.get('gateway.auth.path'),
            'gateway.auth.writable': refresh_auth.get('gateway.auth.writable'),
            'gateway.auth.access.token': access_token,
            'gateway.auth.refresh.token': refresh_token,
        },
        'access'
    )

    return {
        'gateway.auth.access.token': access_token,
        'gateway.auth.refresh.token': refresh_token,
    }

