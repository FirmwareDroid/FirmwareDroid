#!/bin/bash
# -*- coding: utf-8 -*-
# This file is part of FirmwareDroid - https://github.com/FirmwareDroid/FirmwareDroid/blob/main/LICENSE.md
# See the file 'LICENSE' for copying permission.
chmod 400 /etc/mongodb/cluster.key

MONGO_ADMIN_USER=${MONGO_INITDB_ROOT_USERNAME}
MONGO_ADMIN_PASS=${MONGO_INITDB_ROOT_PASSWORD}
MONGO_APPLICATION_DATABASE=${MONGODB_DATABASE_NAME}
MONGO_APPLICATION_USER=${MONGODB_USERNAME}
MONGO_APPLICATION_PASS=${MONGODB_PASSWORD}

echo "################################################## Setup Replica set"
sleep 10 && mongosh mongodb://mongo-db-1:27017/admin -u "${MONGO_INITDB_ROOT_USERNAME}" -p "${MONGO_INITDB_ROOT_PASSWORD}"<<EOF &
var cfg = {
  "_id": "mongo_cluster_1",
  "version": 1,
  "members": [
    {
      "_id": 0,
      "host": "mongo-db-1:27017",
      "priority": 2
    }
  ]
};
rs.initiate(cfg, { force: true });
rs.reconfig(cfg, { force: true });
rs.status()
rs.conf()
db.getMongo().setReadPref('nearest');
db.createUser({user: '$MONGO_ADMIN_USER', pwd: '$MONGO_ADMIN_PASS', roles: [ "root" ]})
db.createUser({user: '$MONGO_APPLICATION_USER', pwd: '$MONGO_APPLICATION_PASS', roles:[{role:'dbOwner', db:'$MONGO_APPLICATION_DATABASE'}]})
use ${MONGO_APPLICATION_DATABASE}
db.createCollection("init")
db.createUser({user: '$MONGO_APPLICATION_USER', pwd: '$MONGO_APPLICATION_PASS', roles:[{role:'dbOwner', db:'$MONGO_APPLICATION_DATABASE'}]})
EOF

echo "=> Created MongoDB user for environment: ${APP_ENV}
=> MONGODB_ADMIN_USER: ${MONGO_ADMIN_USER}
=> MONGODB_APPLICATION_USER: ${MONGO_APPLICATION_USER}
=> MONGODB_APPLICATION_DATABASE: ${MONGO_APPLICATION_DATABASE}
Finished mongodb replica setup
##################################################"