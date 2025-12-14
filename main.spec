import sys
import os
from PyInstaller.utils.hooks import collect_data_files

block_cipher = None

# Hidden imports for lazily-loaded tool modules
# These modules are imported dynamically at runtime, so PyInstaller needs to be told about them
hidden_tool_imports = [
    'devboost.tools.api_inspector',
    'devboost.tools.base64_string_encodec',
    'devboost.tools.block_editor',
    'devboost.tools.color_converter',
    'devboost.tools.cron_expression_editor',
    'devboost.tools.file_optimization',
    'devboost.tools.file_rename',
    'devboost.tools.graphql_client',
    'devboost.tools.http_client',
    'devboost.tools.ip_subnet_calculator',
    'devboost.tools.json_diff',
    'devboost.tools.json_format_validate',
    'devboost.tools.jwt_debugger',
    'devboost.tools.llm_client',
    'devboost.tools.lorem_ipsum_generator',
    'devboost.tools.markdown_viewer',
    'devboost.tools.openapi_mock_server',
    'devboost.tools.random_string_generator',
    'devboost.tools.regex_tester',
    'devboost.tools.ripgrep_search',
    'devboost.tools.scratch_pad',
    'devboost.tools.string_case_converter',
    'devboost.tools.timezone_converter',
    'devboost.tools.unit_converter',
    'devboost.tools.unix_time_converter',
    'devboost.tools.url_encode_decode',
    'devboost.tools.uuid_ulid_generator',
    'devboost.tools.uvx_runner',
    'devboost.tools.xml_beautifier',
    'devboost.tools.yaml_to_json',
]

a = Analysis(['main_cli.py'],
             pathex=['.'],
             binaries=None,
             datas=[],
             hiddenimports=hidden_tool_imports,
             hookspath=None,
             runtime_hooks=None,
             excludes=None,
             cipher=block_cipher)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(pyz,
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas,
          [],
          name='DevBoost',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          runtime_tmpdir=None,
          console=False)

app = BUNDLE(exe,
             name='DevBoost.app',
             icon='assets/icon.icns',
             bundle_identifier='com.github.namuan.devboost',
             info_plist={
                 'CFBundleName': 'DevBoost',
                 'CFBundleVersion': '1.0.0',
                 'CFBundleShortVersionString': '1.0.0',
                 'NSPrincipalClass': 'NSApplication',
                 'NSHighResolutionCapable': True,
                 }
              )
