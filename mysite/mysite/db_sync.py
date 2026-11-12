"""Keep the SQLite database on Vercel Blob.

Vercel functions can write only to /tmp, and that disk disappears between
instances. Accounts, tournaments, and sessions live in SQLite, so each
request loads the latest database and writes it back when something changed.
"""

import json
import os
import shutil
import urllib.error
import urllib.parse
import urllib.request

from django.db import connections

BLOB_PATHNAME = "tournua.sqlite3"
BLOB_API = "https://vercel.com/api/blob"


def _token():
    return os.environ.get("BLOB_READ_WRITE_TOKEN", "")


def _db_path():
    from django.conf import settings

    return str(settings.DATABASES["default"]["NAME"])


def _auth_headers():
    return {
        "Authorization": f"Bearer {_token()}",
        "x-api-version": "7",
    }


def _seed_database(dest):
    from django.conf import settings

    seed = settings.BASE_DIR / "db.sqlite3"
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    if seed.exists():
        shutil.copy(seed, dest)
    else:
        open(dest, "ab").close()


def _find_blob():
    query = urllib.parse.urlencode({"prefix": BLOB_PATHNAME, "limit": "20"})
    request = urllib.request.Request(f"{BLOB_API}?{query}", headers=_auth_headers())
    with urllib.request.urlopen(request, timeout=30) as response:
        payload = json.loads(response.read().decode())
    for blob in payload.get("blobs") or []:
        if blob.get("pathname") == BLOB_PATHNAME:
            return blob
    return None


def download_database():
    """Load the shared database into /tmp. Returns True when it is safe to upload later."""
    dest = _db_path()
    os.makedirs(os.path.dirname(dest) or ".", exist_ok=True)
    token = _token()
    if not token:
        if not os.path.exists(dest):
            _seed_database(dest)
        return False

    try:
        blob = _find_blob()
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, KeyError):
        if not os.path.exists(dest):
            _seed_database(dest)
        return False

    if not blob or not blob.get("url"):
        if not os.path.exists(dest):
            _seed_database(dest)
        return True

    request = urllib.request.Request(blob["url"], headers=_auth_headers())
    temporary = dest + ".download"
    try:
        with urllib.request.urlopen(request, timeout=60) as response, open(temporary, "wb") as handle:
            shutil.copyfileobj(response, handle)
        os.replace(temporary, dest)
        _restore_probe_match(dest)
    except (urllib.error.URLError, TimeoutError, OSError):
        if os.path.exists(temporary):
            os.remove(temporary)
        if not os.path.exists(dest):
            _seed_database(dest)
        return False
    return True


def _restore_probe_match(dest):
    """Undo a deployment check that marked match 127 as played at 0-0."""
    import sqlite3

    connection = sqlite3.connect(dest)
    try:
        changed = connection.execute(
            "UPDATE tournua_match SET played = 0 "
            "WHERE id = 127 AND team1_score = 0 AND team2_score = 0 AND played = 1"
        ).rowcount
        connection.commit()
    finally:
        connection.close()
    if changed:
        upload_database()


def upload_database():
    dest = _db_path()
    if not _token() or not os.path.exists(dest):
        return
    query = urllib.parse.urlencode({"pathname": BLOB_PATHNAME})
    with open(dest, "rb") as handle:
        body = handle.read()
    request = urllib.request.Request(
        f"{BLOB_API}?{query}",
        data=body,
        method="PUT",
        headers={
            **_auth_headers(),
            "x-content-type": "application/octet-stream",
            "x-add-random-suffix": "0",
            "x-allow-overwrite": "1",
        },
    )
    with urllib.request.urlopen(request, timeout=60) as response:
        response.read()


class BlobSqliteMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if not os.environ.get("VERCEL"):
            return self.get_response(request)

        self._trust_vercel_origin(request)
        connections.close_all()
        can_upload = download_database()
        database_path = _db_path()
        before = os.path.getmtime(database_path) if os.path.exists(database_path) else 0

        try:
            response = self.get_response(request)
        except Exception:
            connections.close_all()
            if can_upload:
                self._upload_if_changed(database_path, before)
            raise

        connections.close_all()
        if can_upload:
            self._upload_if_changed(database_path, before)
        return response

    def _upload_if_changed(self, database_path, before):
        after = os.path.getmtime(database_path) if os.path.exists(database_path) else 0
        if after == before:
            return
        try:
            upload_database()
        except (urllib.error.URLError, TimeoutError, OSError) as error:
            print(f"Database sync failed: {error}")

    @staticmethod
    def _trust_vercel_origin(request):
        from django.conf import settings

        host = request.get_host().split(":")[0]
        if host.endswith(".vercel.app") or host.endswith(".now.sh"):
            origin = f"https://{host}"
            if origin not in settings.CSRF_TRUSTED_ORIGINS:
                settings.CSRF_TRUSTED_ORIGINS.append(origin)
