import os
import sys
import unittest

# Add the project root to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from devboost.tools.pipx_runner import PIPX_TOOLS


class TestPipxRunnerFilter(unittest.TestCase):
    def test_pipx_tools_constant(self):
        """Test that PIPX_TOOLS constant is properly defined"""
        # Check that PIPX_TOOLS is a dictionary
        self.assertIsInstance(PIPX_TOOLS, dict)

        # Check that it has some tools
        self.assertGreater(len(PIPX_TOOLS), 0)

        # Check that all tools have string names and descriptions
        for tool_name, description in PIPX_TOOLS.items():
            self.assertIsInstance(tool_name, str)
            self.assertIsInstance(description, str)
            self.assertGreater(len(tool_name), 0)
            self.assertGreater(len(description), 0)


if __name__ == "__main__":
    unittest.main()
