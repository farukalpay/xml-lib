"""Utilities - XML parsing, caching, and structured logging."""

from xml_lib.utils.cache import SchemaCache
from xml_lib.utils.logging import get_logger, structured_log
from xml_lib.utils.xml_utils import parse_xml, stream_parse

__all__ = ["stream_parse", "parse_xml", "SchemaCache", "get_logger", "structured_log"]
