import json
import logging
from typing import Any, Callable

import requests

logger = logging.getLogger("debuger")


class Mars:
    URL = ""
    headers = {"Content-Type": "application/json", "Authorization": ""}

    def __init__(self, username: str, password: str, token: str, client_id: str) -> None:
        self.username = username
        self.password = password
        self.token = token
        self.client_id = client_id

    def refresh_token(self) -> None:
        url = "https://api.metronom.dev/uaa/oauth/token"
        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Authorization": f"Basic {self.token}",
        }
        params = {
            "grant_type": "password",
            "username": self.username,
            "password": self.password,
        }
        response = requests.get(url=url, headers=headers, params=params, verify=False, timeout=20)
        token = response.json().get("access_token", "")
        self.headers["Authorization"] = f"Bearer {token}"

    @staticmethod
    def status_code(func: Callable) -> Callable:
        def wrapper(self, *args, **kwargs) -> list[dict[str, Any]] | dict[str, Any]:
            response = func(self, *args, **kwargs)
            match response.status_code:
                case 200:
                    data = response.json()
                case 401:
                    self.refresh_token()
                    data = func(self, *args, **kwargs).json()
                case 500:
                    return {"error": "Server error 500"}
            return json.loads(data.get("result", []))

        return wrapper

    @status_code
    def run_iql(self, iql: str, scheme: int, results: int = 500):
        url = self.URL + "/iql/run"
        json = {
            "iql": iql,
            "client_id": self.client_id,
            "scheme": scheme,
            "options": {
                "resultPerPage": results,
                "includeAttributes": True,
            },
        }
        response = requests.post(url=url, headers=self.headers, json=json, verify=False, timeout=20)
        return response

    def decode(self, obj: dict[str, Any], fields: dict[str, Any]) -> dict[str, str | int]:
        obj_dict: dict[str, int | str] = dict()
        for attr in obj["attributes"]:
            attr_id = attr["objectTypeAttributeId"]
            key = fields.get(attr_id)
            attr_val = False
            for a in attr["objectAttributeValues"]:
                attr_val_tmp = a["displayValue"]
                match attr_val:
                    case bool():
                        attr_val = attr_val_tmp
                    case list():
                        attr_val.append(attr_val_tmp)
                    case _:
                        attr_val = [attr_val]
            if key:
                obj_dict[fields[attr_id]] = attr_val
        return obj_dict

    def search(self, item_type: int, scheme: int, iql: str = "") -> list[dict[str, int | str]]:
        iql = f'{iql + " AND " if iql else ''}objectType = "{item_type}"'
        objs = self.run_iql(iql=iql, scheme=scheme, results=500)
        fields = {attr["id"]: attr["name"] for attr in objs.get("objectTypeAttributes", {})}
        return [self.decode(obj, fields) for obj in objs.get("objectEntries", [])] if objs else []
