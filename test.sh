#!/bin/bash
unset http_proxy
unset https_proxy
unset HTTP_PROXY
unset HTTPS_PROXY

export http_proxy=http://127.0.0.1:1234
export https_proxy=http://127.0.0.1:1234
export HTTP_PROXY=http://127.0.0.1:1234
export HTTPS_PROXY=http://127.0.0.1:1234

prog=$(shift)
exec $prog "$@"
