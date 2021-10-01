import os
import json
import cherrypy
from fs_gateway import dispatcher

#
# Configure server.
#

# Load properties from config.json.
config_path = os.path.join(os.getcwd(), 'config.json')
assert os.path.exists(config_path)
with open(os.path.join(os.getcwd(), 'config.json'), 'r') as data_file:
    config = json.load(data_file)

# Convert relative paths to absolute paths.
config['fs_gateway.wsgi.log.path'] = os.path.abspath(os.path.expanduser(config['fs_gateway.wsgi.log.path']))
config['fs_gateway.controller.datastore.path'] = os.path.abspath(os.path.expanduser(config['fs_gateway.controller.datastore.path']))
config['fs_gateway.handler.v2.gateway_metadata_file.temp.dir'] = os.path.abspath(os.path.expanduser(config['fs_gateway.handler.v2.gateway_metadata_file.temp.dir']))
config['fs_gateway.handler.v2.gateway_file_thumbnail.temp.dir'] = os.path.abspath(os.path.expanduser(config['fs_gateway.handler.v2.gateway_file_thumbnail.temp.dir']))
config['fs_gateway.handler.v2.gateway_auth.acl.path'] = os.path.abspath(os.path.expanduser(config['fs_gateway.handler.v2.gateway_auth.acl.path']))

# Ensure folder ready.
if not os.path.exists(config['fs_gateway.controller.datastore.path']):
    os.makedirs(config['fs_gateway.controller.datastore.path'])
if not os.path.exists(config['fs_gateway.handler.v2.gateway_file_thumbnail.temp.dir']):
    os.makedirs(config['fs_gateway.handler.v2.gateway_file_thumbnail.temp.dir'])
if not os.path.exists(config['fs_gateway.handler.v2.gateway_metadata_file.temp.dir']):
    os.makedirs(config['fs_gateway.handler.v2.gateway_metadata_file.temp.dir'])


# Load config.
dispatcher.update_config(config)

#
# launch cherrypy server
#

# mount our wsgi app to cherry root
cherrypy.tree.graft(dispatcher.dispatch, '/')

# configure cherrypy
cherrypy.config.update({
    'server.socket_port': 9083,
    'server.socket_host': '127.0.0.1',
    'server.thread_pool': 30,
    # remove any limit on request body size; default is 100MB; Use 2147483647 for 2GB
    'server.max_request_body_size': 0,
})

# run
cherrypy.engine.signals.subscribe()
cherrypy.engine.start()
cherrypy.engine.block()
