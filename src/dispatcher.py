import wsgi
import util.handler
import handler.v2.gateway_auth
import controller.datastore
import handler.v2.gateway_metadata
import handler.v2.gateway_metadata_file
import handler.v2.gateway_file_thumbnail


def dispatch(environ, start_response):
    return wsgi.dispatch(environ, start_response)


def update_config(properties):

    #
    # framework
    #

    wsgi.update_config({
        'log.enable': properties.get('wsgi.log.enable'),
        'log.path': properties.get('wsgi.log.path'),
    })

    #
    # util
    #

    util.handler.update_config({
        "usage.interval.seconds": properties.get('util.handler.usage.interval.seconds'),
        "usage.count.max": properties.get('util.handler.usage.count.max'),
        "auth.duration.seconds": properties.get('util.handler.auth.duration.seconds')
    })

    #
    # controller
    #

    controller.datastore.update_config({
        'path': properties['controller.datastore.path']
    })

    #
    # handler
    #
    handler.v2.gateway_auth.update_config({
        'acl.path': properties['handler.v2.auth.acl.path']
    })
    handler.v2.gateway_metadata_file.update_config({
        'temp.dir': properties['handler.v2.metadata_file.temp.dir']
    })
    handler.v2.gateway_metadata.update_config({
        'temp.dir': properties['handler.v2.metadata.temp.dir']
    })
    handler.v2.gateway_file_thumbnail.update_config({
        'temp.dir': properties['handler.v2.file_thumbnail.temp.dir']
    })

    # auth_config = {}
    # for prop in properties.keys():
    #     if prop.startswith('handler.v2.auth.'):
    #         auth_config[prop[16:]] = properties[prop]
    # handler.v2.auth.update_config(auth_config)
