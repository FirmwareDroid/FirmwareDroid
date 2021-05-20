#!/bin/bash
sleep 10

if [ "$APP_ENV" == "testing" ]; then
  # Admin User
  MONGODB_ADMIN_USER=${TST_MONGO_INITDB_ROOT_USERNAME}
  MONGODB_ADMIN_PASS=${TST_MONGO_INITDB_ROOT_PASSWORD}
elif [ "$APP_ENV" == "development" ]; then
  # Admin User
  MONGODB_ADMIN_USER=${DEV_MONGO_INITDB_ROOT_USERNAME}
  MONGODB_ADMIN_PASS=${DEV_MONGO_INITDB_ROOT_PASSWORD}
else # Production
  # Admin User
  MONGODB_ADMIN_USER=${MONGO_INITDB_ROOT_USERNAME}
  MONGODB_ADMIN_PASS=${MONGO_INITDB_ROOT_PASSWORD}
fi

mongo admin -u ${MONGODB_ADMIN_USER} -p ${MONGODB_ADMIN_PASS} --host mongo-db-1:27017 <<EOF
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
EOF


#,
#    {
#      "_id": 1,
#      "host": "mongo-db-2:27017",
#      "priority": 0
#    },
#    {
#      "_id": 2,
#      "host": "mongo-db-3:27017",
#      "priority": 0
#    }

