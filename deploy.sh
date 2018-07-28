#!/bin/bash -eu

( cd app && npm run build )
rsync -av --delete server/ pi@192.168.0.127:Documents/src/wabatar/server/
rsync -av --delete app/build/ pi@192.168.0.127:Documents/src/wabatar/app/build/
