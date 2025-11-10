"""Utilities - XML parsing, caching, and structured logging."""

from xml_lib.utils.xml_utils import stream_parse, parse_xml
from xml_lib.utils.cache import SchemaCache
from xml_lib.utils.logging import get_logger, structured_log

__all__ = ["stream_parse", "parse_xml", "SchemaCache", "get_logger", "structured_log"]
