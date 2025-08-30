import sys
import unittest
from pathlib import Path

# Add the project root to the path
sys.path.insert(0, str(Path(__file__).parent.parent.resolve()))

from devboost.tools.uvx_runner import UVX_TOOLS


class TestUvxRunnerFilter(unittest.TestCase):
    def test_uvx_tools_constant(self):
        """Test that UVX_TOOLS constant is properly defined"""
        # Check that UVX_TOOLS is a dictionary
        self.assertIsInstance(UVX_TOOLS, dict)

        # Check that it has some tools
        self.assertGreater(len(UVX_TOOLS), 0)

        # Check that all tools have string names and descriptions
        for tool_name, description in UVX_TOOLS.items():
            self.assertIsInstance(tool_name, str)
            self.assertIsInstance(description, str)
            self.assertGreater(len(tool_name), 0)
            self.assertGreater(len(description), 0)


if __name__ == "__main__":
    unittest.main()
