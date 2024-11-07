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
FMD_WEB_CLIENT_ENV_FILE_NAME = "EnvConfig.js"
FMD_WEB_CLIENT_ENV_PATH = "firmware-droid-client/src/"


def is_valid_domain_name(domain_name):
    """
    Checks if the given domain name is valid.

    :param domain_name: str - domain name

    :return: bool - True if the domain name is valid, False otherwise
    """
    import re
    if re.match(r"^([a-z0-9]+(-[a-z0-9]+)*\.)+[a-z]{2,}$", domain_name):
        return True
    else:
        return False


def _create_directory(path):
    """
    Creates a directory if it does not exist.
    :param path: str - path to the directory
    :return: bool - True if the directory exists or was created, False otherwise
    """
    if not os.path.exists(path):
        try:
            os.mkdir(path)
        except Exception as err:
            print(err)
            return False
    return True


def is_valid_memory_limit(memory_limit):
    """
    Checks if the given memory limit is valid.

    :param memory_limit: str - memory limit

    :return: bool - True if the memory limit is valid, False otherwise
    """
    import re
    if re.match(r"^[0-9]+[KMGTP]B$", memory_limit):
        return True
    else:
        return False


def is_valid_cpu_limit(cpu_limit):
    """
    Checks if the given cpu limit is valid.

    :param cpu_limit: str - cpu limit

    :return: bool - True if the cpu limit is valid, False otherwise
    """
    import re
    if re.match(r"^[0-9]+(\.[0-9]+)?$", cpu_limit):
        return True
    else:
        return False


class FmdEnvironment:
    """
    Class that contains the env configuration for the FirmwareDroid service.
    """
    script_file_path = os.path.dirname(os.path.realpath(__file__))
    blob_storage_name = BLOB_STORAGE_NAME
    blob_storage_path = os.path.join(script_file_path, blob_storage_name)
    app_env = None
    app_debug = None
    local_storage_path_list = []
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
    django_sqlite_database_mount_path = None
    use_defaults = False
    django_superuser_password = None
    django_superuser_username = None
    django_superuser_email = None
    docker_memory_limit = None
    docker_memory_swap_limit = None
    docker_cpu_limit = None

    def __init__(self, use_defaults):
        self.use_defaults = use_defaults

    def _get_environment(self):
        """
        Asks the user for the environment configuration. If the user enters an invalid path, the user is asked again.
        """
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

    def _get_blob_storage_path(self):
        """
        Asks the user for the blob storage path or uses the default path.
        """
        self.blob_storage_path = os.path.join(self.script_file_path, self.blob_storage_name)
        if self.use_defaults:
            return self.blob_storage_path
        else:
            return input(f"Where do you want to store blob data? "
                         f"(default: '{self.blob_storage_path}'):") or self.blob_storage_path

    def _get_mongo_db_path(self):
        """
        Asks the user for the mongodb data path or uses the default path.
        """
        self.local_mongo_db_path_node1 = os.path.join(self.blob_storage_path, "mongo_database")
        if self.use_defaults:
            return self.local_mongo_db_path_node1
        else:
            return input(f"Where do you want to store the mongodb data? "
                         f"(default: '{self.local_mongo_db_path_node1}'):") or self.local_mongo_db_path_node1

    def _get_django_sqlite_database_mount_path(self):
        """
        Asks the user for the django sqlite database path or uses the default path.
        """
        self.django_sqlite_database_mount_path = os.path.join(self.blob_storage_path, "django_database/")
        if self.use_defaults:
            return self.django_sqlite_database_mount_path
        else:
            return input(f"Where do you want to store the django sqlite database? "
                         f"(default: '{self.django_sqlite_database_mount_path}'):") \
                or self.django_sqlite_database_mount_path

    def _get_blob_storage(self):
        """
        Asks the user for the blob storage configuration. If the user enters an invalid path, the user is asked again.
        """
        print("# Setting up blob storage...")
        while True:
            self.redis_config_path = os.path.join(self.script_file_path, REDIS_CONFIG_PATH, REDIS_CONFIG_NAME)
            self.redis_password = uuid.uuid4()
            self.redis_port = 6379

            self.blob_storage_path = self._get_blob_storage_path()
            if not _create_directory(self.blob_storage_path):
                continue

            for x in range(0, 10):
                self.local_storage_path_list.append(os.path.join(self.blob_storage_path, f"0{x}_file_storage"))
                if not _create_directory(self.local_storage_path_list[x]):
                    continue

            self.local_mongo_db_path_node1 = self._get_mongo_db_path()
            if not _create_directory(self.local_mongo_db_path_node1):
                continue

            self.django_sqlite_database_mount_path = self._get_django_sqlite_database_mount_path()
            if not _create_directory(os.path.dirname(self.django_sqlite_database_mount_path)):
                continue

            break

        print(f"Set blob storage to: {self.blob_storage_path}")
        print(f"Set mongo db path to: {self.local_mongo_db_path_node1}")

    def _get_mongodb_settings(self):
        print("Setting up database config...")
        self.mongodb_database_name = "FirmwareDroid"
        self.mongodb_auth_src = "admin"
        self.mongodb_port = 27017
        self.mongo_db_replicat_set = "mongo_cluster_1"
        self.mongo_db_hostname = "mongo-db-1"
        self.mongodb_initdb_root_username = "mongodbroot"
        self.mongodb_initdb_root_password = uuid.uuid4()
        self.mongodb_username = "mongodbuser"
        self.mongodb_password = uuid.uuid4()

    def _get_domain_name(self, default_domain_name):
        """
        Asks the user for a domain name. If the user enters an invalid domain name, the user is asked again.

        :param default_domain_name: str - default domain name

        :return: str - valid domain name
        """
        if self.use_defaults:
            return default_domain_name
        else:
            domain_name = input(f"Please, enter a valid domain name "
                                f"(default: '{default_domain_name}'):") or default_domain_name
            while not is_valid_domain_name(domain_name):
                print("Invalid domain name. Please try again.")
                domain_name = input(f"Please, enter a valid domain name "
                                    f"(default: '{default_domain_name}'):") or default_domain_name
            return domain_name

    def _get_web_config(self):
        """
        Asks the user for the web configuration. If the user enters an invalid domain name, the user is asked again.
        """
        print("Setting up web config...")
        self.mass_import_number_of_threads = 3
        default_domain_name = "fmd.localhost"
        default_companion_domain_name = "fmd-aosp.init-lab.ch"
        self.domain_name = self._get_domain_name(default_domain_name)
        self.api_title = "FirmwareDroid REST API"
        self.api_version = 1.0
        self.api_description = "REST API documentation for the FirmwareDroid service"
        self.api_prefix = "/api"
        self.api_doc_folder = "/docs"
        self.cors_additional_host = default_companion_domain_name
        self.django_secret_key = secrets.token_hex(100)
        self.django_sqlite_database_path = os.path.join("/var/www/", BLOB_STORAGE_NAME, "django_database/")
        self.django_superuser_username = "fmd-admin"
        self.django_superuser_password = uuid.uuid4()
        self.django_superuser_email = "fmd-admin@" + self.domain_name

    def _get_docker_limits(self):
        """
        Asks the user for the memory limit for the docker container. If the user enters an invalid memory limit,
        the user is asked again.
        """
        if self.use_defaults:
            self.docker_memory_limit = "10GB"
            self.docker_memory_swap_limit = "10GB"
            self.docker_cpu_limit = "0.5"
        else:
            while not is_valid_memory_limit(self.docker_memory_limit):
                self.docker_memory_limit = input("Enter the memory limit for the docker container "
                                                 "(default: 10GB):") or "10GB"
                self.docker_memory_swap_limit = input("Enter the swap memory limit for the docker "
                                                      "container (default: 10GB):") or "10GB"
            while not is_valid_cpu_limit(self.docker_cpu_limit):
                self.docker_cpu_limit = input("Enter the cpu limit for the docker container "
                                              "(default: 0.5):") or "0.5"

    def create_env_file(self):
        """
        Creates the .env file for the FirmwareDroid service.
        """
        self._get_environment()
        self._get_blob_storage()
        self._get_mongodb_settings()
        self._get_web_config()
        self._get_docker_limits()
        template = TEMPLATE_ENV.get_template(ENV_FILE_NAME)
        content = template.render(
            app_env=self.app_env,
            app_debug=self.app_debug,
            local_storage_path_00=self.local_storage_path_list[0],
            local_storage_path_01=self.local_storage_path_list[1],
            local_storage_path_02=self.local_storage_path_list[2],
            local_storage_path_03=self.local_storage_path_list[3],
            local_storage_path_04=self.local_storage_path_list[4],
            local_storage_path_05=self.local_storage_path_list[5],
            local_storage_path_06=self.local_storage_path_list[6],
            local_storage_path_07=self.local_storage_path_list[7],
            local_storage_path_08=self.local_storage_path_list[8],
            local_storage_path_09=self.local_storage_path_list[9],
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
            django_sqlite_database_mount_path=self.django_sqlite_database_mount_path,
            django_superuser_password=self.django_superuser_password,
            django_superuser_username=self.django_superuser_username,
            django_superuser_email=self.django_superuser_email,
            docker_memory_limit=self.docker_memory_limit,
            docker_memory_swap_limit=self.docker_memory_swap_limit,
            docker_cpu_limit=self.docker_cpu_limit
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
    Uses a config template to create a valid runtime configuration for redis. Writes the config file into the env
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
    Uses a config template to create a valid runtime configuration for mongodb. Write several config files into the
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
    print("Completed mongodb env setup.")
    replica_setup_source_path = os.path.join(env_instance.script_file_path, TEMPLATE_FOLDER, REPLICA_SET_SCRIPT_NAME)
    shutil.copy(replica_setup_source_path, mongo_env_init_path)


def setup_frontend_env(env_instance):
    """
    Uses a config template to create a valid runtime configuration for the frontend.
    """
    template = TEMPLATE_ENV.get_template(FMD_WEB_CLIENT_ENV_FILE_NAME)
    content = template.render(
        domain_name=env_instance.domain_name
    )
    output_file_path = os.path.join(env_instance.script_file_path, FMD_WEB_CLIENT_ENV_PATH,
                                    FMD_WEB_CLIENT_ENV_FILE_NAME)
    with open(output_file_path, 'w') as f:
        f.write(content)
    print("Completed frontend env setup.")


def main():
    """
    Command-line interface for the setup script. Parses the arguments and calls the setup functions.
    """
    parser = argparse.ArgumentParser(prog='setup',
                                     description="A cli tool to setup FirmwareDroid")
    parser.add_argument("-p", "--production-mode",
                        action="store_true",
                        default=False,
                        required=False,
                        help="Allows a production setup with advanced settings.")
    args = parser.parse_args()

    env_path = os.path.join("./.env")
    if os.path.exists(env_path):
        print(".env file already exists!")
        exit(1)

    if args.production_mode:
        use_defaults = False
        print("Using production settings...")
    else:
        use_defaults = True
        print("Using default development settings...")

    env_instance = setup_environment_variables(use_defaults=use_defaults)
    setup_nginx(env_instance)
    setup_redis(env_instance)
    setup_mongo_env(env_instance)
    setup_frontend_env(env_instance)
    print("Ready for startup!")


if __name__ == "__main__":
    main()
