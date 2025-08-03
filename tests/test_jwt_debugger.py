import base64
import hashlib
import hmac
import json
import time
import unittest

from devdriver.tools.jwt_debugger import JWTDebugger


class TestJWTDebugger(unittest.TestCase):
    """Test cases for JWT Debugger functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.jwt_debugger = JWTDebugger()

        # Sample JWT components
        self.sample_header = {"alg": "HS256", "typ": "JWT"}
        self.sample_payload = {"sub": "1234567890", "name": "John Doe", "iat": 1516239022}
        self.sample_secret = "your-256-bit-secret"  # noqa: S105

        # Create a valid JWT token
        header_b64 = self._base64_url_encode(json.dumps(self.sample_header).encode())
        payload_b64 = self._base64_url_encode(json.dumps(self.sample_payload).encode())
        signing_input = f"{header_b64}.{payload_b64}"

        signature = hmac.new(self.sample_secret.encode(), signing_input.encode(), hashlib.sha256).digest()
        signature_b64 = self._base64_url_encode(signature)

        self.valid_jwt = f"{header_b64}.{payload_b64}.{signature_b64}"

    def _base64_url_encode(self, data: bytes) -> str:
        """Helper method to encode data to base64url format."""
        encoded = base64.b64encode(data).decode("utf-8")
        return encoded.replace("+", "-").replace("/", "_").rstrip("=")

    def test_init(self):
        """Test JWTDebugger initialization."""
        jwt = JWTDebugger()
        self.assertEqual(jwt.header, {})
        self.assertEqual(jwt.payload, {})
        self.assertEqual(jwt.signature, "")
        self.assertEqual(jwt.algorithm, "HS256")
        self.assertEqual(jwt.secret, "")
        self.assertFalse(jwt.is_valid)
        self.assertEqual(jwt.error_message, "")

    def test_base64_url_decode_valid(self):
        """Test base64url decoding with valid input."""
        # Test normal base64url
        data = "SGVsbG8gV29ybGQ"
        result = self.jwt_debugger._base64_url_decode(data)
        self.assertEqual(result, b"Hello World")

        # Test with URL-safe characters
        data = "SGVsbG8tV29ybGRf"
        result = self.jwt_debugger._base64_url_decode(data)
        self.assertEqual(result, b"Hello-World_")

    def test_base64_url_decode_invalid(self):
        """Test base64url decoding with invalid input."""
        with self.assertRaises(ValueError):
            self.jwt_debugger._base64_url_decode("invalid!@#$%")

    def test_base64_url_encode(self):
        """Test base64url encoding."""
        data = b"Hello World"
        result = self.jwt_debugger._base64_url_encode(data)
        self.assertEqual(result, "SGVsbG8gV29ybGQ")

        # Test with characters that need URL-safe encoding
        data = b"Hello-World_"
        result = self.jwt_debugger._base64_url_encode(data)
        self.assertEqual(result, "SGVsbG8tV29ybGRf")

    def test_parse_jwt_valid(self):
        """Test parsing a valid JWT token."""
        success, error = self.jwt_debugger.parse_jwt(self.valid_jwt)

        self.assertTrue(success)
        self.assertEqual(error, "")
        self.assertEqual(self.jwt_debugger.header, self.sample_header)
        self.assertEqual(self.jwt_debugger.payload, self.sample_payload)
        self.assertEqual(self.jwt_debugger.algorithm, "HS256")
        self.assertNotEqual(self.jwt_debugger.signature, "")

    def test_parse_jwt_invalid_format(self):
        """Test parsing JWT with invalid format."""
        # Test with wrong number of parts
        success, error = self.jwt_debugger.parse_jwt("invalid.jwt")
        self.assertFalse(success)
        self.assertIn("Invalid JWT format", error)

        # Test with empty string
        success, error = self.jwt_debugger.parse_jwt("")
        self.assertFalse(success)
        self.assertIn("Invalid JWT format", error)

    def test_parse_jwt_invalid_header(self):
        """Test parsing JWT with invalid header."""
        invalid_jwt = "invalid_header.eyJzdWIiOiIxMjM0NTY3ODkwIn0.signature"
        success, error = self.jwt_debugger.parse_jwt(invalid_jwt)
        self.assertFalse(success)
        self.assertIn("Invalid header", error)

    def test_parse_jwt_invalid_payload(self):
        """Test parsing JWT with invalid payload."""
        header_b64 = self._base64_url_encode(json.dumps(self.sample_header).encode())
        invalid_jwt = f"{header_b64}.invalid_payload.signature"
        success, error = self.jwt_debugger.parse_jwt(invalid_jwt)
        self.assertFalse(success)
        self.assertIn("Invalid payload", error)

    def test_verify_signature_valid(self):
        """Test signature verification with valid JWT and secret."""
        # First parse the JWT
        self.jwt_debugger.parse_jwt(self.valid_jwt)

        # Then verify signature
        is_valid, message = self.jwt_debugger.verify_signature(self.valid_jwt, self.sample_secret)

        self.assertTrue(is_valid)
        self.assertIn("verified successfully", message)
        self.assertTrue(self.jwt_debugger.is_valid)

    def test_verify_signature_invalid_secret(self):
        """Test signature verification with wrong secret."""
        # First parse the JWT
        self.jwt_debugger.parse_jwt(self.valid_jwt)

        # Then verify with wrong secret
        is_valid, message = self.jwt_debugger.verify_signature(self.valid_jwt, "wrong-secret")

        self.assertFalse(is_valid)
        self.assertIn("Invalid signature", message)
        self.assertFalse(self.jwt_debugger.is_valid)

    def test_verify_signature_empty_inputs(self):
        """Test signature verification with empty inputs."""
        is_valid, message = self.jwt_debugger.verify_signature("", "")
        self.assertFalse(is_valid)
        self.assertIn("Token and secret are required", message)

        is_valid, message = self.jwt_debugger.verify_signature(self.valid_jwt, "")
        self.assertFalse(is_valid)
        self.assertIn("Token and secret are required", message)

    def test_verify_signature_unsupported_algorithm(self):
        """Test signature verification with unsupported algorithm."""
        # Create JWT with unsupported algorithm
        header = {"alg": "RS256", "typ": "JWT"}
        header_b64 = self._base64_url_encode(json.dumps(header).encode())
        payload_b64 = self._base64_url_encode(json.dumps(self.sample_payload).encode())
        jwt_token = f"{header_b64}.{payload_b64}.signature"

        # Parse and verify
        self.jwt_debugger.parse_jwt(jwt_token)
        is_valid, message = self.jwt_debugger.verify_signature(jwt_token, self.sample_secret)

        self.assertFalse(is_valid)
        self.assertIn("Unsupported algorithm", message)

    def test_get_header_json_empty(self):
        """Test getting header JSON when empty."""
        result = self.jwt_debugger.get_header_json()
        self.assertEqual(result, "{\n}")

    def test_get_header_json_with_data(self):
        """Test getting header JSON with data."""
        self.jwt_debugger.parse_jwt(self.valid_jwt)
        result = self.jwt_debugger.get_header_json()

        # Parse the result to verify it's valid JSON
        parsed = json.loads(result)
        self.assertEqual(parsed, self.sample_header)

    def test_get_payload_json_empty(self):
        """Test getting payload JSON when empty."""
        result = self.jwt_debugger.get_payload_json()
        self.assertEqual(result, "{\n}")

    def test_get_payload_json_with_data(self):
        """Test getting payload JSON with data."""
        self.jwt_debugger.parse_jwt(self.valid_jwt)
        result = self.jwt_debugger.get_payload_json()

        # Parse the result to verify it's valid JSON
        parsed = json.loads(result)
        self.assertEqual(parsed, self.sample_payload)

    def test_get_signature_formula_default(self):
        """Test getting signature formula with default algorithm."""
        result = self.jwt_debugger.get_signature_formula()
        self.assertIn("HMACSHA256", result)
        self.assertIn("base64UrlEncode", result)

    def test_get_signature_formula_different_algorithm(self):
        """Test getting signature formula with different algorithm."""
        self.jwt_debugger.algorithm = "HS384"
        result = self.jwt_debugger.get_signature_formula()
        self.assertIn("HMACSHA384", result)

        self.jwt_debugger.algorithm = "HS512"
        result = self.jwt_debugger.get_signature_formula()
        self.assertIn("HMACSHA512", result)

    def test_supported_algorithms(self):
        """Test that all supported algorithms are properly defined."""
        expected_algorithms = ["HS256", "HS384", "HS512"]

        for algo in expected_algorithms:
            self.assertIn(algo, JWTDebugger.SUPPORTED_ALGORITHMS)
            self.assertTrue(callable(JWTDebugger.SUPPORTED_ALGORITHMS[algo]))

    def test_algorithm_hs384(self):
        """Test JWT with HS384 algorithm."""
        # Create JWT with HS384
        header = {"alg": "HS384", "typ": "JWT"}
        header_b64 = self._base64_url_encode(json.dumps(header).encode())
        payload_b64 = self._base64_url_encode(json.dumps(self.sample_payload).encode())
        signing_input = f"{header_b64}.{payload_b64}"

        signature = hmac.new(self.sample_secret.encode(), signing_input.encode(), hashlib.sha384).digest()
        signature_b64 = self._base64_url_encode(signature)

        jwt_token = f"{header_b64}.{payload_b64}.{signature_b64}"

        # Parse and verify
        success, _ = self.jwt_debugger.parse_jwt(jwt_token)
        self.assertTrue(success)
        self.assertEqual(self.jwt_debugger.algorithm, "HS384")

        is_valid, _ = self.jwt_debugger.verify_signature(jwt_token, self.sample_secret)
        self.assertTrue(is_valid)

    def test_algorithm_hs512(self):
        """Test JWT with HS512 algorithm."""
        # Create JWT with HS512
        header = {"alg": "HS512", "typ": "JWT"}
        header_b64 = self._base64_url_encode(json.dumps(header).encode())
        payload_b64 = self._base64_url_encode(json.dumps(self.sample_payload).encode())
        signing_input = f"{header_b64}.{payload_b64}"

        signature = hmac.new(self.sample_secret.encode(), signing_input.encode(), hashlib.sha512).digest()
        signature_b64 = self._base64_url_encode(signature)

        jwt_token = f"{header_b64}.{payload_b64}.{signature_b64}"

        # Parse and verify
        success, _ = self.jwt_debugger.parse_jwt(jwt_token)
        self.assertTrue(success)
        self.assertEqual(self.jwt_debugger.algorithm, "HS512")

        is_valid, _ = self.jwt_debugger.verify_signature(jwt_token, self.sample_secret)
        self.assertTrue(is_valid)

    def test_check_expiration_no_payload(self):
        """Test expiration check with no payload."""
        is_expired, message = self.jwt_debugger.check_expiration()
        self.assertFalse(is_expired)
        self.assertIn("No payload to check", message)

    def test_check_expiration_no_exp_claim(self):
        """Test expiration check with no exp claim."""
        self.jwt_debugger.payload = {"sub": "1234567890", "name": "John Doe"}
        is_expired, message = self.jwt_debugger.check_expiration()
        self.assertFalse(is_expired)
        self.assertIn("No expiration claim found", message)

    def test_check_expiration_expired_token(self):
        """Test expiration check with expired token."""
        # Create payload with past expiration time
        past_timestamp = int(time.time()) - 3600  # 1 hour ago
        self.jwt_debugger.payload = {"sub": "1234567890", "name": "John Doe", "exp": past_timestamp}

        is_expired, message = self.jwt_debugger.check_expiration()
        self.assertTrue(is_expired)
        self.assertIn("Token expired on", message)

    def test_check_expiration_valid_token(self):
        """Test expiration check with valid token."""
        # Create payload with future expiration time
        future_timestamp = int(time.time()) + 3600  # 1 hour from now
        self.jwt_debugger.payload = {"sub": "1234567890", "name": "John Doe", "exp": future_timestamp}

        is_expired, message = self.jwt_debugger.check_expiration()
        self.assertFalse(is_expired)
        self.assertIn("Token valid until", message)

    def test_check_expiration_invalid_format(self):
        """Test expiration check with invalid exp format."""
        self.jwt_debugger.payload = {"sub": "1234567890", "name": "John Doe", "exp": "invalid_timestamp"}

        is_expired, message = self.jwt_debugger.check_expiration()
        self.assertFalse(is_expired)
        self.assertIn("Invalid expiration claim format", message)


if __name__ == "__main__":
    unittest.main()
