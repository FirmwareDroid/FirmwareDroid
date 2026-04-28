# -*- coding: utf-8 -*-
# This file is part of FirmwareDroid - https://github.com/FirmwareDroid/FirmwareDroid/blob/main/LICENSE.md
# See the file 'LICENSE' for copying permission.
import datetime
import os
import shutil
import sys
import uuid
import secrets
from jinja2 import Environment, FileSystemLoader
from secrets import token_bytes
from base64 import b64encode
import argparse

# Make source/ importable so we can reuse env_utils from setup.py
_SCRIPT_DIR = os.path.dirname(os.path.realpath(__file__))
sys.path.insert(0, os.path.join(_SCRIPT_DIR, "source"))
from utils.env_utils import (  # noqa: E402 – import after path manipulation
    generate_key,
    save_key,
    load_key,
    encrypt_value,
    decrypt_value,
    decrypt_env_to_dict,
    Fernet,
)

TEMPLATE_FOLDER = "templates/"
TEMPLATE_ENV = Environment(loader=FileSystemLoader(TEMPLATE_FOLDER))
REDIS_CONFIG_NAME = "redis.conf"
REDIS_CONFIG_PATH = "env/redis/"
MONGO_CONFIG_PATH = "env/mongo/"
NGINX_CONFIG_NAME = "app.conf"
NGINX_STEAM_NAME = "stream.conf"
NGINX_CONFIG_PATH = "env/nginx/"
NEO4J_CONFIG_PATH = "env/neo4j/"
ENV_FILE_NAME = "env"
ENV_KEY_FILE_NAME = ".env.key"
REPLICA_SET_SCRIPT_NAME = "mongo_replica_set_setup.sh"
BLOB_STORAGE_NAME = "blob_storage/"
FMD_WEB_CLIENT_ENV_FILE_NAME = "EnvConfig.js"
FMD_WEB_CLIENT_ENV_PATH = "firmware-droid-client/src/"

# Fields in the .env template whose values must be encrypted on disk.
SECRET_FIELDS = frozenset({
    "REDIS_PASSWORD",
    "MONGO_INITDB_ROOT_PASSWORD",
    "MONGODB_PASSWORD",
    "DJANGO_SECRET_KEY",
    "DJANGO_SUPERUSER_PASSWORD",
    "NEO4J_AUTH",
})


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
    local_neo4j_db_path = None
    neo4j_password = None
    neo4j_auth_enabled = None
    neo4j_connector_http_listen_address= None
    neo4j_default_advertised_address= None

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


    def _get_neo4j_database_path(self):
        self.local_neo4j_db_path = os.path.join(self.blob_storage_path, "neo4j_database/")
        if self.use_defaults:
            return self.local_neo4j_db_path
        else:
            return input(f"Where do you want to store the ne04j database? "
                         f"(default: '{self.local_neo4j_db_path}'):") \
                or self.local_neo4j_db_path


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

            self.neo4j_database_path = self._get_neo4j_database_path()
            if not _create_directory(os.path.dirname(self.neo4j_database_path)):
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

    def _get_neo4j_settings(self):
        """
        Sets up the neo4j database settings.
        """
        self.neo4j_password = uuid.uuid4()
        self.neo4j_auth_enabled = True
        self.neo4j_connector_http_listen_address = "0.0.0.0"
        self.neo4j_default_advertised_address = "neo4j"


    def create_env_file(self, key_file_path):
        """
        Creates the .env file for the FirmwareDroid service with all secret
        values encrypted on disk using Fernet symmetric encryption.

        :param key_file_path: str - path where the .env.key file will be saved.
        """
        self._get_environment()
        self._get_blob_storage()
        self._get_mongodb_settings()
        self._get_web_config()
        self._get_docker_limits()
        self._get_neo4j_settings()

        # Generate and persist the Fernet encryption key.
        key = generate_key()
        save_key(key, key_file_path)
        fernet = Fernet(key)
        print(f"Generated encryption key and saved to: {key_file_path}")
        print("IMPORTANT: Keep this key file secure. "
              "Without it, encrypted secrets cannot be recovered.\n")

        # Collect plaintext secret values for display to the user.
        neo4j_auth_plaintext = f"neo4j/{self.neo4j_password}"
        plaintext_secrets = {
            "REDIS_PASSWORD": str(self.redis_password),
            "MONGO_INITDB_ROOT_PASSWORD": str(self.mongodb_initdb_root_password),
            "MONGODB_PASSWORD": str(self.mongodb_password),
            "DJANGO_SECRET_KEY": str(self.django_secret_key),
            "DJANGO_SUPERUSER_PASSWORD": str(self.django_superuser_password),
            "NEO4J_AUTH": neo4j_auth_plaintext,
        }

        def _enc(value):
            """Encrypt a string value and return the ENC: prefixed token."""
            return encrypt_value(str(value), fernet)

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
            redis_password=_enc(self.redis_password),
            redis_port=self.redis_port,
            mongodb_database_name=self.mongodb_database_name,
            mongodb_auth_src=self.mongodb_auth_src,
            mongodb_port=self.mongodb_port,
            mongo_db_replicat_set=self.mongo_db_replicat_set,
            mongodb_initdb_root_username=self.mongodb_initdb_root_username,
            mongodb_initdb_root_password=_enc(self.mongodb_initdb_root_password),
            mongodb_username=self.mongodb_username,
            mongodb_password=_enc(self.mongodb_password),
            mongo_db_hostname=self.mongo_db_hostname,
            mass_import_number_of_threads=self.mass_import_number_of_threads,
            domain_name=self.domain_name,
            api_title=self.api_title,
            api_version=self.api_version,
            api_description=self.api_description,
            api_prefix=self.api_prefix,
            api_doc_folder=self.api_doc_folder,
            cors_additional_host=self.cors_additional_host,
            django_secret_key=_enc(self.django_secret_key),
            django_sqlite_database_path=self.django_sqlite_database_path,
            django_sqlite_database_mount_path=self.django_sqlite_database_mount_path,
            django_superuser_password=_enc(self.django_superuser_password),
            django_superuser_username=self.django_superuser_username,
            django_superuser_email=self.django_superuser_email,
            docker_memory_limit=self.docker_memory_limit,
            docker_memory_swap_limit=self.docker_memory_swap_limit,
            docker_cpu_limit=self.docker_cpu_limit,
            local_neo4j_db_path=self.local_neo4j_db_path,
            # NEO4J_AUTH is written as "neo4j/<password>"; encrypt the whole value.
            neo4j_password=_enc(str(self.neo4j_password)),
            neo4j_auth_enabled=self.neo4j_auth_enabled,
            neo4j_connector_http_listen_address=self.neo4j_connector_http_listen_address,
            neo4j_default_advertised_address=self.neo4j_default_advertised_address
        )
        out_file_path = os.path.join(self.script_file_path, "." + ENV_FILE_NAME)
        with open(out_file_path, mode="w", encoding="utf-8") as out_file:
            out_file.write(content)
        os.chmod(out_file_path, 0o600)
        print("Created .env file (secrets are encrypted with ENC: prefix)\n")

        _print_plaintext_secrets(plaintext_secrets)


def _print_plaintext_secrets(secrets_dict):
    """Print plaintext secret values to the console for the operator to record."""
    separator = "=" * 70
    print(separator)
    print("PLAINTEXT SECRETS – record these now, they will not be shown again")
    print(separator)
    for name, value in secrets_dict.items():
        print(f"  {name}: {value}")
    print(separator)
    print("Store these secrets in a password manager or secure vault.\n")


def setup_environment_variables(use_defaults, key_file_path):
    env_instance = FmdEnvironment(use_defaults=use_defaults)
    env_instance.create_env_file(key_file_path)
    return env_instance


def rotate_secrets(env_file_path, key_file_path):
    """
    Re-generate all secret values in *env_file_path*, encrypt them with the
    existing key from *key_file_path*, and write the updated file.

    The new plaintext secrets are printed to stdout so the operator can update
    downstream services (MongoDB users, Redis passwords, etc.) accordingly.

    .. warning::
        After rotation you **must** restart all services and manually update
        any credentials that are stored inside MongoDB, Redis, or Neo4j
        (they are not updated automatically).
    """
    key = load_key(key_file_path)
    fernet = Fernet(key)

    # Read the current env file, decrypting existing ENC: values.
    current = decrypt_env_to_dict(env_file_path, key_file_path)

    # Generate new random values for every secret field.
    new_secrets = {
        "REDIS_PASSWORD": str(uuid.uuid4()),
        "MONGO_INITDB_ROOT_PASSWORD": str(uuid.uuid4()),
        "MONGODB_PASSWORD": str(uuid.uuid4()),
        "DJANGO_SECRET_KEY": secrets.token_hex(100),
        "DJANGO_SUPERUSER_PASSWORD": str(uuid.uuid4()),
        "NEO4J_AUTH": f"neo4j/{uuid.uuid4()}",
    }

    # Re-write the env file, substituting encrypted new values for secret fields.
    updated_lines = []
    with open(env_file_path, "r", encoding="utf-8") as f:
        for line in f:
            stripped = line.strip()
            if stripped and not stripped.startswith("#") and "=" in stripped:
                name, _, _ = stripped.partition("=")
                name = name.strip()
                if name in new_secrets:
                    encrypted = encrypt_value(new_secrets[name], fernet)
                    updated_lines.append(f"{name}={encrypted}\n")
                    continue
            updated_lines.append(line)

    with open(env_file_path, "w", encoding="utf-8") as f:
        f.writelines(updated_lines)
    os.chmod(env_file_path, 0o600)

    print(f"Rotated secrets in {env_file_path}")
    _print_plaintext_secrets(new_secrets)
    print("Restart all services and update credentials in MongoDB/Redis/Neo4j as needed.")


def rekey_env(env_file_path, old_key_file_path, new_key_file_path=None):
    """
    Replace the encryption key used for *env_file_path*.

    Decrypts all ``ENC:`` values with the old key, generates a new key,
    re-encrypts all values with the new key, and writes the updated files.

    :param env_file_path: path to the .env file to re-encrypt.
    :param old_key_file_path: path to the current .env.key file.
    :param new_key_file_path: where to save the new key (defaults to the same
        path, replacing the old key).
    """
    if new_key_file_path is None:
        new_key_file_path = old_key_file_path

    # Decrypt all current ENC: values using the old key.
    current = decrypt_env_to_dict(env_file_path, old_key_file_path)

    # Generate and save the new key.
    new_key = generate_key()
    save_key(new_key, new_key_file_path)
    new_fernet = Fernet(new_key)

    # Identify which fields are currently encrypted.
    old_key = load_key(old_key_file_path)
    old_fernet = Fernet(old_key)
    encrypted_fields = set()
    with open(env_file_path, "r", encoding="utf-8") as f:
        for line in f:
            stripped = line.strip()
            if stripped and not stripped.startswith("#") and "=" in stripped:
                name, _, value = stripped.partition("=")
                if value.strip().startswith("ENC:"):
                    encrypted_fields.add(name.strip())

    # Re-write env file with new encryption.
    updated_lines = []
    with open(env_file_path, "r", encoding="utf-8") as f:
        for line in f:
            stripped = line.strip()
            if stripped and not stripped.startswith("#") and "=" in stripped:
                name, _, _ = stripped.partition("=")
                name = name.strip()
                if name in encrypted_fields:
                    encrypted = encrypt_value(current[name], new_fernet)
                    updated_lines.append(f"{name}={encrypted}\n")
                    continue
            updated_lines.append(line)

    with open(env_file_path, "w", encoding="utf-8") as f:
        f.writelines(updated_lines)
    os.chmod(env_file_path, 0o600)

    print(f"Re-keyed {env_file_path} with new key saved to {new_key_file_path}")
    print("Restart all services for the new key to take effect.")


def render_and_write(env_instance, template_name, out_name, context):
    template = TEMPLATE_ENV.get_template(template_name)
    content = template.render(**context)
    out_file_path = os.path.join(env_instance.script_file_path, NGINX_CONFIG_PATH, out_name)
    os.makedirs(os.path.dirname(out_file_path), exist_ok=True)
    with open(out_file_path, mode="w", encoding="utf-8") as out_file:
        out_file.write(content)


def setup_nginx(env_instance):
    """
    Uses an config template to create a valid runtime configuration for nginx.

    :param env_instance: class:`FmdEnvironment` - with parameters set for the web domain.
    """
    nginx_path = os.path.join(env_instance.script_file_path, NGINX_CONFIG_PATH)
    if not os.path.exists(nginx_path):
        os.makedirs("./env/nginx")
        os.makedirs(f"./env/nginx/live/{env_instance.domain_name}")

    render_and_write(env_instance, NGINX_CONFIG_NAME, NGINX_CONFIG_NAME, {"domain_name": env_instance.domain_name})
    render_and_write(env_instance, NGINX_STEAM_NAME, NGINX_STEAM_NAME, {"domain_name": env_instance.domain_name})

    output_path = os.path.join(env_instance.script_file_path, NGINX_CONFIG_PATH, f"live/{env_instance.domain_name}/")
    generate_certificate(env_instance, output_path)
    print("Completed nginx env setup.")


def setup_neo4j(env_instance):
    neo4j_path = os.path.join(env_instance.script_file_path, NEO4J_CONFIG_PATH)

    os.makedirs(NEO4J_CONFIG_PATH, exist_ok=True)
    os.makedirs(f"{NEO4J_CONFIG_PATH}/ssl/https", exist_ok=True)
    os.makedirs(f"{NEO4J_CONFIG_PATH}/ssl/bolt", exist_ok=True)
    output_path = os.path.join(env_instance.script_file_path, NEO4J_CONFIG_PATH, f"ssl/https/")
    generate_certificate(env_instance,
                         output_path,
                         port=7473,
                         private_key_filename="private.key",
                         public_key_filename="public.crt"
                         )
    output_path = os.path.join(env_instance.script_file_path, NEO4J_CONFIG_PATH, f"ssl/bolt/")
    generate_certificate(env_instance,
                         output_path,
                         port=7687,
                         private_key_filename="private.key",
                         public_key_filename="public.crt"
                         )
    print("Completed neo4j env setup.")



def generate_certificate(env_instance, output_path, port=None, private_key_filename=None, public_key_filename=None):
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

    if port:
        domain_name = f"{env_instance.domain_name}:{port}"
    else:
        domain_name = env_instance.domain_name

    # Create a subject for the certificate
    subject = x509.Name([
        x509.NameAttribute(NameOID.COUNTRY_NAME, "CH"),
        x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, "Zurich"),
        x509.NameAttribute(NameOID.LOCALITY_NAME, "Winterthur"),
        x509.NameAttribute(NameOID.ORGANIZATION_NAME, "Zurich University of Applied Sciences"),
        x509.NameAttribute(NameOID.COMMON_NAME, domain_name),
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
        datetime.datetime.now(datetime.UTC)
    ).not_valid_after(
        datetime.datetime.now(datetime.UTC) + datetime.timedelta(days=1024)
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

    if not private_key_filename:
        private_key_filename = 'privkey.pem'
    if not public_key_filename:
        public_key_filename = "certificate.pem"

    privkey_pem_path = os.path.join(output_path, private_key_filename)
    cert_pem_path = os.path.join(output_path, public_key_filename)
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


def setup_monitoring(env_instance):
    """
    Create per-service env folders and default configuration files for monitoring stack.
    """
    # create env dirs
    node_env_dir = os.path.join(env_instance.script_file_path, "env", "node-exporter")
    cadvisor_dir = os.path.join(env_instance.script_file_path, "env", "cadvisor")
    prometheus_dir = os.path.join(env_instance.script_file_path, "env", "prometheus")
    grafana_dir = os.path.join(env_instance.script_file_path, "env", "grafana")

    os.makedirs(node_env_dir, exist_ok=True)
    os.makedirs(cadvisor_dir, exist_ok=True)
    os.makedirs(prometheus_dir, exist_ok=True)
    os.makedirs(grafana_dir, exist_ok=True)

    # generate secure random passwords for each monitoring service
    # using token_urlsafe which is suitable for secrets in env files
    node_exporter_password = secrets.token_urlsafe(24)
    cadvisor_password = secrets.token_urlsafe(24)
    prometheus_password = secrets.token_urlsafe(24)
    grafana_admin_password = secrets.token_urlsafe(24)

    # write node-exporter env file
    node_env_file = os.path.join(node_env_dir, "env")
    node_env_content = (
        "# node-exporter env\n"
        f"NODE_EXPORTER_DEFAULT_PASSWORD={node_exporter_password}\n"
    )
    with open(node_env_file, "w", encoding="utf-8") as f:
        f.write(node_env_content)
    os.chmod(node_env_file, 0o600)

    # write cadvisor env file
    cadvisor_env_file = os.path.join(cadvisor_dir, "env")
    cadvisor_env_content = (
        "# cadvisor env\n"
        f"CADVISOR_DEFAULT_PASSWORD={cadvisor_password}\n"
    )
    with open(cadvisor_env_file, "w", encoding="utf-8") as f:
        f.write(cadvisor_env_content)
    os.chmod(cadvisor_env_file, 0o600)

    # write prometheus env file
    prometheus_env_file = os.path.join(prometheus_dir, "env")
    prometheus_env_content = (
        "# prometheus env\n"
        f"PROMETHEUS_DEFAULT_PASSWORD={prometheus_password}\n"
    )
    with open(prometheus_env_file, "w", encoding="utf-8") as f:
        f.write(prometheus_env_content)
    os.chmod(prometheus_env_file, 0o600)

    # grafana
    grafana_env_file = os.path.join(grafana_dir, "env")
    grafana_env_content = (
        f"GF_SECURITY_ADMIN_PASSWORD={grafana_admin_password}\n"
        "GF_USERS_ALLOW_SIGN_UP=false\n"
        "GF_SERVER_ROOT_URL=%(protocol)s://%(domain)s/\n" % {"protocol": "https", "domain": env_instance.domain_name}
    )
    with open(grafana_env_file, "w", encoding="utf-8") as f:
        f.write(grafana_env_content)
    os.chmod(grafana_env_file, 0o600)
    print("Completed monitoring env setup.")


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
    parser.add_argument("--rotate-secrets",
                        action="store_true",
                        default=False,
                        required=False,
                        help="Generate new random values for all secret fields in an "
                             "existing .env, re-encrypt with the current key, and print "
                             "the new plaintext secrets. Services must be restarted and "
                             "credentials in MongoDB/Redis/Neo4j must be updated manually.")
    parser.add_argument("--rekey",
                        action="store_true",
                        default=False,
                        required=False,
                        help="Replace the encryption key in .env.key and re-encrypt all "
                             "secret values in .env with the new key. Services must be "
                             "restarted afterwards.")
    args = parser.parse_args()

    script_dir = os.path.dirname(os.path.realpath(__file__))
    env_path = os.path.join(script_dir, ".env")
    key_path = os.path.join(script_dir, ENV_KEY_FILE_NAME)

    # --- rotate-secrets sub-command ---
    if args.rotate_secrets:
        if not os.path.exists(env_path):
            print("Error: .env file not found. Run setup first.")
            exit(1)
        if not os.path.exists(key_path):
            print("Error: .env.key file not found. Run setup first.")
            exit(1)
        rotate_secrets(env_path, key_path)
        return

    # --- rekey sub-command ---
    if args.rekey:
        if not os.path.exists(env_path):
            print("Error: .env file not found. Run setup first.")
            exit(1)
        if not os.path.exists(key_path):
            print("Error: .env.key file not found. Run setup first.")
            exit(1)
        rekey_env(env_path, key_path)
        return

    # --- normal setup ---
    if os.path.exists(env_path):
        print(".env file already exists!")
        exit(1)

    if args.production_mode:
        use_defaults = False
        print("Using production settings...")
    else:
        use_defaults = True
        print("Using default development settings...")

    env_instance = setup_environment_variables(use_defaults=use_defaults, key_file_path=key_path)
    setup_nginx(env_instance)
    setup_neo4j(env_instance)
    setup_redis(env_instance)
    setup_mongo_env(env_instance)
    setup_frontend_env(env_instance)
    setup_monitoring(env_instance)
    print("Ready for startup! Use ./start.sh to launch the application.")


if __name__ == "__main__":
    main()
