# xrpl_stats_client
Python client for XRPL validator statistics

Prototype client that submits stats related to the `rippled` daemon, along with other system related information.

This client has been tested on Python 3.6, and will not work on Python 3.5 and below.

It is recommended that this client be run under a separate Virtual Environment. It can only be run on the machine where the `rippled` validator is installed.

Module requirements are published in `requirements.txt`. A sample systemd file is also provided, and can be modified to suit requirements. There are editable parameters in the `monitor.ini` file, and careful attention must be paid to them.

The mandatory parameters are:
```
[default]
endpoint = THE HTTP ENDPOINT

[credentials]
secret = YOURSECRET
```
Status reports are published in JSON, with a header containing the SHA256 hash of the payload. The hash is based on the shared secret which is defined in the key `secret`.

The script has a few command line methods:

`python status_monitor.py gensecret` will generate a random secret, which should be stored in the `monitor.ini` file. It is recommended that you use this, to ensure a random secret.

`python status_monitor.py testmode` will not send data to the endpoint, but print the Header and the JSON payload to the screen.

Future methods will include a `configtest`

The script will **always** return a JSON, even if the `rippled` daemon isn't running. It wil return a key/value `"Error" : true", in that event, but system information will continue to be present.
