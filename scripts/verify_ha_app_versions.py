#!/usr/bin/env python3
"""Check that HA app metadata, Docker image pins and operator docs agree.

This is intentionally dependency-free and runs on *every* pull request.
It cannot replace multi-arch builds or live upgrade/rollback acceptance.
"""
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
issues = []


def read(path):
    return (ROOT / path).read_text(encoding="utf-8")


def only(pattern, text, description):
    matches = re.findall(pattern, text, flags=re.MULTILINE)
    if len(matches) != 1:
        issues.append(f"{description}: expected one occurrence, got {len(matches)}")
        return None
    return matches[0]


def check_equal(left, right, label):
    if left is None or right is None:
        return
    if left != right:
        issues.append(f"{label}: '{left}' != '{right}'")


def app_version(app):
    return only(r"""^version:\s*["']?([0-9][A-Za-z0-9.+-]*)["']?\s*$""",
                read(f"{app}/config.yaml"), f"{app} manifest version")


def check_semver_wrapper(app, upstream):
    appver = app_version(app)
    if appver and not re.fullmatch(re.escape(upstream) + r"-rch[0-9]+", appver):
        issues.append(f"{app}: app version '{appver}' does not match pinned runtime '{upstream}-rchN'")
    return appver


def check_readme(label, expected):
    text = read("README.md")
    pattern = rf"^- {re.escape(label)}: \x60([0-9][A-Za-z0-9.+-]*)\x60"
    actual = only(pattern, text, f"README {label}")
    check_equal(actual, expected, f"README {label}")


def main():
    # Gitea MCP: binary source, HA manifest, startup banner and README.
    mcp_docker = read("gitea_mcp/Dockerfile")
    mcp = only(r"^FROM docker\.gitea\.com/gitea-mcp-server:([0-9.]+) AS upstream\s*$",
               mcp_docker, "Gitea MCP pinned Docker image")
    check_semver_wrapper("gitea_mcp", mcp or "invalid")
    mcp_banner = only(r"Starting Gitea MCP ([0-9.]+)", read("gitea_mcp/run.sh"),
                      "Gitea MCP startup banner")
    check_equal(mcp_banner, mcp, "Gitea MCP startup banner")
    check_readme("Gitea MCP", mcp)

    # Runner: HA version must also match BUILD_VERSION label.
    runner_docker = read("gitea_runner/Dockerfile")
    runner = only(r"^FROM docker\.io/gitea/runner:([0-9.]+)\s*$",
                  runner_docker, "Gitea Runner pinned Docker image")
    runner_app = check_semver_wrapper("gitea_runner", runner or "invalid")
    build_version = only(r"^ARG BUILD_VERSION=([0-9A-Za-z.+-]+)\s*$",
                         runner_docker, "Gitea Runner build label")
    check_equal(build_version, runner_app, "Gitea Runner BUILD_VERSION")
    banner = only(r"Starting Gitea Runner ([0-9.]+)", read("gitea_runner/run.sh"),
                  "Gitea Runner startup banner")
    check_equal(banner, runner, "Gitea Runner startup banner")
    check_readme("Gitea Runner", runner)

    # Cloudflared app version is derived from the upstream HA app version,
    # not the cloudflared executable's independent 2026.x release series.
    cf_docker = read("cloudflared_auth/Dockerfile")
    cf = only(r"^ARG UPSTREAM_VERSION=([0-9.]+)\s*$",
              cf_docker, "Cloudflared upstream version ARG")
    if cf:
        check_semver_wrapper("cloudflared_auth", cf)

    # Vaultwarden's HA app version follows a separate numbering scheme.
    # Its one-time SQLite rollback snapshot must match the embedded server.
    vw_docker = read("vaultwarden/Dockerfile")
    vw = only(r'^FROM "vaultwarden/server:([0-9.]+)" AS vaultwarden\s*$',
              vw_docker, "Vaultwarden server image")
    app_version("vaultwarden")
    rollback = only(r'^\s*local migration_version="([0-9.]+)"\s*$',
                    read("vaultwarden/rootfs/etc/s6-overlay/s6-rc.d/vaultwarden/run"),
                    "Vaultwarden migration backup version")
    check_equal(rollback, vw, "Vaultwarden rollback snapshot")
    check_readme("Vaultwarden", vw)

    if issues:
        print("HA app release gate FAILED:", file=sys.stderr)
        for issue in issues:
            print(f" - {issue}", file=sys.stderr)
        return 1
    print(f"HA app release gate OK: Gitea MCP {mcp}, Runner {runner}, "
          f"Cloudflared app {cf}, Vaultwarden server {vw}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
