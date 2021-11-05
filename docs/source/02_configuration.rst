Configuration
=============
By default FirmwareDroid has configured three environments--production, development, and testing. This is subject to
change and we will move to docker secrets in a future versions of FirmwareDroid. Currently the complete configuration
of FirmwareDroid can be done via environment variables and some config files.

FirmwareDroid expects an ``/FirmwareDroid/.env`` file in the root folder and a folder ``/FirmwareDroid/env/`` with
some specific config files.

This is an example environment config (.env) for all environments::

    ##########################################################################################
    # Global Configuration
    # Used for production, development and testing
    ##########################################################################################
    # Environment - production, development, testing
    FLASK_ENV=development
    FLASK_DEBUG=True
    APP_ENV=development
    APP_DEBUG=True
    APP_PORT=5000


    ##########################################################################################
    # Production Configuration
    #
    ##########################################################################################
    # Docker-Compose
    LOCAL_STORAGE_PATH=./00_file_storage
    LOCAL_MONGO_DB_PATH_NODE1=./mongodb_data/node1/
    ELASTIC_SEARCH_DB_PATH=./elastic_search_data/data/
    ELASTIC_SEARCH_CONFIG_PATH=./elastic_search_data/config/

    # Redis-Database
    REDIS_DB_PATH=./redis-data
    REDIS_CONFIG_PATH=./env/redis/redis.conf

    # RQ-Dashboard
    RQ_DASHBOARD_REDIS_URL=redis://redis:6379
    RQ_DASHBOARD_PASSWORD=sOmE_sEcUrE_pAsS_sOmE_sEcUrE_pAsS
    RQ_DASHBOARD_USERNAME=redis-admin
    REDIS_HOST_PORT=redis:6379

    # Mongo-Database
    MONGO_INITDB_DATABASE=FirmwareDroid
    MONGODB_APPLICATION_DATABASE=FirmwareDroid
    MONGO_INITDB_ROOT_USERNAME=mongodbroot
    MONGO_INITDB_ROOT_PASSWORD=your_mongodb_root_password
    MONGODB_USERNAME=mongodbuser
    MONGODB_PASSWORD=your_mongodb_user_password
    MONGODB_HOSTNAME=mongo-db-1
    MONGODB_DATABASE=FirmwareDroid
    MONGODB_PORT=27017
    MONGODB_REPLICA_SET=mongo_cluster_1

    # Web
    APP_DATA_FOLDER=./file_store/ # DO NOT CHANGE
    BASIC_AUTH_USERNAME=admin
    BASIC_AUTH_PASSWORD=CHANGE_THIS_SECRET
    BASIC_AUTH_FORCE=True
    JWT_SECRET_KEY=JWT_TEST_TOKEN_CHANGE_THIS
    FLASK_ADMIN_PW=CHANGE_THIS_SECRET
    FLASK_ADMIN_MAIL=suth@zhaw.ch
    FLASK_ADMIN_USERNAME=admin
    MASS_IMPORT_NUMBER_OF_THREADS=3
    DOMAIN_NAME=firmwaredroid.cloudlab.zhaw.ch

    # Web - Swagger
    API_TITLE="FirmwareDroid API - Production"
    API_VERSION=1.0
    API_DESCRIPTION="REST API documentation for the FirmwareDroid tool"
    API_PREFIX=/api
    API_DOC_FOLDER=/docs

    # Web - Mail
    MAIL_SERVER=smtp.office365.com
    MAIL_PORT=587
    MAIL_USERNAME=example@outlook.com
    MAIL_PASSWORD=CHANGE_THIS_SECRET
    MAIL_DEFAULT_SENDER=example@outlook.com
    MAIL_SECRET_KEY=CHANGE_THIS_SECRET
    MAIL_SALT=SaltAndPepperAreTheBest

    # Certbot
    CERT_WEBROOT_PATH=/var/www/certbot
    CERT_EMAIL=info.init@zhaw.ch
    CERT_DOMAIN=firmwaredroid.cloudlab.zhaw.ch

    ##########################################################################################
    # Development Configuration
    #
    ##########################################################################################
    # Docker-Compose
    DEV_LOCAL_STORAGE_PATH=./00_file_storage
    DEV_LOCAL_MONGO_DB_PATH_NODE1=./mongodb_data/node1/
    DEV_ELASTIC_SEARCH_DB_PATH=./elastic_search_data/data/
    DEV_ELASTIC_SEARCH_CONFIG_PATH=./elastic_search_data/config/

    # Redis-Database
    DEV_REDIS_DB_PATH=./redis-data
    DEV_REDIS_CONFIG_PATH=./env/redis/redis.conf

    # RQ-Dashboard
    DEV_RQ_DASHBOARD_REDIS_URL=redis://redis:6379
    DEV_RQ_DASHBOARD_PASSWORD=sOmE_sEcUrE_pAsS_sOmE_sEcUrE_pAsS
    DEV_RQ_DASHBOARD_USERNAME=redis-admin
    DEV_REDIS_HOST_PORT=redis:6379

    # Mongo-Database
    DEV_MONGO_INITDB_DATABASE=DevFirmwareDroid
    DEV_MONGO_INITDB_ROOT_USERNAME=Devmongodbroot
    DEV_MONGO_INITDB_ROOT_PASSWORD=your_mongodb_root_password
    DEV_MONGODB_USERNAME=Devmongodbuser
    DEV_MONGODB_PASSWORD=your_mongodb_user_password
    DEV_MONGODB_HOSTNAME=mongo-db-1
    DEV_MONGODB_DATABASE=DevFirmwareDroid
    DEV_MONGODB_PORT=27017
    DEV_MONGODB_REPLICA_SET=mongo_cluster_1

    # Web
    DEV_APP_DATA_FOLDER=./file_store/
    DEV_BASIC_AUTH_USERNAME=admin
    DEV_BASIC_AUTH_PASSWORD=CHANGE_THIS_SECRET
    DEV_BASIC_AUTH_FORCE=True
    DEV_JWT_SECRET_KEY=JWT_TEST_TOKEN_CHANGE_THIS
    DEV_FLASK_ADMIN_PW=CHANGE_THIS_SECRET
    DEV_FLASK_ADMIN_MAIL=example@example.ch
    DEV_FLASK_ADMIN_USERNAME=devAdmin
    DEV_MASS_IMPORT_NUMBER_OF_THREADS=3
    DEV_DOMAIN_NAME=firmwaredroid.cloudlab.zhaw.ch

    # Web - Swagger
    DEV_API_TITLE="FirmwareDroid API - Development"
    DEV_API_VERSION=1.0
    DEV_API_DESCRIPTION="REST API documentation for the FirmwareDroid tool"
    DEV_API_PREFIX=/api
    DEV_API_DOC_FOLDER=/docs

    # Web - Mail
    DEV_MAIL_SERVER=smtp.office365.com
    DEV_MAIL_PORT=587
    DEV_MAIL_USERNAME=example@outlook.com
    DEV_MAIL_PASSWORD=CHANGE_THIS_SECRET
    DEV_MAIL_DEFAULT_SENDER=example@outlook.com
    DEV_MAIL_SECRET_KEY=SUPERaweseomeSECRET
    DEV_MAIL_SALT=SaltAndPepperAreTheBest


    ##########################################################################################
    # Testing Configuration
    #
    ##########################################################################################
    # Docker-Compose
    TST_LOCAL_STORAGE_PATH=./00_file_storage
    TST_LOCAL_MONGO_DB_PATH_NODE1=./mongodb_data/node1/
    TST_ELASTIC_SEARCH_DB_PATH=./elastic_search_data/data/
    TST_ELASTIC_SEARCH_CONFIG_PATH=./elastic_search_data/config/

    # Redis-Database
    TST_REDIS_DB_PATH=./redis-data
    TST_REDIS_CONFIG_PATH=./env/redis/redis.conf

    # RQ-Dashboard
    TST_RQ_DASHBOARD_REDIS_URL=redis://redis:6379
    TST_RQ_DASHBOARD_PASSWORD=sOmE_sEcUrE_pAsS_sOmE_sEcUrE_pAsS
    TST_RQ_DASHBOARD_USERNAME=redis-admin
    TST_REDIS_HOST_PORT=redis:6379

    # Mongo-Database
    TST_MONGO_INITDB_DATABASE=TestFirmwareDroid
    TST_MONGODB_APPLICATION_DATABASE=TestFirmwareDroid
    TST_MONGO_INITDB_ROOT_USERNAME=Testmongodbroot
    TST_MONGO_INITDB_ROOT_PASSWORD=your_mongodb_root_password
    TST_MONGODB_USERNAME=Testmongodbuser
    TST_MONGODB_PASSWORD=your_mongodb_user_password
    TST_MONGODB_HOSTNAME=mongo-db-1
    TST_MONGODB_DATABASE=TestFirmwareDroid
    TST_MONGODB_PORT=27017
    TST_MONGODB_REPLICA_SET=mongo_cluster_1

    # Web
    TST_APP_DATA_FOLDER=./file_store/
    TST_BASIC_AUTH_USERNAME=admin
    TST_BASIC_AUTH_PASSWORD=CHANGE_THIS_SECRET
    TST_BASIC_AUTH_FORCE=True
    TST_JWT_SECRET_KEY=JWT_TEST_TOKEN_CHANGE_THIS
    TST_FLASK_ADMIN_USERNAME=tstAdmin
    TST_FLASK_ADMIN_PW=CHANGE_THIS_SECRET
    TST_FLASK_ADMIN_MAIL=TEST@FIRMWAREDROID.COM
    TST_MASS_IMPORT_NUMBER_OF_THREADS=3
    TST_DOMAIN_NAME=firmwaredroid.cloudlab.zhaw.ch

    # Web - Swagger
    TST_API_TITLE="FirmwareDroid API - Testing"
    TST_API_VERSION=1.0
    TST_API_DESCRIPTION="TEST REST API documentation for the FirmwareDroid tool"
    TST_API_PREFIX=/api
    TST_API_DOC_FOLDER=/docs

    # Web - Mail
    TST_MAIL_SERVER=smtp.office365.com
    TST_MAIL_PORT=587
    TST_MAIL_USERNAME=example@outlook.com
    TST_MAIL_PASSWORD=CHANGE_THIS_SECRET
    TST_MAIL_DEFAULT_SENDER=example@outlook.com
    TST_MAIL_SECRET_KEY=SUPERaweseomeSECRET
    TST_MAIL_SALT=SaltAndPepperAreTheBest

::

The ``/FirmwareDroid/env/`` should contain the following folders, subfolders, and config-files:
    * /elasticsearch/config
        * elasticsearch.yml
        * elasticsearch_node_1.yml
        * elasticsearch_node_2.yml
        * elasticsearch_node_3.yml
    * /mongo/
        * /auth/
            * cluster.key
    * /init/
        * createusers.sh
    * /mongo-connector/
        * mongo-connector-config.json
    * /nginx/
        * app.conf
        * /ssl/live/firmwaredroid.cloudlab.zhaw.ch
            * certificate.pem
            * privkey.pem
    * /redis/
        * redis.conf




