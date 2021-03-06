from loguru import logger
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.routing import Match
from fastapi import Depends, FastAPI, Query, Request
from anonymizeip import anonymize_ip
import json

MONITORING_MESSAGE = "|{masked_ip}|{client}|{special}|{method}|{url}|{headers}|{params}"


class MonitoringMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request_info = extract_request(request)
        monitoring_info = format_monitoring_info(request_info)
        # logging
        # logger.info(monitoring_info)
        logger.bind(es=True, debug=True).info(monitoring_info)
        # finish
        response = await call_next(request)
        return response


def extract_request(request: Request):
    # Process headers and remove cookie field
    headers = dict(request.headers)
    info = {
        "method": request.method,
        "url": {
            "url": str(request.url),
            "path": request.url.path,
            "port": request.url.port,
            "scheme": request.url.scheme,
        },
        "params": {
            "query_params": dict(request.query_params),
            "path_params": dict(request.path_params),
        },
        "client": {"host": request.client.host},
        "headers": headers,
    }
    return info


def special_headers(headers) -> str:
    """Mark incoming request for whether it is for special usage:
    unit tests, client package building, etc
    If True, returns "special", otherwise returns "normal".
    """
    if "client-type" in headers.keys():
        if headers["client-type"] == "pytest":
            return "special"
    if "ci" in headers.keys() and json.loads(headers["ci"].lower()):
        return "special"
    return "normal"


def get_masked_ip(headers):
    if "x-forwarded-for" in headers.keys():
        field = "x-forwarded-for"
    elif "X-Forwarded-For" in headers.keys():
        field = "X-Forwarded-For"
    else:
        return None
    x_forwarded_for = headers[field]
    masked_ip = None
    try:
        # "1.2.3.4, 1.2.3.4" -> "1.2.3.4" the last field
        if "," in x_forwarded_for:
            ip = x_forwarded_for.split(",")[-1].strip()
        else:
            ip = x_forwarded_for
        # "1.2.3.4" -> "1.2.3.0"
        masked_ip = anonymize_ip(ip)
    except:
        return None
    return masked_ip


def format_monitoring_info(info):
    headers = info["headers"]
    params = info["params"]
    special = special_headers(headers)
    masked_ip = get_masked_ip(headers)
    filtered_headers = filter_headers(headers)
    client = "others"
    if "client-type" in headers:
        client = headers["client-type"]
    message = MONITORING_MESSAGE.format(
        masked_ip=masked_ip,
        client=client,
        special=special,
        method=info["method"],
        url=json.dumps(info["url"]),
        headers=json.dumps(filtered_headers),
        params=json.dumps(params["query_params"]),
    )
    return message


def filter_headers(headers):
    filtered_headers = headers
    filtered_headers.pop("cookie", None)
    filtered_headers.pop("x-forwarded-for", None)
    filtered_headers.pop("X-Forwarded-For", None)
    return filtered_headers


# logger handlers
logger.add(
    "logs/elasticsearch.log",
    format="{time:YYYY-MM-DD HH:mm:ss} {message}",
    filter=lambda record: "es" in record["extra"],
    enqueue=False,
    rotation="7 days",
    retention="7 days",
    compression="tar.gz",
    backtrace=False,
    # catch=False,
    # serialize=True,
)
logger.add(
    "logs/debug.log",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {file}:{line} | {message}",
    filter=lambda record: "debug" in record["extra"],
    rotation="7 days",
    compression="tar.gz",
)
