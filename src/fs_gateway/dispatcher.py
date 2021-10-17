import fs_gateway.wsgi
import fs_gateway.util.handler
import fs_gateway.handler.v2.gateway_auth
import fs_gateway.controller.datastore
import fs_gateway.handler.v2.gateway_metadata_file
import fs_gateway.handler.v2.gateway_file_thumbnail


def dispatch(environ, start_response):
    return fs_gateway.wsgi.dispatch(environ, start_response)


def update_config(properties):

    #
    # framework
    #

    fs_gateway.wsgi.update_config({
        'log.enable': properties.get('fs_gateway.wsgi.log.enable'),
        'log.path': properties.get('fs_gateway.wsgi.log.path'),
    })

    #
    # util
    #

    fs_gateway.util.handler.update_config({
        "usage.interval.seconds": properties.get('fs_gateway.util.handler.usage.interval.seconds'),
        "usage.count.max": properties.get('fs_gateway.util.handler.usage.count.max'),
        "auth.duration.seconds": properties.get('fs_gateway.util.handler.auth.duration.seconds')
    })

    #
    # controller
    #

    fs_gateway.controller.datastore.update_config({
        'path': properties['fs_gateway.controller.datastore.path']
    })

    #
    # handler
    #

    fs_gateway.handler.v2.gateway_auth.update_config({
        'acl.path': properties['fs_gateway.handler.v2.gateway_auth.acl.path']
    })
    fs_gateway.handler.v2.gateway_metadata_file.update_config({
        'temp.dir': properties['fs_gateway.handler.v2.gateway_metadata_file.temp.dir']
    })
    fs_gateway.handler.v2.gateway_file_thumbnail.update_config({
        'temp.dir': properties['fs_gateway.handler.v2.gateway_file_thumbnail.temp.dir']
    })

