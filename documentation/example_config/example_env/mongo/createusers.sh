#!/bin/bash

echo "##################################################
=> Create MongoDB user for environment: ${APP_ENV}
##################################################"



if [ "$APP_ENV" == "testing" ]; then
  # Admin User
  MONGODB_ADMIN_USER=${TST_MONGO_INITDB_ROOT_USERNAME}
  MONGODB_ADMIN_PASS=${TST_MONGO_INITDB_ROOT_PASSWORD}

  # Application Database User
  MONGODB_APPLICATION_DATABASE=${TST_MONGODB_DATABASE}
  MONGODB_APPLICATION_USER=${TST_MONGODB_USERNAME}
  MONGODB_APPLICATION_PASS=${TST_MONGODB_PASSWORD}

elif [ "$APP_ENV" == "development" ]; then
  # Admin User
  MONGODB_ADMIN_USER=${DEV_MONGO_INITDB_ROOT_USERNAME}
  MONGODB_ADMIN_PASS=${DEV_MONGO_INITDB_ROOT_PASSWORD}

  # Application Database User
  MONGODB_APPLICATION_DATABASE=${DEV_MONGODB_DATABASE}
  MONGODB_APPLICATION_USER=${DEV_MONGODB_USERNAME}
  MONGODB_APPLICATION_PASS=${DEV_MONGODB_PASSWORD}

else # Production
  # Admin User
  MONGODB_ADMIN_USER=${MONGO_INITDB_ROOT_USERNAME}
  MONGODB_ADMIN_PASS=${MONGO_INITDB_ROOT_PASSWORD}

  # Application Database User
  MONGODB_APPLICATION_DATABASE=${MONGODB_DATABASE}
  MONGODB_APPLICATION_USER=${MONGODB_USERNAME}
  MONGODB_APPLICATION_PASS=${MONGODB_PASSWORD}
fi


 
# Wait for MongoDB to boot
RET=1
while [[ RET -ne 0 ]]; do
    echo "=> Waiting for confirmation of MongoDB service startup..."
    sleep 1
    mongo admin --eval "help" >/dev/null 2>&1
    RET=$?
done
 
# Create the admin user
echo "=> Creating admin user with a password in MongoDB"
mongo admin --eval "db.createUser({user: '$MONGODB_ADMIN_USER', pwd: '$MONGODB_ADMIN_PASS', roles:[{role:'root',db:'admin'}]});" || command_failed=1

if [ ${command_failed:-0} -eq 1 ]
then
 echo "Could not create admin user. Continue."
fi
 
sleep 1
 
# If we've defined the MONGODB_APPLICATION_DATABASE environment variable and it's a different database
# than admin, then create the user for that database.
# First it authenticates to Mongo using the admin user it created above.
# Then it switches to the REST API database and runs the createUser command 
# to actually create the user and assign it to the database.
if [ "$MONGODB_APPLICATION_DATABASE" != "admin" ]; then
    echo "=> Creating an ${MONGODB_APPLICATION_USER} user in ${MONGODB_APPLICATION_DATABASE} with a password in MongoDB"
    mongo admin -u $MONGODB_ADMIN_USER -p $MONGODB_ADMIN_PASS << EOF
use $MONGODB_APPLICATION_DATABASE
db.createUser({user: '$MONGODB_APPLICATION_USER', pwd: '$MONGODB_APPLICATION_PASS', roles:[{role:'dbOwner', db:'$MONGODB_APPLICATION_DATABASE'}]})
EOF
fi
 
sleep 1
 
# If everything went well, add a file as a flag so we know in the future to not re-create the
# users if we're recreating the container (provided we're using some persistent storage)
echo "=> Done!"
touch /data/db/.mongodb_password_set
 
echo "========================================================================"
echo "You can now connect to the admin MongoDB server using:"
echo ""
echo "    mongo admin -u $MONGODB_ADMIN_USER -p $MONGODB_ADMIN_PASS --host <host> --port <port>"
echo ""
echo "Please remember to change the admin password as soon as possible!"
echo "========================================================================"