# -*- coding: utf-8 -*-
# This file is part of FirmwareDroid - https://github.com/FirmwareDroid/FirmwareDroid/blob/main/LICENSE.md
# See the file 'LICENSE' for copying permission.
import datetime
import os
import shutil
import uuid
import secrets
from jinja2 import Environment, FileSystemLoader
from secrets import token_bytes
from base64 import b64encode
import argparse

TEMPLATE_FOLDER = "templates/"
TEMPLATE_ENV = Environment(loader=FileSystemLoader(TEMPLATE_FOLDER))
REDIS_CONFIG_NAME = "redis.conf"
REDIS_CONFIG_PATH = "env/redis/"
MONGO_CONFIG_PATH = "env/mongo/"
NGINX_CONFIG_NAME = "app.conf"
NGINX_CONFIG_PATH = "env/nginx/"
ENV_FILE_NAME = "env"
REPLICA_SET_SCRIPT_NAME = "mongo_replica_set_setup.sh"
BLOB_STORAGE_NAME = "blob_storage/"


class FmdEnvironment:
    """
    Class that contains the env configuration for the FirmwareDroid service.
    """
    script_file_path = os.path.dirname(os.path.realpath(__file__))
    blob_storage_name = BLOB_STORAGE_NAME
    blob_storage_path = os.path.join(script_file_path, blob_storage_name)
    app_env = None
    app_debug = None
    local_storage_path = None
    local_storage_path_secondary = None
    local_mongo_db_path_node1 = None
    redis_config_path = None
    redis_password = None
    redis_port = None
    mongodb_database_name = None
    mongodb_auth_src = None
    mongodb_port = None
    mongo_db_replicat_set = None
    mongodb_initdb_root_username = None
    mongodb_initdb_root_password = None
    mongodb_username = None
    mongodb_password = None
    mongo_db_hostname = None
    mass_import_number_of_threads = None
    domain_name = None
    api_title = None
    api_version = None
    api_description = None
    api_prefix = None
    api_doc_folder = None
    cors_additional_host = None
    django_secret_key = None
    django_sqlite_database_path = None
    use_defaults = False
    django_superuser_password = None
    django_superuser_username = None
    django_superuser_email = None

    def __init__(self, use_defaults):
        self.use_defaults = use_defaults

    def _get_environment(self):
        print("Setting up environment...")
        while True:
            if self.use_defaults:
                user_input = "no"
            else:
                user_input = input("Enable production mode? (default: no) yes/no: ") or "no"

            if user_input.lower() == "yes":
                self.app_env = "production"
                self.app_debug = False
                print("Production mode enabled. Debugging logs disabled.")
                break
            elif user_input.lower() == "no":
                self.app_env = "development"
                self.app_debug = True
                print("Development mode enabled. Debugging logs active.")
                break

    def _get_blob_storage(self):
        print("# Setting up blob storage...")
        while True:
            self.redis_config_path = os.path.join(self.script_file_path, REDIS_CONFIG_PATH, REDIS_CONFIG_NAME)
            self.redis_password = uuid.uuid4()
            self.redis_port = 6379
            if self.use_defaults:
                user_input = self.blob_storage_path
            else:
                user_input = input(f"Where do you want to store blob data? "
                                   f"(default: '{self.blob_storage_path}'):") or self.blob_storage_path
            if user_input:
                self.blob_storage_path = user_input

            if not os.path.exists(self.blob_storage_path):
                try:
                    os.mkdir(self.blob_storage_path)
                except Exception as err:
                    print(err)
                    continue
            self.local_storage_path = os.path.join(self.blob_storage_path, "00_file_storage")
            self.local_storage_path_secondary = os.path.join(self.blob_storage_path, "01_file_storage")
            self.local_mongo_db_path_node1 = os.path.join(self.blob_storage_path, "mongo_database")
            print(f"Set blob storage to: {user_input}")
            break

    def _get_mongodb_settings(self):
        print("Setting up database config...")
        self.mongodb_database_name = "FirmwareDroid"
        self.mongodb_auth_src = "admin"
        self.mongodb_port = 27017
        self.mongo_db_replicat_set = "mongo_cluster_1"
        self.mongodb_initdb_root_username = "mongodbroot"
        self.mongodb_initdb_root_password = uuid.uuid4()
        self.mongodb_username = "mongodbuser"
        self.mongodb_password = uuid.uuid4()
        self.mongo_db_hostname = "mongo-db-1"

    def _get_web_config(self):
        print("Setting up web config...")
        self.mass_import_number_of_threads = 3
        default_domain_name = "fmd.localhost"
        default_companion_domain_name = "fmd-aosp.init-lab.ch"
        if self.use_defaults:
            user_input = default_domain_name
        else:
            user_input = input(f"Please, enter a valid domain name "
                               f"(default: '{default_domain_name}'):") or default_domain_name
        if user_input:
            self.domain_name = user_input
        else:
            self.domain_name = default_domain_name
        self.api_title = "FirmwareDroid REST API"
        self.api_version = 1.0
        self.api_description = "REST API documentation for the FirmwareDroid service"
        self.api_prefix = "/api"
        self.api_doc_folder = "/docs"
        self.cors_additional_host = default_companion_domain_name
        self.django_secret_key = secrets.token_hex(100)
        self.django_sqlite_database_path = os.path.join("/var/www/", BLOB_STORAGE_NAME, "django_database/db.sqlite3")
        self.django_superuser_username = "fmd-admin"
        self.django_superuser_password = uuid.uuid4()
        self.django_superuser_email = "fmd-admin@fmd.localhost"

    def create_env_file(self):
        self._get_environment()
        self._get_blob_storage()
        self._get_mongodb_settings()
        self._get_web_config()
        template = TEMPLATE_ENV.get_template(ENV_FILE_NAME)
        content = template.render(
            app_env=self.app_env,
            app_debug=self.app_debug,
            local_storage_path=self.local_storage_path,
            local_storage_path_secondary=self.local_storage_path_secondary,
            local_mongo_db_path_node1=self.local_mongo_db_path_node1,
            redis_config_path=self.redis_config_path,
            redis_password=self.redis_password,
            redis_port=self.redis_port,
            mongodb_database_name=self.mongodb_database_name,
            mongodb_auth_src=self.mongodb_auth_src,
            mongodb_port=self.mongodb_port,
            mongo_db_replicat_set=self.mongo_db_replicat_set,
            mongodb_initdb_root_username=self.mongodb_initdb_root_username,
            mongodb_initdb_root_password=self.mongodb_initdb_root_password,
            mongodb_username=self.mongodb_username,
            mongodb_password=self.mongodb_password,
            mongo_db_hostname=self.mongo_db_hostname,
            mass_import_number_of_threads=self.mass_import_number_of_threads,
            domain_name=self.domain_name,
            api_title=self.api_title,
            api_version=self.api_version,
            api_description=self.api_description,
            api_prefix=self.api_prefix,
            api_doc_folder=self.api_doc_folder,
            cors_additional_host=self.cors_additional_host,
            django_secret_key=self.django_secret_key,
            django_sqlite_database_path=self.django_sqlite_database_path,
            django_superuser_password=self.django_superuser_password,
            django_superuser_username=self.django_superuser_username,
            django_superuser_email=self.django_superuser_email,
        )
        out_file_path = os.path.join(self.script_file_path, "." + ENV_FILE_NAME)
        with open(out_file_path, mode="w", encoding="utf-8") as out_file:
            out_file.write(content)
            print("Created .env file")


def setup_environment_variables(use_defaults):
    env_instance = FmdEnvironment(use_defaults=use_defaults)
    env_instance.create_env_file()
    return env_instance


def setup_nginx(env_instance):
    """
    Uses an config template to create a valid runtime configuration for nginx.

    :param env_instance: class:`FmdEnvironment` - with parameters set for the web domain.
    """
    nginx_path = os.path.join(env_instance.script_file_path, NGINX_CONFIG_PATH)
    if not os.path.exists(nginx_path):
        os.makedirs("./env/nginx")
        os.makedirs(f"./env/nginx/live/{env_instance.domain_name}")

    template = TEMPLATE_ENV.get_template(NGINX_CONFIG_NAME)
    content = template.render(
        domain_name=env_instance.domain_name
    )
    out_file_path = os.path.join(env_instance.script_file_path, NGINX_CONFIG_PATH, NGINX_CONFIG_NAME)
    with open(out_file_path, mode="w", encoding="utf-8") as out_file:
        out_file.write(content)
    generate_certificate(env_instance)
    print("Completed nginx env setup.")


def generate_certificate(env_instance):
    """
    Generates a self-signed x509 certificate for the nginx service. This certificate is used for the webserver as
    default certificate.

   :param env_instance: class:`FmdEnvironment` - with parameters set for the web domain.
    """
    from cryptography import x509
    from cryptography.hazmat.backends import default_backend
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives.asymmetric import rsa
    from cryptography.x509.oid import NameOID
    from cryptography.hazmat.primitives import hashes

    # Generate a new private key
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
        backend=default_backend()
    )

    # Create a subject for the certificate
    subject = x509.Name([
        x509.NameAttribute(NameOID.COUNTRY_NAME, "CH"),
        x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, "Zurich"),
        x509.NameAttribute(NameOID.LOCALITY_NAME, "Winterthur"),
        x509.NameAttribute(NameOID.ORGANIZATION_NAME, "Zurich University of Applied Sciences"),
        x509.NameAttribute(NameOID.COMMON_NAME, env_instance.domain_name),
    ])

    # Create a certificate
    certificate = x509.CertificateBuilder().subject_name(
        subject
    ).issuer_name(
        subject
    ).public_key(
        private_key.public_key()
    ).serial_number(
        x509.random_serial_number()
    ).not_valid_before(
        datetime.datetime.utcnow()
    ).not_valid_after(
        datetime.datetime.utcnow() + datetime.timedelta(days=1024)
    ).sign(private_key, hashes.SHA256(), default_backend())

    # Serialize the private key to PEM format
    private_key_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.TraditionalOpenSSL,
        encryption_algorithm=serialization.NoEncryption()
    )

    # Serialize the certificate to PEM format
    certificate_pem = certificate.public_bytes(
        encoding=serialization.Encoding.PEM
    )

    cert_out_path = os.path.join(env_instance.script_file_path, NGINX_CONFIG_PATH, f"live/{env_instance.domain_name}/")
    privkey_pem_path = os.path.join(cert_out_path, 'privkey.pem')
    cert_pem_path = os.path.join(cert_out_path, 'certificate.pem')
    with open(privkey_pem_path, 'wb') as f:
        f.write(private_key_pem)

    with open(cert_pem_path, 'wb') as f:
        f.write(certificate_pem)


def setup_redis(env_instance):
    """
    Uses an config template to create a valid runtime configuration for redis. Writes the config file into the env
    directory.

    :param env_instance: class:`FmdEnvironment` - with parameters set for redis.

    """
    redis_path = os.path.join(env_instance.script_file_path, REDIS_CONFIG_PATH)
    if not os.path.exists(redis_path):
        os.makedirs("./env/redis")
    template = TEMPLATE_ENV.get_template(REDIS_CONFIG_NAME)
    content = template.render(
        redis_password=env_instance.redis_password
    )
    output_file_path = os.path.join(env_instance.script_file_path, REDIS_CONFIG_PATH, REDIS_CONFIG_NAME)
    with open(output_file_path, 'w') as f:
        f.write(content)

    print("Completed redis env setup.")


def setup_mongo_env(env_instance):
    """
    Uses an config template to create a valid runtime configuration for mongodb. Write several config files into the
    mongo env directory.

    :param env_instance: class:`FmdEnvironment` - with parameters set for mongodb.
    """
    mongo_env_auth_path = "env/mongo/auth"
    mongo_env_init_path = "env/mongo/init"
    mongo_path = os.path.join(env_instance.script_file_path, MONGO_CONFIG_PATH)
    if not os.path.exists(mongo_path):
        os.makedirs("./" + mongo_env_auth_path)
        os.makedirs("./env/mongo/config")
        os.makedirs("./" + mongo_env_init_path)
    key_file_path = os.path.join(env_instance.script_file_path, mongo_env_auth_path, "cluster.key")
    cluster_key = b64encode(token_bytes(756)).decode()
    with open(key_file_path, mode="w", encoding="utf-8") as out_file:
        out_file.write(cluster_key)
        print("Created cluster key")
    os.chmod(key_file_path, 400)
    print("Completed mongodb env setup. Ready for first startup!")
    replica_setup_source_path = os.path.join(env_instance.script_file_path, TEMPLATE_FOLDER, REPLICA_SET_SCRIPT_NAME)
    shutil.copy(replica_setup_source_path, mongo_env_init_path)


def main():
    parser = argparse.ArgumentParser(prog='setup',
                                     description="A cli tool to setup FirmwareDroid")
    parser.add_argument("-d", "--fmd-domain-name",
                        type=str,
                        default="fmd.localhost",
                        required=False,
                        help="Specifies the domain name used to setup FirmwareDroid")
    args = parser.parse_args()

    env_path = os.path.join("./.env")
    if os.path.exists(env_path):
        print(".env file already exists!")
        exit(1)
    env_instance = setup_environment_variables(use_defaults=True)
    setup_nginx(env_instance)
    setup_redis(env_instance)
    setup_mongo_env(env_instance)


if __name__ == "__main__":
    main()
