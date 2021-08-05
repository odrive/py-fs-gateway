import os
import base64
import json
import random
import string
import util.handler
import controller.datastore


def handle(environ):
    #
    # Load params.
    #

    params = {
        # From PATH_INFO
        # /v2/auth/<access.token>
        'access.token': environ['PATH_INFO'][9:] if len(environ['PATH_INFO']) > 9 else None,
    }

    #
    # Validate.
    #

    #
    # Delegate.
    #

    delegate_func = '_{}{}'.format(
        environ['REQUEST_METHOD'].lower(),
        '_auth' if params['access.token'] else ''
    )
    if delegate_func in globals():
        return eval(delegate_func)(environ, params)

    # Unknown.
    return {
        'code': '404',
        'message': 'Not found.'
    }


# Sign in.
# POST /v2/auth
@util.handler.handle_unexpected_exception
@util.handler.limit_usage
@util.handler.handle_requests_exception
def _post(environ, params):
    #
    # Params.
    #

    params.update({
        # From body.
        'key': None,
        'refresh.token': None,
    })

    # Load body.
    params.update(json.load(environ['wsgi.input']) if environ.get('wsgi.input') else {})

    #
    # Validate.
    #

    # Required params.
    if not (params['key'] or params['refresh.token']):
        return {
            'code': '400',
            'message': 'Missing key and refresh.token'
        }

    #
    # Execute.
    #

    # Authorize key.
    if params['key']:
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
                'access.token': authorization.get('access.token'),
                'refresh.token': authorization.get('refresh.token'),
                'root.content.id': authorization.get('root.content.id')
            }),
        }

    # Refresh access.token.
    if params['refresh.token']:
        authorization = _refresh(params['refresh.token'])
        if authorization is None:
            return {
                'code': '403',
                'message': 'Unauthorized'
            }

        return {
            'code': '200',
            'message': 'OK',
            'contentType': 'application/json',
            'content': json.dumps({
                'access.token': authorization.get('access.token'),
                'refresh.token': authorization.get('refresh.token'),
                'root.content.id': authorization.get('root.content.id')
            }),
        }

    # handle unexpected
    assert False


# Sign out.
# DELETE /v2/auth/<access.token>
@util.handler.handle_unexpected_exception
@util.handler.limit_usage
@util.handler.handle_requests_exception
def _delete_auth(environ, params):
    assert params.get('access.token')

    # Check access.
    access = controller.datastore.get(params['access.token'], 'access')
    if access is None:
        # Already gone.
        return {
            'code': '200',
            'message': 'OK'
        }

    # Delete access.
    controller.datastore.delete(access['access.token'], 'access')
    controller.datastore.delete(access['refresh.token'], 'refresh')
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
    controller.datastore.put(
        access_token,
        {
            'path': _acl.get(f"{access_key}.path"),
            'writable': _acl.get(f"{access_key}.writable") if _acl.get(f"{access_key}.writable") is True else False,
            'access.token': access_token,
            'refresh.token': refresh_token,
        },
        'access'
    )
    controller.datastore.put(
        refresh_token,
        {
            'path': _acl.get(f"{access_key}.path"),
            'writable': _acl.get(f"{access_key}.writable")  if _acl.get(f"{access_key}.writable") is True else False,
        },
        'refresh'
    )

    return {
        'access.token': access_token,
        'refresh.token': refresh_token,
        'root.content.id': ''
    }


def _refresh(refresh_token):
    # Load authorization to refresh.
    refresh_auth = controller.datastore.get(refresh_token, 'refresh')
    if refresh_auth is None:
        # Not allowed.
        return None

    # Create session.
    access_token = ''.join(
        random.SystemRandom().choice(
            string.ascii_uppercase + string.ascii_lowercase + string.digits) for _ in range(32))

    # Persist session.
    controller.datastore.put(
        access_token,
        {
            'path': refresh_auth.get('path'),
            'writable': refresh_auth.get('writable'),
            'access.token': access_token,
            'refresh.token': refresh_token,
        },
        'access'
    )

    return {
        'access.token': access_token,
        'refresh.token': refresh_token,
        'root.content.id': ''
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
