`proxyd`: A WPAD-enabler for CLI programs
=========================================

While GUI programs on Linux usually support Autoconfiguration proxy servers,
most tools do not. Notably, cURL doesn't perform well. The
[WPAD](https://en.wikipedia.org/wiki/Web_Proxy_Auto-Discovery_Protocol) protocol
gives admins the ability to specify whether websites are to be accessed on a
granular level. They can deterime the correct proxy server or direct connection
based on the user's IP address as well as the destination domain name. Thus,
when outside of the company network, this script will be able to tell that the
user is connected directly to the internet.

However, the `http_proxy` environment variables are all-or-nothing. Either all
of your traffic is routed through the proxy (if it's set) or no traffic is (if
it isn't set). Furthermore, due to the nature of environment variables, it isn't
possible to change this variable once the process has started. This makes VPN
use particularly frustrating, as you constantly need to juggle whether you're on
the network on not.

The `proxyd` project aims to alleviate this issue. It is a thin proxy server
that bridges your programs to servers by utilising the
[libproxy](https://github.com/libproxy/libproxy) library. `libproxy` is meant to
be a smart proxy resolver capable of reading your system's settings and figuring
out which proxy you need, if any. Any HTTP proxy compatible program that uses
`http_proxy` will work with `proxyd` and get smart.

```
At work / VPN:
curl -> proxyd -> work proxy -> internet

At home / coffee shoppe:
curl -> proxyd -> internet
```

# Using
`proxyd` is at the moment a Python 2.7 program developed for RHEL 7. This is
likely to change in the near future. To get it to work with GNOME 3, you need to install:

```
# yum install -y libproxy-{gnome,kde,networkmanager,python}
```

This gives you the necessary `libproxy` modules so that it can detect your chosen DE's settings, as well as the necessary Python 2.7 bindings.

Then, you can launch the server on port 1234 (likely to change):

```sh
./main.py
```

To test it:

```sh
./test.sh curl -L google.com
```

# Known issues
* At the moment, the `CONNECT` proxy command isn't supported. It is required
  for HTTPS connections.
