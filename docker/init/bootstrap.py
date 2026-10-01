#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# This file is part of FirmwareDroid - https://github.com/FirmwareDroid/FirmwareDroid/blob/main/LICENSE.md
# See the file 'LICENSE' for copying permission.
"""
Entrypoint for the `init` bootstrap container.

Generates all secrets and per-service runtime configuration (Mongo cluster key + replica-set
init script, Redis password-protected config, Nginx TLS + reverse-proxy config, Neo4j TLS)
into `/config`, which is expected to be mounted as the shared `fmd-config` named Docker volume.

The container is idempotent: if `/config/.bootstrapped` already exists, it exits immediately
without regenerating anything (so restarting the stack does not rotate secrets or invalidate
existing databases).

Nothing is written to the host filesystem: `/config` only exists inside the named volume, and
this container never mounts the repository checkout.
"""
import os
import shutil
import sys
from pathlib import Path

from bootstrap_lib import (
    GeneratedSecrets,
    generate_certificate,
    generate_cluster_key,
    get_template_env,
    render_template,
)

CONFIG_DIR = Path(os.environ.get("FMD_CONFIG_DIR", "/config"))
MARKER_FILE = CONFIG_DIR / ".bootstrapped"


def _domain_name() -> str:
    return os.environ.get("DOMAIN_NAME", "fmd.localhost")


def copy_entrypoint_wrapper() -> None:
    """Copies entrypoint-wrapper.sh into the shared config directory for service entrypoints."""
    candidate_paths = [
        Path("/app/entrypoint-wrapper.sh"),
        Path(__file__).parent / "entrypoint-wrapper.sh",
    ]
    for p in candidate_paths:
        if p.is_file():
            dst = CONFIG_DIR / "entrypoint-wrapper.sh"
            dst.write_bytes(p.read_bytes())
            os.chmod(dst, 0o755)
            break


def bootstrap_mongo(secrets_obj: GeneratedSecrets) -> None:
    print("Generating MongoDB cluster key and replica-set init script...")
    auth_dir = CONFIG_DIR / "mongo" / "auth"
    init_dir = CONFIG_DIR / "mongo" / "init"
    auth_dir.mkdir(parents=True, exist_ok=True)
    init_dir.mkdir(parents=True, exist_ok=True)

    cluster_key_path = auth_dir / "cluster.key"
    cluster_key_path.write_text(generate_cluster_key(), encoding="utf-8")
    os.chmod(cluster_key_path, 0o400)

    template_dir = Path("/templates") if Path("/templates").exists() else Path("templates")
    replica_script_src = template_dir / "mongo_replica_set_setup.sh"
    replica_script_dst = init_dir / "mongo_replica_set_setup.sh"
    replica_script_dst.write_bytes(replica_script_src.read_bytes())
    os.chmod(replica_script_dst, 0o755)

    # Mongo may run as UID 1000:1000; ensure cluster.key and init script are accessible
    try:
        shutil.chown(cluster_key_path, user=1000, group=1000)
        shutil.chown(auth_dir, user=1000, group=1000)
        shutil.chown(init_dir, user=1000, group=1000)
    except Exception as e:
        print(f"Notice: could not chown mongo directories/keys to 1000:1000: {e}")


def bootstrap_redis(secrets_obj: GeneratedSecrets) -> None:
    print("Generating Redis config...")
    env = get_template_env()
    render_template(env, "redis.conf", CONFIG_DIR / "redis" / "redis.conf",
                    redis_password=secrets_obj.redis_password)


def bootstrap_nginx(domain_name: str, frontend_dev_proxy: bool = False) -> None:
    print(f"Generating Nginx config (frontend_dev_proxy={frontend_dev_proxy}) and self-signed TLS certificate...")
    env = get_template_env()
    render_template(env, "app.conf", CONFIG_DIR / "nginx" / "app.conf",
                    domain_name=domain_name,
                    frontend_dev_proxy=frontend_dev_proxy)
    render_template(env, "stream.conf", CONFIG_DIR / "nginx" / "stream.conf", domain_name=domain_name)

    live_dir = CONFIG_DIR / "nginx" / "live" / domain_name
    if not (live_dir / "privkey.pem").exists() or not (live_dir / "certificate.pem").exists():
        generate_certificate(live_dir, domain_name,
                             private_key_filename="privkey.pem",
                             public_key_filename="certificate.pem")


def bootstrap_neo4j(domain_name: str) -> None:
    print("Generating Neo4j TLS certificates...")
    https_dir = CONFIG_DIR / "neo4j" / "ssl" / "https"
    bolt_dir = CONFIG_DIR / "neo4j" / "ssl" / "bolt"
    generate_certificate(https_dir, domain_name, port=7473,
                         private_key_filename="private.key",
                         public_key_filename="public.crt")
    generate_certificate(bolt_dir, domain_name, port=7687,
                         private_key_filename="private.key",
                         public_key_filename="public.cert")

    # Provide common alias filenames so both legacy and modern Neo4j settings match
    for directory in (https_dir, bolt_dir):
        key_file = directory / "private.key"
        if key_file.exists():
            (directory / "neo4j.key").write_bytes(key_file.read_bytes())
    if (https_dir / "public.crt").exists():
        (https_dir / "neo4j.crt").write_bytes((https_dir / "public.crt").read_bytes())
    if (bolt_dir / "public.cert").exists():
        (bolt_dir / "neo4j.cert").write_bytes((bolt_dir / "public.cert").read_bytes())
        (bolt_dir / "public.crt").write_bytes((bolt_dir / "public.cert").read_bytes())


def write_runtime_env(secrets_obj: GeneratedSecrets, domain_name: str) -> None:
    runtime_env_path = CONFIG_DIR / "runtime.env"
    runtime_env_path.write_text(secrets_obj.as_runtime_env(domain_name), encoding="utf-8")
    os.chmod(runtime_env_path, 0o644)


def write_secrets_summary(secrets_obj: GeneratedSecrets, domain_name: str) -> str:
    secrets_dir = CONFIG_DIR / "secrets"
    secrets_dir.mkdir(parents=True, exist_ok=True)
    summary = secrets_obj.as_human_readable(domain_name)
    summary_path = secrets_dir / "generated-secrets.txt"
    summary_path.write_text(summary, encoding="utf-8")
    os.chmod(summary_path, 0o600)
    return summary


def set_permissions() -> None:
    """Ensure non-root container users (www, neo4j, etc.) can read generated configurations."""
    for p in CONFIG_DIR.rglob("*"):
        if p.name == "cluster.key":
            continue  # MongoDB requires cluster.key to stay strict 400
        if p.name == "generated-secrets.txt" or (p.is_file() and p.parent.name == "secrets"):
            try:
                os.chmod(p, 0o600)
            except Exception:
                pass
            continue
        try:
            if p.is_dir():
                os.chmod(p, 0o755)
            elif p.suffix == ".sh":
                os.chmod(p, 0o755)
            else:
                os.chmod(p, 0o644)
        except Exception:
            pass


def main() -> int:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    domain_name = _domain_name()
    frontend_dev_proxy = os.environ.get("FRONTEND_DEV_PROXY", "false").lower() in ("true", "1", "yes")

    if MARKER_FILE.exists():
        print(f"'{MARKER_FILE}' already present; secrets bootstrap already completed.")
        # Ensure Nginx reverse-proxy configuration is kept in sync with environment / templates
        bootstrap_nginx(domain_name, frontend_dev_proxy=frontend_dev_proxy)
        set_permissions()
        print("Updated Nginx configuration in fmd-config volume.")
        return 0

    print(f"Bootstrapping FirmwareDroid runtime config for domain '{domain_name}'...")

    secrets_obj = GeneratedSecrets()

    copy_entrypoint_wrapper()
    bootstrap_mongo(secrets_obj)
    bootstrap_redis(secrets_obj)
    bootstrap_nginx(domain_name, frontend_dev_proxy=frontend_dev_proxy)
    bootstrap_neo4j(domain_name)
    write_runtime_env(secrets_obj, domain_name)
    summary = write_secrets_summary(secrets_obj, domain_name)
    set_permissions()

    MARKER_FILE.write_text("bootstrapped\n", encoding="utf-8")

    print_secrets = os.environ.get("PRINT_BOOTSTRAP_SECRETS", "false").lower() in ("true", "1", "yes")

    print("\n" + "=" * 70)
    if print_secrets:
        print(summary)
    else:
        print("FirmwareDroid runtime configuration and credentials generated!")
        print("")
        print("For security reasons, generated credentials are NOT printed to container logs.")
        print("You can retrieve your administrator credentials and secrets at any time by running:")
        print("")
        print("    docker compose cp init:/config/secrets/generated-secrets.txt .")
        print("    cat generated-secrets.txt")
        print("")
        print("Alternatively, view them directly via:")
        print("    docker compose exec web cat /var/www/config/secrets/generated-secrets.txt")
    print("=" * 70)
    print("Bootstrap complete.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
