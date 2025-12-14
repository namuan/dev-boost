"""
Lazy loader for tool widgets to improve application startup time.

This module provides on-demand importing of tool modules, deferring the heavy
import cost until the user actually selects a specific tool.
"""

import logging
import time
from collections.abc import Callable
from typing import Any

logger = logging.getLogger(__name__)

# Registry mapping tool names to their module paths and factory function names
TOOL_REGISTRY: dict[str, tuple[str, str]] = {
    "API Inspector": ("devboost.tools.api_inspector", "create_api_inspector_widget"),
    "Base64 String Encode/Decode": ("devboost.tools.base64_string_encodec", "create_base64_string_encodec_widget"),
    "Block Editor": ("devboost.tools.block_editor", "create_blocks_editor_widget"),
    "Color Converter": ("devboost.tools.color_converter", "create_color_converter_widget"),
    "Cron Expression Editor": ("devboost.tools.cron_expression_editor", "create_cron_expression_editor_widget"),
    "File Optimization Tool": ("devboost.tools.file_optimization", "create_file_optimization_widget"),
    "File Rename Tool": ("devboost.tools.file_rename", "create_file_rename_widget"),
    "GraphQL Client": ("devboost.tools.graphql_client", "create_graphql_client_widget"),
    "HTTP Client": ("devboost.tools.http_client", "create_http_client_widget"),
    "IP Subnet Calculator": ("devboost.tools.ip_subnet_calculator", "create_ip_subnet_calculator_widget"),
    "JSON Diff": ("devboost.tools.json_diff", "create_json_diff_widget"),
    "JSON Format/Validate": ("devboost.tools.json_format_validate", "create_json_formatter_widget"),
    "JWT Debugger": ("devboost.tools.jwt_debugger", "create_jwt_debugger_widget"),
    "LLM Client": ("devboost.tools.llm_client", "create_llm_client_widget"),
    "Lorem Ipsum Generator": ("devboost.tools.lorem_ipsum_generator", "create_lorem_ipsum_tool_widget"),
    "Markdown Viewer": ("devboost.tools.markdown_viewer", "create_markdown_preview_widget"),
    "OpenAPI Mock Server": ("devboost.tools.openapi_mock_server", "create_openapi_mock_server_widget"),
    "Random String Generator": ("devboost.tools.random_string_generator", "create_random_string_tool_widget"),
    "RegExp Tester": ("devboost.tools.regex_tester", "create_regexp_tester_widget"),
    "Ripgrep Search": ("devboost.tools.ripgrep_search", "create_ripgrep_search_widget"),
    "Scratch Pad": ("devboost.tools.scratch_pad", "create_scratch_pad_widget"),
    "String Case Converter": ("devboost.tools.string_case_converter", "create_case_converter_widget"),
    "TimeZone Converter": ("devboost.tools.timezone_converter", "create_timezone_converter_widget"),
    "Unit Converter": ("devboost.tools.unit_converter", "create_unit_converter_widget"),
    "Unix Time Converter": ("devboost.tools.unix_time_converter", "create_unix_time_converter_widget"),
    "URL Encode/Decode": ("devboost.tools.url_encode_decode", "create_url_codec_widget"),
    "UUID/ULID Generate/Decode": ("devboost.tools.uuid_ulid_generator", "create_uuid_ulid_tool_widget"),
    "Uvx Runner": ("devboost.tools.uvx_runner", "create_uvx_runner_widget"),
    "XML Beautifier": ("devboost.tools.xml_beautifier", "create_xml_formatter_widget"),
    "YAML to JSON": ("devboost.tools.yaml_to_json", "create_yaml_to_json_widget"),
}

# Cache for imported factory functions
_factory_cache: dict[str, Callable] = {}


def get_tool_factory(tool_name: str) -> Callable | None:
    """
    Get the factory function for a tool, importing the module lazily if needed.

    Args:
        tool_name: The display name of the tool (e.g., "Markdown Viewer")

    Returns:
        The factory function to create the tool widget, or None if not found.
    """
    # Check cache first
    if tool_name in _factory_cache:
        logger.debug("Using cached factory for %s", tool_name)
        return _factory_cache[tool_name]

    # Look up the tool in the registry
    if tool_name not in TOOL_REGISTRY:
        logger.warning("Tool '%s' not found in registry", tool_name)
        return None

    module_path, factory_name = TOOL_REGISTRY[tool_name]

    # Import the module lazily
    start_time = time.perf_counter()
    try:
        import importlib

        module = importlib.import_module(module_path)
        factory = getattr(module, factory_name)

        elapsed = (time.perf_counter() - start_time) * 1000
        logger.info("LAZY_LOAD: Imported %s in %.1fms", tool_name, elapsed)

        # Cache the factory
        _factory_cache[tool_name] = factory
        return factory

    except (ImportError, AttributeError):
        elapsed = (time.perf_counter() - start_time) * 1000
        # logging.exception automatically includes the exception info; don't add
        # the exception object to the formatted message to satisfy linting rules
        logger.exception("Failed to import %s (%.1fms)", tool_name, elapsed)
        return None


def create_tool_widget(tool_name: str, style_func: Any = None, scratch_pad: Any = None) -> Any:
    """
    Create a tool widget by lazily loading its module and calling the factory.

    Args:
        tool_name: The display name of the tool
        style_func: The style function to pass to the widget factory
        scratch_pad: The scratch pad widget to pass to the widget factory

    Returns:
        The created widget, or None if creation failed.
    """
    factory = get_tool_factory(tool_name)
    if factory is None:
        return None

    try:
        # Some widgets don't take scratch_pad argument
        if tool_name in ("Block Editor", "Scratch Pad"):
            return factory(style_func)
        return factory(style_func, scratch_pad)
    except Exception:
        # logging.exception will include the current exception; keep message
        # focused on the operation and avoid interpolating the exception object
        logger.exception("Failed to create widget for %s", tool_name)
        return None


def preload_tool(tool_name: str) -> None:
    """
    Preload a tool's module in the background (for anticipated use).

    Args:
        tool_name: The display name of the tool to preload
    """
    get_tool_factory(tool_name)
