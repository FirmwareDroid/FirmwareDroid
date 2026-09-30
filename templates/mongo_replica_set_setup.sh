#!/bin/bash
# -*- coding: utf-8 -*-
# This file is part of FirmwareDroid - https://github.com/FirmwareDroid/FirmwareDroid/blob/main/LICENSE.md
# See the file 'LICENSE' for copying permission.

chmod 400 /etc/mongodb/cluster.key 2>/dev/null || true

if [ -f /config/runtime.env ]; then
    set -a
    # shellcheck disable=SC1090
    . /config/runtime.env
    set +a
fi

MONGO_ADMIN_USER=${MONGO_INITDB_ROOT_USERNAME}
MONGO_ADMIN_PASS=${MONGO_INITDB_ROOT_PASSWORD}
MONGO_APPLICATION_DATABASE=${MONGODB_DATABASE_NAME:-FirmwareDroid}
MONGO_APPLICATION_USER=${MONGODB_USERNAME}
MONGO_APPLICATION_PASS=${MONGODB_PASSWORD}

echo "################################################## Setup Replica set"
(
    until mongosh mongodb://127.0.0.1:27017/admin -u "${MONGO_ADMIN_USER}" -p "${MONGO_ADMIN_PASS}" --quiet --eval "db.adminCommand('ping')" >/dev/null 2>&1; do
        sleep 2
    done

    mongosh mongodb://127.0.0.1:27017/admin -u "${MONGO_ADMIN_USER}" -p "${MONGO_ADMIN_PASS}" <<'EOF'
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
try {
  rs.initiate(cfg, { force: true });
} catch(e) {
  print("rs.initiate notice: " + e);
}
EOF

    until mongosh mongodb://127.0.0.1:27017/admin -u "${MONGO_ADMIN_USER}" -p "${MONGO_ADMIN_PASS}" --quiet --eval "db.hello().isWritablePrimary" 2>/dev/null | grep -q true; do
        sleep 1
    done

    mongosh mongodb://127.0.0.1:27017/admin -u "${MONGO_ADMIN_USER}" -p "${MONGO_ADMIN_PASS}" <<EOF
db.getMongo().setReadPref('nearest');
try {
  db.createUser({user: '$MONGO_ADMIN_USER', pwd: '$MONGO_ADMIN_PASS', roles: [ "root" ]});
} catch(e) {
  try { db.updateUser('$MONGO_ADMIN_USER', {pwd: '$MONGO_ADMIN_PASS'}); } catch(e2) {}
}
try {
  db.createUser({user: '$MONGO_APPLICATION_USER', pwd: '$MONGO_APPLICATION_PASS', roles:[{role:'dbOwner', db:'$MONGO_APPLICATION_DATABASE'}]});
} catch(e) {
  try { db.updateUser('$MONGO_APPLICATION_USER', {pwd: '$MONGO_APPLICATION_PASS'}); } catch(e2) {}
}
var appDb = db.getSiblingDB('$MONGO_APPLICATION_DATABASE');
try {
  appDb.createCollection("init");
} catch(e) {}
try {
  appDb.createUser({user: '$MONGO_APPLICATION_USER', pwd: '$MONGO_APPLICATION_PASS', roles:[{role:'dbOwner', db:'$MONGO_APPLICATION_DATABASE'}]});
} catch(e) {
  try { appDb.updateUser('$MONGO_APPLICATION_USER', {pwd: '$MONGO_APPLICATION_PASS'}); } catch(e2) {}
}
EOF

    echo "=> Created MongoDB user for environment: ${APP_ENV:-production}
=> MONGODB_ADMIN_USER: ${MONGO_ADMIN_USER}
=> MONGODB_APPLICATION_USER: ${MONGO_APPLICATION_USER}
=> MONGODB_APPLICATION_DATABASE: ${MONGO_APPLICATION_DATABASE}
Finished mongodb replica setup
##################################################"
) &
