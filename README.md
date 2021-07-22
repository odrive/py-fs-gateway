# File Server Gateway
odrive integrates with applications through Storage Gateways.

A Storage Gateway is simply a web server implementing the [Gateway API](https://github.com/odrive/gateway-api) used by odrive to access and synchronize files.

File Server Gateway is a reference implementation of the Gateway API providing access to server storage.

# Setup

- Clone this repo.
- Install Python3.
- Install the latest PIP.
- Run the setup script to create the Python virtual environment:

*Windows*
```
setup/setup_win.ps1
```

*Mac or Linux*
```
setup/setup_mac.sh
```

# Configure
`/bin/config.json` defines the runtime configuration.
```
{
  "controller.datastore.path": "datastore",

  "util.handler.usage.interval.seconds": 1,
  "util.handler.usage.count.max": 60,
  "util.handler.auth.duration.seconds": 86400,

  "wsgi.log.enable": true,
  "wsgi.log.path": "server.log",

  "handler.v2.metadata_file.temp.dir": "temp",
  "handler.v2.metadata.temp.dir": "temp",
  "handler.v2.file_thumbnail.temp.dir": "temp",
  "handler.v2.auth.acl.path": "acl.json"
}
```

The default configuration enables logging and uses the current working directory for logs and session files. 

If you want to change the runtime settings, update the properties in `config.json` and restart.

Property | Description
---|---
`controller.datastore.path` | Where to store session files.
`util.handler.usage.interval.seconds` | Sampling period for limiting usage.
`util.handler.usage.count.max` | Maximum requests within usage interface. Requests beyond the max return 429 status code.
`util.handler.auth.expiration` | Session duration in minutes.  
`wsgi.log.enable` | Set `true` to log every server request.
`wsgi.log.path` | Relative or absolute path to server log.
`handler.v2.metadata_file.temp.dir`| Temp staging directory for uploads.
`handler.v2.file_thumbnail.temp.dir`| Temp caching directory for thumbnails.
`handler.v2.auth.acl.path` | Where to get the access control file.

# Access Control
File Server Gateway requires a valid *access key* to `POST /v2/auth` and receive access tokens. 
`/bin/acl.json` defines the valid access keys and permissions. The server admin updates this file to grant and revoke access.

Property | Description
---|---
`<replace_with_access_key>.path` | Accessible path and root folder for access key. Path must be absolute.
`<replace_with_access_key>.writeable` | Default access is read-only. Set `true` to enable write access.

For example, to grant users write access to `/gateway/storage`, add the following keys to `/bin/acl.json`:

```
**Mac/Linux**
{
  "demo.path": "/gateway/storage",
  "demo.writable": true
}
```
**Windows**
```
{
  "demo.path": "C:\\gateway\\storage",
  "demo.writable": true
}
```

For secure access, replace "demo" with a randomized key to give users.

Restart the server to load changes to access control.

# Configure cherrypy

File Server Gateway is a WSGI application running in cherrypy. `/bin/run.py` defines the cherrypy configuration.

```
# configure cherrypy
cherrypy.config.update({
    'server.socket_port': 9083,
    'server.socket_host': '127.0.0.1',
    'server.thread_pool': 30,
    'server.max_request_body_size': 0,
})
```

Modify `/bin/run.py` to change the cherrypy configuration. For example, update the `server.socket_port` property to change the server port number.


# Launch

Start the web server from the project bin directory.

*Windows*
```
cd bin
python run.py
```

*Mac or Linux*
```
cd bin
python3 run.py
```


# Connect

## Gateway Shell

Access server storage from the command line with Gateway Shell. 
You can interactively access the file server or create scripts to automate access. 

*Download link and screen shots coming soon ...*

## Gateway Sync

Access server storage directly on your computer with Gateway Sync.

*Download link and screen shots coming soon ...*

## Gateway API

Access server storage programmatically with the [Gateway API](https://github.com/odrive/gateway-api). 

All gateways implement the same API except for authorization. Use the File Server Gateway /v2/auth endpoint to sign in and then use the Gateway API to browse and access files on the server.

### Signing into File Server Gateway
```
POST /v2/auth
```
**Request Body JSON**

Property | Description
---------|-------------
`key` | Secret key defined in acl.json.

**Response JSON**

Property | Description
---------|------------
`access.token` | Required AUTHORIZATION header for subsequent API requests. Does not expire.
`root.content.id` | `''` Session root folder ID is an empty string.

**Response Status**

Status | Description
-------|------------
`200` | OK
`400` | Missing key
`403` | Invalid key
`429` | Rate limited
