import os
import json
import random
import string
import fs_gateway.util.handler
import fs_gateway.controller.datastore


def handle(environ):
    #
    # Load params.
    #

    params = {
        # From PATH_INFO
        # /v2/gateway_auth/<gateway.auth.access.token>
        'gateway.auth.access.token': environ['PATH_INFO'][17:] if len(environ['PATH_INFO']) > 17 else None,
    }

    #
    # Validate.
    #

    #
    # Delegate.
    #

    delegate_func = '_{}{}'.format(
        environ['REQUEST_METHOD'].lower(),
        '_gateway_auth' if params['gateway.auth.access.token'] else ''
    )
    if delegate_func in globals():
        return eval(delegate_func)(environ, params)

    # Unknown.
    return {
        'code': '404',
        'message': 'Not found.'
    }


# Sign in.
# POST /v2/gateway_auth
@fs_gateway.util.handler.handle_unexpected_exception
@fs_gateway.util.handler.limit_usage
def _post(environ, params):
    #
    # Params.
    #

    params.update({
        # From body.
        'key': None,
    })

    # Load body.
    params.update(json.load(environ['wsgi.input']) if environ.get('wsgi.input') else {})

    #
    # Validate.
    #

    # Required params.
    if params['key'] is None:
        return {
            'code': '400',
            'message': 'Missing key '
        }

    #
    # Execute.
    #

    # Authorize key.
    authorization = _authorize(params['key'])
    if authorization is None:
        # Not allowed.
        return {
            'code': '403',
            'message': 'Unauthorized'
        }

    # Authorized.
    return {
        'code': '200',
        'message': 'OK',
        'contentType': 'application/json',
        'content': json.dumps({
            'gateway.auth.access.token': authorization.get('gateway.auth.access.token'),
            'gateway.auth.refresh.token': authorization.get('gateway.auth.refresh.token'),
            'gateway.auth.metadata.id': authorization.get('gateway.auth.metadata.id')
        }),
    }


# Sign out.
# DELETE /v2/gateway_auth/<gateway.auth.access.token>
@fs_gateway.util.handler.handle_unexpected_exception
@fs_gateway.util.handler.limit_usage
def _delete_gateway_auth(environ, params):
    assert params.get('gateway.auth.access.token')

    # Check access.
    access = fs_gateway.controller.datastore.get(params['gateway.auth.access.token'], 'access')
    if access is None:
        # Already gone.
        return {
            'code': '200',
            'message': 'OK'
        }

    # Delete access.
    fs_gateway.controller.datastore.delete(access['gateway.auth.access.token'], 'access')
    fs_gateway.controller.datastore.delete(access['gateway.auth.refresh.token'], 'refresh')
    return {
        'code': '200',
        'message': 'OK'
    }


def _authorize(access_key):
    # Load access_key.
    access_path = _acl.get(f"{access_key}.path")
    if access_path is None:
        # Not authorized.
        return None
    assert os.path.exists(access_path)

    # Create session.
    access_token = ''.join(
        random.SystemRandom().choice(
            string.ascii_uppercase + string.ascii_lowercase + string.digits) for _ in range(32))

    refresh_token = ''.join(
        random.SystemRandom().choice(
            string.ascii_uppercase + string.ascii_lowercase + string.digits) for _ in range(32))

    # Persist session.
    assert _acl.get(f"{access_key}.path")
    fs_gateway.controller.datastore.put(
        access_token,
        {
            'gateway.auth.path': _acl.get(f"{access_key}.path"),
            'gateway.auth.writable': _acl.get(f"{access_key}.writable") if _acl.get(f"{access_key}.writable") is True else False,
            'gateway.auth.access.token': access_token,
            'gateway.auth.refresh.token': refresh_token,
        },
        'access'
    )
    fs_gateway.controller.datastore.put(
        refresh_token,
        {
            'gateway.auth.path': _acl.get(f"{access_key}.path"),
            'gateway.auth.writable': _acl.get(f"{access_key}.writable")  if _acl.get(f"{access_key}.writable") is True else False,
        },
        'refresh'
    )

    return {
        'gateway.auth.access.token': access_token,
        'gateway.auth.refresh.token': refresh_token,
        'gateway.auth.metadata.id': ''
    }


def update_config(config):
    assert config.get('acl.path')

    with open(config['acl.path'], 'r') as acl_json:
        _acl.clear()
        _acl.update(json.load(acl_json))

    _config.update(config)


_config = {
    # 'acl.path': '/acl.json'
}

_acl = {
    # '<key>.path': <path>,
    # '<key>.writeable': True or False
}
