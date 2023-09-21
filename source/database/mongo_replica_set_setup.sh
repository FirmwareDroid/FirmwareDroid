#!/bin/bash
# -*- coding: utf-8 -*-
# This file is part of FirmwareDroid - https://github.com/FirmwareDroid/FirmwareDroid/blob/main/LICENSE.md
# See the file 'LICENSE' for copying permission.
sleep 10

# Root User
MONGODB_ADMIN_USER=${MONGO_INITDB_ROOT_USERNAME}
MONGODB_ADMIN_PASS=${MONGO_INITDB_ROOT_PASSWORD}
# Application Database User
MONGODB_APPLICATION_DATABASE=${MONGODB_DATABASE}
MONGODB_APPLICATION_USER=${MONGODB_USERNAME}
MONGODB_APPLICATION_PASS=${MONGODB_PASSWORD}

echo "##################################################"
echo "Setup Replica set"
mongosh mongodb://${MONGODB_ADMIN_USER}:${MONGODB_ADMIN_PASS}@mongo-db-1:27017/admin <<EOF
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
db.getMongo().setReadPref('nearest');
use ${MONGODB_APPLICATION_DATABASE}
db.createUser({user: '$MONGODB_APPLICATION_USER', pwd: '$MONGODB_APPLICATION_PASS', roles:[{role:'dbOwner', db:'$MONGODB_APPLICATION_DATABASE'}]})
EOF
echo "Completed Replica setup"
echo "##################################################
=> Create MongoDB user for environment: ${APP_ENV}
=> MONGODB_ADMIN_USER: ${MONGODB_ADMIN_USER}
=> MONGODB_APPLICATION_USER: ${MONGODB_APPLICATION_USER}
=> MONGODB_APPLICATION_DATABASE: ${MONGODB_APPLICATION_DATABASE}
##################################################"
if [ "${MONGODB_APPLICATION_DATABASE}" != "admin" ]; then
    echo "=> Creating an '${MONGODB_APPLICATION_USER}' user in '${MONGODB_APPLICATION_DATABASE}' with a password in MongoDB"
    mongosh mongodb://"${MONGODB_ADMIN_USER}":"${MONGODB_ADMIN_PASS}"@mongo-db-1:27017/admin << EOF
use ${MONGODB_APPLICATION_DATABASE}
db.createCollection("init")
db.createUser({user: '$MONGODB_APPLICATION_USER', pwd: '$MONGODB_APPLICATION_PASS', roles:[{role:'dbOwner', db:'$MONGODB_APPLICATION_DATABASE'}]})
EOF
fi
echo "Finished mongo setup"