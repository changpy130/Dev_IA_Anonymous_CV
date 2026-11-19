from dataclasses import dataclass

import pandas as pd
import requests


class N8nError(Exception):
    pass

class CvRejectedError(N8nError):
    """The pipeline refused this CV. The user can fix it."""


@dataclass(frozen=True)
class UploadResult:
    code: str
    link: str
    alertes: int


class N8nClient:
    def __init__(self, base_url: str, api_key: str, timeout: int = 120):
        self._base = base_url.rstrip("/")
        self._headers = {"X-API-Key": api_key}
        self._timeout = timeout

    def upload_cv(self, file_name: str, content: bytes, mime: str) -> UploadResult:
        # HTTP multipart/form-data (file_name, content, mime) is the universal format for uploading files.
        data = self._request("POST", "cv-upload", files={"CV": (file_name, content, mime)})  # content: raw bytes; mime: file type, e.g. pdf
        return UploadResult(data["code"], data["link"], int(data["alertes"]))

    def list_consultants(self) -> pd.DataFrame:
        return pd.DataFrame(self._request("GET", "consultants"))

    def _request(self, method: str, path: str, **kwargs):
        try:
            response = requests.request(
                method, f"{self._base}/webhook/{path}",
                headers=self._headers, timeout=self._timeout, **kwargs,
            )
            
            if response.status_code == 422:
                raise CvRejectedError(response.json().get("message", "CV refusé."))
            
            response.raise_for_status()
            return response.json()
        
        except (requests.RequestException, ValueError) as exc:
            raise N8nError(f"n8n call failed ({path}): {exc}") from exc