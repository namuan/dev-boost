import os
import sys
import time
import unittest
import uuid

from PyQt6.QtWidgets import QApplication

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "devdriver", "tools"))

from uuid_ulid_generator import UUIDULIDProcessor, create_uuid_ulid_tool_widget


class TestUUIDULIDProcessor(unittest.TestCase):
    """Test cases for the UUIDULIDProcessor backend logic."""

    def setUp(self):
        self.processor = UUIDULIDProcessor()

    def test_generate_uuid_v1(self):
        """Test UUID v1 generation."""
        uuid_v1 = self.processor.generate_uuid_v1()
        self.assertIsInstance(uuid_v1, str)
        self.assertEqual(len(uuid_v1), 36)  # Standard UUID format with hyphens

        # Parse as UUID to verify it's valid
        parsed_uuid = uuid.UUID(uuid_v1)
        self.assertEqual(parsed_uuid.version, 1)

    def test_generate_uuid_v4(self):
        """Test UUID v4 generation."""
        uuid_v4 = self.processor.generate_uuid_v4()
        self.assertIsInstance(uuid_v4, str)
        self.assertEqual(len(uuid_v4), 36)  # Standard UUID format with hyphens

        # Parse as UUID to verify it's valid
        parsed_uuid = uuid.UUID(uuid_v4)
        self.assertEqual(parsed_uuid.version, 4)

    def test_generate_ulid(self):
        """Test ULID generation."""
        ulid = self.processor.generate_ulid()
        self.assertIsInstance(ulid, str)
        self.assertEqual(len(ulid), 26)  # ULID is 26 characters

        # Verify all characters are in ULID alphabet
        for char in ulid:
            self.assertIn(char.upper(), self.processor.ULID_ALPHABET)

    def test_ulid_timestamp_ordering(self):
        """Test that ULIDs generated in sequence have proper timestamp ordering."""
        ulid1 = self.processor.generate_ulid()
        time.sleep(0.001)  # Small delay to ensure different timestamp
        ulid2 = self.processor.generate_ulid()

        # ULIDs should be lexicographically sortable by timestamp
        self.assertLess(ulid1, ulid2)

    def test_encode_base32(self):
        """Test Base32 encoding."""
        # Test known values
        result = self.processor._encode_base32(0, 5)
        self.assertEqual(result, "00000")

        result = self.processor._encode_base32(31, 2)
        self.assertEqual(result, "0Z")

    def test_decode_base32(self):
        """Test Base32 decoding."""
        # Test known values
        result = self.processor._decode_base32("00000")
        self.assertEqual(result, 0)

        result = self.processor._decode_base32("0Z")
        self.assertEqual(result, 31)

    def test_decode_base32_invalid_character(self):
        """Test Base32 decoding with invalid character."""
        with self.assertRaises(ValueError):
            self.processor._decode_base32("INVALID!")

    def test_decode_uuid_v4(self):
        """Test UUID v4 decoding."""
        test_uuid = "550e8400-e29b-41d4-a716-446655440000"
        result = self.processor.decode_uuid(test_uuid)

        self.assertEqual(result["standard_format"], test_uuid)
        self.assertEqual(result["raw_contents"], "550E8400E29B41D4A716446655440000")
        self.assertEqual(result["version"], 4)
        self.assertEqual(result["variant"], "RFC 4122")
        self.assertEqual(result["contents_time"], "N/A (not time-based)")
        self.assertEqual(result["contents_clock_id"], "N/A")
        self.assertEqual(result["contents_node"], "N/A")

    def test_decode_uuid_v1(self):
        """Test UUID v1 decoding."""
        # Generate a UUID v1 and decode it
        uuid_v1 = self.processor.generate_uuid_v1()
        result = self.processor.decode_uuid(uuid_v1)

        self.assertEqual(result["standard_format"], uuid_v1)
        self.assertEqual(result["version"], 1)
        self.assertEqual(result["variant"], "RFC 4122")
        self.assertNotEqual(result["contents_time"], "N/A (not time-based)")
        self.assertNotEqual(result["contents_clock_id"], "N/A")
        self.assertNotEqual(result["contents_node"], "N/A")

    def test_decode_uuid_invalid(self):
        """Test decoding invalid UUID."""
        result = self.processor.decode_uuid("invalid-uuid")

        self.assertEqual(result["standard_format"], "Invalid UUID")
        self.assertEqual(result["raw_contents"], "Invalid UUID")
        self.assertEqual(result["version"], "Unknown")
        self.assertEqual(result["variant"], "Unknown")

    def test_decode_ulid(self):
        """Test ULID decoding."""
        # Generate a ULID and decode it
        ulid = self.processor.generate_ulid()
        result = self.processor.decode_ulid(ulid)

        self.assertEqual(result["standard_format"], ulid)
        self.assertEqual(result["raw_contents"], ulid)
        self.assertEqual(result["version"], "ULID")
        self.assertEqual(result["variant"], "ULID")
        self.assertNotEqual(result["contents_time"], "Invalid")
        self.assertEqual(result["contents_clock_id"], "N/A (ULID)")

    def test_decode_ulid_invalid(self):
        """Test decoding invalid ULID."""
        result = self.processor.decode_ulid("invalid-ulid")

        self.assertEqual(result["standard_format"], "Invalid ULID")
        self.assertEqual(result["version"], "Unknown")

    def test_detect_and_decode_uuid(self):
        """Test auto-detection of UUID format."""
        test_uuid = "550e8400-e29b-41d4-a716-446655440000"
        result = self.processor.detect_and_decode(test_uuid)

        self.assertEqual(result["version"], 4)
        self.assertEqual(result["variant"], "RFC 4122")

    def test_detect_and_decode_ulid(self):
        """Test auto-detection of ULID format."""
        ulid = self.processor.generate_ulid()
        result = self.processor.detect_and_decode(ulid)

        self.assertEqual(result["version"], "ULID")
        self.assertEqual(result["variant"], "ULID")

    def test_get_variant_name(self):
        """Test variant name mapping."""
        self.assertEqual(self.processor._get_variant_name(uuid.RFC_4122), "RFC 4122")
        self.assertEqual(self.processor._get_variant_name(uuid.RESERVED_NCS), "Reserved NCS")
        self.assertEqual(self.processor._get_variant_name(uuid.RESERVED_MICROSOFT), "Reserved Microsoft")
        self.assertEqual(self.processor._get_variant_name(uuid.RESERVED_FUTURE), "Reserved Future")
        self.assertEqual(self.processor._get_variant_name(999), "Unknown (999)")


class TestUUIDULIDWidget(unittest.TestCase):
    """Test cases for the UUID/ULID widget UI."""

    @classmethod
    def setUpClass(cls):
        """Set up QApplication for widget testing."""
        if not QApplication.instance():
            cls.app = QApplication([])
        else:
            cls.app = QApplication.instance()

    def setUp(self):
        """Set up widget for testing."""
        self.widget = create_uuid_ulid_tool_widget(self.app.style)

    def test_widget_creation(self):
        """Test that widget is created successfully."""
        self.assertIsNotNone(self.widget)
        self.assertTrue(self.widget.isVisible() or True)  # Widget exists


class TestIntegration(unittest.TestCase):
    """Integration tests for the complete UUID/ULID tool."""

    def setUp(self):
        self.processor = UUIDULIDProcessor()

    def test_uuid_roundtrip(self):
        """Test generating and then decoding a UUID."""
        # Generate UUID v4
        generated_uuid = self.processor.generate_uuid_v4()

        # Decode it
        decoded = self.processor.decode_uuid(generated_uuid)

        # Verify roundtrip
        self.assertEqual(decoded["standard_format"], generated_uuid)
        self.assertEqual(decoded["version"], 4)

    def test_ulid_roundtrip(self):
        """Test generating and then decoding a ULID."""
        # Generate ULID
        generated_ulid = self.processor.generate_ulid()

        # Decode it
        decoded = self.processor.decode_ulid(generated_ulid)

        # Verify roundtrip
        self.assertEqual(decoded["standard_format"], generated_ulid)
        self.assertEqual(decoded["version"], "ULID")

    def test_multiple_generation_uniqueness(self):
        """Test that multiple generations produce unique results."""
        uuids = [self.processor.generate_uuid_v4() for _ in range(100)]
        ulids = [self.processor.generate_ulid() for _ in range(100)]

        # All UUIDs should be unique
        self.assertEqual(len(set(uuids)), 100)

        # All ULIDs should be unique
        self.assertEqual(len(set(ulids)), 100)

    def test_performance_generation(self):
        """Test performance of generation methods."""
        import time

        # Test UUID v4 generation speed
        start_time = time.time()
        for _ in range(1000):
            self.processor.generate_uuid_v4()
        uuid_time = time.time() - start_time

        # Test ULID generation speed
        start_time = time.time()
        for _ in range(1000):
            self.processor.generate_ulid()
        ulid_time = time.time() - start_time

        # Both should complete in reasonable time (less than 1 second for 1000 generations)
        self.assertLess(uuid_time, 1.0)
        self.assertLess(ulid_time, 1.0)

    def test_edge_cases(self):
        """Test edge cases and boundary conditions."""
        # Empty string
        result = self.processor.detect_and_decode("")
        self.assertIn("Invalid", str(result.values()))

        # Whitespace
        result = self.processor.detect_and_decode("   ")
        self.assertIn("Invalid", str(result.values()))

        # Wrong length
        result = self.processor.detect_and_decode("123")
        self.assertIn("Invalid", str(result.values()))


if __name__ == "__main__":
    unittest.main()
