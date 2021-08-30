import os
import base64
import time
import platform
import urllib
import urllib.parse
import requests
import traceback
import controller.datastore


def handle_requests_exception(dispatch_func):
    def wrapper(environ, params):
        try:
            return dispatch_func(environ, params)

        except requests.Timeout:
            return {'code': '504', 'message': 'Network Timeout'}

        except requests.ConnectionError:
            return {'code': '504', 'message': 'Network Connection Error'}

    return wrapper


def handle_unexpected_exception(dispatch_func):
    def wrapper(*args, **kwargs):
        try:
            # execute wrapped function
            return dispatch_func(*args, **kwargs)

        except Exception as e:

            # notify
            _print_unexpected_exception(e)

            # handle as internal server error
            return {'code': '500', 'message': 'Unexpected Error'}

    return wrapper


def check_authorization(dispatch_func):
    def wrapper(environ, params):

        # Get access token
        params['access.token'] = _get_access_token(environ)
        if params['access.token'] is None:
            return {
                'code': '401', 
                'message': 'Unauthorized'
            }

        # Get unexpired authorization for access token.
        params['authorization'] = controller.datastore.get(params['access.token'], 'access', _config['auth.duration.seconds'])
        if params['authorization'] is None:
            return {
                'code': '401', 
                'message': 'Unauthorized'
            }

        # Delegate authorized access.
        return dispatch_func(environ, params)

    return wrapper


def load_path(dispatch_func):
    def wrapper(environ, params):

        # Convert content.id to absolute path.
        if not params['metadata.content.id']:
            # Root.
            params['path'] = params['authorization']['path']
            return dispatch_func(environ, params)
        params['metadata.content.path'] = base64.urlsafe_b64decode(params['metadata.content.id'].encode('utf-8')).decode('utf-8')

        # If Windows, convert to a "long" path to deal with the path length restriction
        if platform.system() == "Windows":
            params['authorization']['path'] = _get_win_long_path(params['authorization']['path'])

        params['path'] = os.path.join(params['authorization']['path'], params['metadata.content.path'])
        if not os.path.exists(params['path']):
            return {'code': '404', 'message': 'Not Found'}

        return dispatch_func(environ, params)

    return wrapper


def check_read_permission(dispatch_func):
    def wrapper(environ, params):
        assert params.get('authorization')

        # check path permission
        if not params['path'].startswith(params['authorization']['path']):
            return {'code': '403', 'message': 'Unauthorized'}

        # dispatch
        return dispatch_func(environ, params)

    return wrapper


def check_write_permission(dispatch_func):
    def wrapper(environ, params):
        assert params.get('authorization')

        # check path permission
        if not params['path'].startswith(params['authorization']['path']):
            return {'code': '403', 'message': 'Unauthorized'}

        # check write permission
        if not params['authorization'].get('writable'):
            return {'code': '403', 'message': 'Read Only'}

        # dispatch
        return dispatch_func(environ, params)

    return wrapper


def handle_file_system_io_error(dispatch_func):
    def wrapper(environ, params):
        try:
            return dispatch_func(environ, params)
        except (IOError, OSError) as e:
            return {'code': '403', 'message': 'File System Not Allowed'}

    return wrapper


def limit_usage(dispatch_func):
    def wrapper(*args, **kwargs):

        global _usage_count
        global _usage_start

        # reset usage after usage interval
        if time.time() > _usage_start + _config['usage.interval.seconds']:
            _usage_start = time.time()
            _usage_count = 0

        _usage_count += 1

        # check if exceed max requests within usage interval
        if _usage_count > _config['usage.count.max']:
            return {'code': '429', 'message': 'Exceeded usage limit'}

        # execute wrapped function
        return dispatch_func(*args, **kwargs)

    return wrapper


def get_metadata(access_root, path):

    # Convert system path to access path
    access_path = path[len(access_root)+1:]  # remove the trailing slash with +1

    # base64 encoded relative path
    content_id = ''
    parent_content_id = None
    if access_path:
        content_id = base64.urlsafe_b64encode(access_path.encode('utf-8')).decode('ascii')
        parent_access_path = os.path.dirname(access_path)
        if parent_access_path:
            parent_content_id = base64.urlsafe_b64encode(access_path.encode('utf-8')).decode('ascii')

    # remap metadata
    if os.path.isdir(path):
        remapped_node = {
            'metadata.content.id': content_id,
            'metadata.content.parent.id': parent_content_id,
            'metadata.content.name': os.path.basename(path),
            'metadata.content.type': 'folder',
            'metadata.content.modified': int(os.path.getmtime(path) * 1000),  # milliseconds since unix epoch
        }
    else:
        remapped_node = {
            'metadata.content.id': content_id,
            'metadata.content.parent.id': parent_content_id,
            'metadata.content.name': os.path.basename(path),
            'metadata.content.type': 'file',
            'metadata.content.modified': int(os.path.getmtime(path) * 1000),  # milliseconds since unix epoch
            'metadata.file.size': os.path.getsize(path),
            'metadata.file.hash': f"{os.path.getsize(path)}{os.path.getmtime(path)}"
        }

    return remapped_node


def _print_unexpected_exception(exception):
    print('')
    print('-------unhandled exception---------')
    print(traceback.print_exc())
    print(exception)

    # report uncaught HTTPError
    if isinstance(exception, requests.HTTPError):
        print('')
        print('HTTP ERROR')
        print('URL: ' + exception.response.url)
        print('Status Code: ' + str(exception.response.status_code))
        print('Reason: ' + exception.response.reason)

        for header in exception.response.headers:
            if header.lower().startswith('x-odrive'):
                print(header + ': ' + exception.response.headers[header])
    print('')


def _get_access_token(environ):
    assert environ

    # Load from HTTP header.
    if 'HTTP_AUTHORIZATION' in environ:
        # load access token from header
        http_authorization_split = environ['HTTP_AUTHORIZATION'].split(' ')
        access_token = http_authorization_split[1] if len(http_authorization_split) > 1 else None
        if access_token:
            return access_token

    # Load from query string.
    query_params = urllib.parse.parse_qs(environ.get('QUERY_STRING'))
    if query_params.get('aut'):
        access_token = query_params['aut'][0]
        if access_token:
            return access_token

    # Load from cookie.
    access_token = _get_cookie('s', environ)
    if access_token:
        return access_token

    # No session ID.
    return None


def _get_cookie(name, environ):
    cookies = environ.get('HTTP_COOKIE')
    if cookies is None:
        return None

    # convert 'aaa=bbb; ccc=ddd' into {'aaa': 'bbb', 'ccc': 'ddd'}
    cookie_list = [item.split('=') for item in cookies.split(';')]
    cookie_map = {cookie[0].strip(' '): cookie[1].strip(' ') for cookie in cookie_list}

    return cookie_map.get(name)


def _get_win_long_path(path):
    _WINDOWS_LONG_PATH_PREFIX = "\\\\?\\"
    long_path = "{}{}".format(_WINDOWS_LONG_PATH_PREFIX, path)
    return long_path


#
# config
#

def update_config(config):
    assert config.get('usage.interval.seconds')
    assert config.get('usage.count.max')
    _config.update(config)


_config = {
    'usage.interval.seconds': 10,  # number of seconds
    'usage.count.max': 1000,  # max requests within usage interval
    'auth.duration.seconds': 86400  # session duration
}

_usage_start = time.time()
_usage_count = 0

