#!/bin/sh

if [ -f "/tmp/collector/startService.sh" ] && [ -d "/opt/collector" ]; then
    rm -rf /opt/collector
fi

if [ -f "/tmp/collector/startService.sh" ]; then
    cp -rf /tmp/collector /opt/collector
fi

if [ ! -d "/opt/collector" ]; then
    ln -s /opt/DockerCollector /opt/collector
fi

cd /opt/mongodb
chmod 775 startMongo.sh
./startMongo.sh

cd /opt/collector
chmod 775 startService.sh
./startService.sh /opt/collector

