import hashlib
import logging
from pathlib import Path

from config.config import DRIVE_ROOT_FOLDER_ID
from models.models import RawDocModel

SCOPES = ["https://www.googleapis.com/auth/drive"]
_OAUTH_CREDENTIALS_PATH = Path("config/oauth_credentials.json")
_TOKEN_PATH = Path("config/token.json")
_SA_CREDENTIALS_PATH = Path("config/credentials.json")


def _hash_path(rel: str) -> str:
    """SHA1 del path relativo — cabe en los 124 bytes del límite de appProperties."""
    return hashlib.sha1(rel.encode("utf-8")).hexdigest()


def _get_creds():
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from google.auth.transport.requests import Request

    creds = None
    if _TOKEN_PATH.exists():
        creds = Credentials.from_authorized_user_file(str(_TOKEN_PATH), SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                str(_OAUTH_CREDENTIALS_PATH), SCOPES
            )
            creds = flow.run_local_server(port=0)
        _TOKEN_PATH.write_text(creds.to_json(), encoding="utf-8")
    return creds


class DriveUploader:
    def __init__(self):
        self._service = None
        self._folder_cache: dict[str, str] = {}
        self._root_id: str | None = None
        self._init_service()

    def _init_service(self):
        if not _OAUTH_CREDENTIALS_PATH.exists():
            logging.warning(
                "DriveUploader: config/oauth_credentials.json no encontrado — "
                "subida a Drive deshabilitada"
            )
            return
        try:
            from googleapiclient.discovery import build

            creds = _get_creds()
            self._service = build("drive", "v3", credentials=creds)
            self._root_id = DRIVE_ROOT_FOLDER_ID

            about = self._service.about().get(fields="user").execute()
            email = about["user"]["emailAddress"]
            logging.info(f"DriveUploader: conectado a Google Drive como {email}")
        except Exception as e:
            logging.warning(
                f"DriveUploader: no se pudo inicializar ({e}) — "
                "subida deshabilitada"
            )
            self._service = None

    def _get_or_create_folder(self, name: str, parent_id: str) -> str:
        cache_key = f"{parent_id}/{name}"
        if cache_key in self._folder_cache:
            return self._folder_cache[cache_key]

        q = (
            f"name='{name}' "
            f"and mimeType='application/vnd.google-apps.folder' "
            f"and '{parent_id}' in parents "
            f"and trashed=false"
        )
        results = (
            self._service.files()
            .list(q=q, fields="files(id)", pageSize=1)
            .execute()
        )
        files = results.get("files", [])

        if files:
            folder_id = files[0]["id"]
        else:
            metadata = {
                "name": name,
                "mimeType": "application/vnd.google-apps.folder",
                "parents": [parent_id],
            }
            folder = (
                self._service.files()
                .create(body=metadata, fields="id")
                .execute()
            )
            folder_id = folder["id"]

        self._folder_cache[cache_key] = folder_id
        return folder_id

    def archivo_existe(self, doc_id: str) -> str | None:
        if self._service is None:
            return None
        try:
            q = (
                f"appProperties has {{key='doc_id' and value='{doc_id}'}} "
                f"and trashed=false"
            )
            results = (
                self._service.files()
                .list(q=q, fields="files(id)", pageSize=1)
                .execute()
            )
            files = results.get("files", [])
            if files:
                return f"https://drive.google.com/file/d/{files[0]['id']}/view"
            return None
        except Exception as e:
            logging.warning(f"DriveUploader: error verificando existencia ({e})")
            return None

    def upload_file(self, local_path: Path, doc: RawDocModel, doc_id: str | None = None) -> str | None:
        if self._service is None:
            return None
        try:
            from googleapiclient.http import MediaFileUpload

            source_id = self._get_or_create_folder(doc.source, self._root_id)
            date_id = self._get_or_create_folder(doc.f_public, source_id)
            tipo_id = self._get_or_create_folder(doc.tipo, date_id)

            try:
                local_rel = str(local_path.relative_to(Path("downloads"))).replace("\\", "/")
            except ValueError:
                local_rel = local_path.name

            file_metadata = {
                "name": local_path.name,
                "parents": [tipo_id],
                "appProperties": {"doc_id": doc_id or "", "local_path": _hash_path(local_rel)},
            }
            media = MediaFileUpload(str(local_path), resumable=False)
            result = self._service.files().create(
                body=file_metadata, media_body=media, fields="id"
            ).execute()
            file_id = result["id"]
            logging.info(f"DriveUploader: subido {local_path.name}")
            return f"https://drive.google.com/file/d/{file_id}/view"
        except Exception as e:
            logging.warning(f"DriveUploader: error subiendo {local_path.name}: {e}")
            return None

    def upload_pending_to_drive(self, downloads_dir, on_progress=None, stop_event=None, sheets_reporter=None) -> int:
        if self._service is None:
            return 0
        from googleapiclient.http import MediaFileUpload
        from db.memory import Memory

        db = Memory()
        downloads_dir = Path(downloads_dir)
        count = 0
        try:
            for file_path in sorted(downloads_dir.rglob("*")):
                if not file_path.is_file():
                    continue
                if stop_event and stop_event.is_set():
                    break
                try:
                    rel = str(file_path.relative_to(downloads_dir)).replace("\\", "/")
                except ValueError:
                    continue
                path_hash = _hash_path(rel)
                q = (
                    f"appProperties has {{key='local_path' and value='{path_hash}'}} "
                    f"and trashed=false"
                )
                try:
                    results = self._service.files().list(
                        q=q, fields="files(id)", pageSize=1
                    ).execute()
                    if results.get("files"):
                        continue
                except Exception as check_err:
                    logging.warning(f"DriveUploader: error verificando existencia de '{rel}': {check_err}")

                if on_progress:
                    on_progress(f"Subiendo a Drive: {file_path.name}")
                try:
                    parts = file_path.relative_to(downloads_dir).parts
                    folder_id = self._root_id
                    for folder_name in parts[:-1]:
                        folder_id = self._get_or_create_folder(folder_name, folder_id)
                    doc_id = db.get_doc_id_by_local_path(rel) or ""
                    meta = db.get_doc_by_id(doc_id) if doc_id else None
                    file_metadata = {
                        "name": parts[-1],
                        "parents": [folder_id],
                        "appProperties": {"local_path": path_hash, "doc_id": doc_id},
                    }
                    media = MediaFileUpload(str(file_path.resolve()), resumable=True)
                    result = self._service.files().create(
                        body=file_metadata, media_body=media, fields="id"
                    ).execute()
                    file_id = result["id"]
                    drive_url = f"https://drive.google.com/file/d/{file_id}/view"
                    count += 1
                    logging.info(f"DriveUploader: subido pendiente {parts[-1]}")
                    if sheets_reporter:
                        source  = parts[0]
                        titulo  = meta["title"] if meta else Path(parts[-1]).stem
                        f_public = meta["f_public"] if meta else ""
                        stem    = Path(parts[-1]).stem
                        tipo    = stem.split("_", 1)[1] if "_" in stem else ""
                        actualizado = sheets_reporter.actualizar_enlace_drive(source, titulo, drive_url)
                        if not actualizado:
                            sheets_reporter.agregar_fila(source, f_public, titulo, tipo, drive_url)
                except Exception as e:
                    msg = f"Error subiendo {file_path.name}: {e}"
                    logging.warning(f"DriveUploader: {msg}")
                    if on_progress:
                        on_progress(msg)
        except Exception as e:
            logging.warning(f"DriveUploader: error en upload_pending_to_drive: {e}")
        return count

    def sync_from_drive(self, downloads_dir, on_progress=None, stop_event=None) -> int:
        if self._service is None:
            return 0
        from googleapiclient.http import MediaIoBaseDownload
        import io

        downloads_dir = Path(downloads_dir)
        count = 0
        try:
            sources = self._list_folder_contents(self._root_id)
            for src in sources:
                if src["mimeType"] != "application/vnd.google-apps.folder":
                    continue
                dates = self._list_folder_contents(src["id"])
                for dt in dates:
                    if dt["mimeType"] != "application/vnd.google-apps.folder":
                        continue
                    tipos = self._list_folder_contents(dt["id"])
                    for tipo in tipos:
                        if tipo["mimeType"] != "application/vnd.google-apps.folder":
                            continue
                        if stop_event and stop_event.is_set():
                            return count
                        files = self._list_folder_contents(tipo["id"])
                        for f in files:
                            if f["mimeType"] == "application/vnd.google-apps.folder":
                                continue
                            local_path = downloads_dir / src["name"] / dt["name"] / tipo["name"] / f["name"]
                            if not local_path.exists():
                                if on_progress:
                                    on_progress(f"Sincronizando desde Drive: {f['name']}")
                                try:
                                    local_path.parent.mkdir(parents=True, exist_ok=True)
                                    request = self._service.files().get_media(fileId=f["id"])
                                    fh = io.BytesIO()
                                    downloader = MediaIoBaseDownload(fh, request)
                                    done = False
                                    while not done:
                                        _, done = downloader.next_chunk()
                                    local_path.write_bytes(fh.getvalue())
                                    count += 1
                                    logging.info(f"DriveUploader: sincronizado {f['name']}")
                                except Exception as e:
                                    logging.warning(f"DriveUploader: error descargando {f['name']}: {e}")
        except Exception as e:
            logging.warning(f"DriveUploader: error en sync_from_drive: {e}")
        return count

    def _list_folder_contents(self, folder_id: str) -> list:
        results, page_token = [], None
        while True:
            resp = (
                self._service.files()
                .list(
                    q=f"'{folder_id}' in parents and trashed=false",
                    fields="nextPageToken, files(id, name, mimeType)",
                    pageSize=200,
                    pageToken=page_token,
                )
                .execute()
            )
            results.extend(resp.get("files", []))
            page_token = resp.get("nextPageToken")
            if not page_token:
                break
        return results

    def delete_file_by_local_path(self, rel_path: str) -> str | None:
        if self._service is None:
            return None
        try:
            q = (
                f"appProperties has {{key='local_path' and value='{_hash_path(rel_path)}'}} "
                f"and trashed=false"
            )
            results = (
                self._service.files()
                .list(q=q, fields="files(id,name)", pageSize=1)
                .execute()
            )
            files = results.get("files", [])
            if files:
                file_id = files[0]["id"]
                drive_url = f"https://drive.google.com/file/d/{file_id}/view"
                self._service.files().delete(fileId=file_id).execute()
                logging.info(f"DriveUploader: eliminado de Drive — {rel_path}")
                return drive_url
        except Exception as e:
            logging.warning(f"DriveUploader: error eliminando {rel_path} de Drive: {e}")
        return None

    def close(self):
        if self._service:
            try:
                self._service.close()
            except Exception:
                pass
            self._service = None
