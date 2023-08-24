import os
import re
from datetime import datetime
from typing import Any

import pystac
import requests


def url_validate(target: str) -> bool:
    """Validate whether a supplied URL is reliably written.

    Parameters
    ----------
    target : str

    References
    ----------
    https://stackoverflow.com/a/7160778/7322852
    """
    url_regex = re.compile(
        r"^(?:http|ftp)s?://"  # http:// or https://
        # domain...
        r"(?:(?:[A-Z\d](?:[A-Z\d-]{0,61}[A-Z\d])?\.)+(?:[A-Z]{2,6}\.?|[A-Z\d-]{2,}\.?)|"
        r"localhost|"  # localhost...
        r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})"  # ...or ip
        r"(?::\d+)?"  # optional port
        r"(?:/?|[/?]\S+)$",
        re.IGNORECASE,
    )
    return True if re.match(url_regex, target) else False


def stac_host_reachable(url: str) -> bool:
    try:
        registry = requests.get(url)
        registry.raise_for_status()
        return True
    except (requests.exceptions.RequestException, requests.exceptions.ConnectionError):
        return False


def stac_collection_exists(stac_host: str, collection_id: str) -> bool:
    """
    Get a STAC collection

    Returns the collection JSON.
    """
    r = requests.get(os.path.join(stac_host, "collections", collection_id), verify=False)

    return r.status_code == 200


def create_stac_collection(collection_id: str, collection_info: dict[str, Any]) -> dict[str, Any]:
    """
    Create a basic STAC collection.

    Returns the collection.
    """

    sp_extent = pystac.SpatialExtent([collection_info.pop("spatialextent")])
    tmp = collection_info.pop("temporalextent")
    tmp_extent = pystac.TemporalExtent(
        [
            [
                datetime.strptime(tmp[0], "%Y-%m-%d") if tmp[0] is not None else None,
                datetime.strptime(tmp[1], "%Y-%m-%d") if tmp[1] is not None else None,
            ]
        ]
    )
    collection_info["extent"] = pystac.Extent(sp_extent, tmp_extent)
    collection_info["summaries"] = pystac.Summaries({"needs_summaries_update": ["true"]})

    collection = pystac.Collection(id=collection_id, **collection_info)

    return collection.to_dict()


def post_stac_collection(stac_host: str, json_data: dict[str, Any]) -> None:
    """
    Post a STAC collection.

    Returns the collection id.
    """
    collection_id = json_data["id"]
    r = requests.post(os.path.join(stac_host, "collections"), json=json_data, verify=False)

    if r.status_code == 200:
        print(
            f"{bcolors.OKGREEN}[INFO] Pushed STAC collection [{collection_id}] to [{stac_host}] ({r.status_code}){bcolors.ENDC}"
        )
    elif r.status_code == 409:
        print(
            f"{bcolors.WARNING}[INFO] STAC collection [{collection_id}] already exists on [{stac_host}] ({r.status_code}), updating..{bcolors.ENDC}"
        )
        r = requests.put(os.path.join(stac_host, "collections"), json=json_data, verify=False)
        r.raise_for_status()
    else:
        r.raise_for_status()


def post_stac_item(stac_host: str, collection_id: str, data: dict[str, dict]) -> bool:
    pass
