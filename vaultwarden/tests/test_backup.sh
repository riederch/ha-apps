#!/usr/bin/env bash
# Isolated functional tests for the startup SQLite rollback point.
set -euo pipefail

script="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)/rootfs/etc/s6-overlay/s6-rc.d/vaultwarden/run"
tmpdir="$(mktemp -d)"
trap 'rm -rf "$tmpdir"' EXIT
export DATA_FOLDER="$tmpdir/data"
mkdir -p "$DATA_FOLDER"

bashio::log.notice() { :; }
bashio::exit.nok() {
    printf 'Expected startup refusal: %s\n' "$*" >&2
    exit 97
}

# Source only the actual production backup function (not the app startup).
source <(sed -n '/^backup_sqlite_before_upgrade() {/,/^}/p' "$script")
declare -F backup_sqlite_before_upgrade >/dev/null

database="$DATA_FOLDER/db.sqlite3"
backup="$DATA_FOLDER/migration-backups/db.sqlite3.pre-1.37.5"

# Nothing to back up on a fresh instance.
backup_sqlite_before_upgrade
test ! -e "$backup"

python3 - "$database" <<'PY'
import sqlite3
import sys
with sqlite3.connect(sys.argv[1]) as db:
    db.execute("CREATE TABLE sample (k TEXT PRIMARY KEY, v TEXT)")
    db.execute("INSERT INTO sample VALUES ('key', 'before-upgrade')")
PY

# First boot creates a verified, independent SQLite rollback point.
backup_sqlite_before_upgrade
test -s "$backup"
test "$(sqlite3 "$backup" "SELECT v FROM sample WHERE k='key';")" = "before-upgrade"
test "$(sqlite3 "$backup" 'PRAGMA quick_check;')" = "ok"

# A subsequent boot must never overwrite the pre-migration snapshot.
sqlite3 "$database" "UPDATE sample SET v='after-upgrade' WHERE k='key';"
backup_sqlite_before_upgrade
test "$(sqlite3 "$backup" "SELECT v FROM sample WHERE k='key';")" = "before-upgrade"

# Existing corrupt backup must stop startup, not be silently accepted.
printf 'not-a-sqlite-database' > "$backup"
if (backup_sqlite_before_upgrade >/dev/null 2>&1); then
    echo 'FAIL: corrupt existing rollback snapshot was accepted' >&2
    exit 1
fi

# Corrupt source with no snapshot must also fail closed.
rm -f "$backup"
printf 'not-a-sqlite-database' > "$database"
if (backup_sqlite_before_upgrade >/dev/null 2>&1); then
    echo 'FAIL: corrupt source SQLite database was accepted' >&2
    exit 1
fi

echo 'PASS: Vaultwarden SQLite backup creation, idempotence and fail-closed handling'
