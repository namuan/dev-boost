"""Tests for IP Subnet Calculator tool."""

import ipaddress

from devboost.tools.ip_subnet_calculator import IPConverter, IPSubnetCalculator


class TestIPSubnetCalculator:
    """Test cases for IPSubnetCalculator class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.calculator = IPSubnetCalculator()

    def test_parse_ipv4_with_cidr(self):
        """Test parsing IPv4 address with CIDR notation."""
        network = self.calculator.parse_ip_input("192.168.1.0/24")
        assert network is not None
        assert isinstance(network, ipaddress.IPv4Network)
        assert str(network) == "192.168.1.0/24"
        assert network.prefixlen == 24

    def test_parse_ipv4_without_cidr(self):
        """Test parsing IPv4 address without CIDR notation."""
        network = self.calculator.parse_ip_input("192.168.1.1")
        assert network is not None
        assert isinstance(network, ipaddress.IPv4Network)
        assert str(network) == "192.168.1.1/32"
        assert network.prefixlen == 32

    def test_parse_ipv6_with_cidr(self):
        """Test parsing IPv6 address with CIDR notation."""
        network = self.calculator.parse_ip_input("2001:db8::/32")
        assert network is not None
        assert isinstance(network, ipaddress.IPv6Network)
        assert str(network) == "2001:db8::/32"
        assert network.prefixlen == 32

    def test_parse_ipv6_without_cidr(self):
        """Test parsing IPv6 address without CIDR notation."""
        network = self.calculator.parse_ip_input("2001:db8::1")
        assert network is not None
        assert isinstance(network, ipaddress.IPv6Network)
        assert str(network) == "2001:db8::1/128"
        assert network.prefixlen == 128

    def test_parse_invalid_ip(self):
        """Test parsing invalid IP address."""
        network = self.calculator.parse_ip_input("invalid.ip.address")
        assert network is None

    def test_parse_empty_input(self):
        """Test parsing empty input."""
        network = self.calculator.parse_ip_input("")
        assert network is None

    def test_get_network_info_ipv4(self):
        """Test getting network information for IPv4."""
        network = ipaddress.IPv4Network("192.168.1.0/24")
        info = self.calculator.get_network_info(network)

        assert info["Network Address"] == "192.168.1.0"
        assert info["Broadcast Address"] == "192.168.1.255"
        assert info["Netmask"] == "255.255.255.0"
        assert info["CIDR Notation"] == "192.168.1.0/24"
        assert info["Prefix Length"] == "24"
        assert info["Total Addresses"] == "256"
        assert info["Usable Hosts"] == "254"
        assert info["IP Version"] == "IPv4"
        assert info["Network Class"] == "C"

    def test_get_network_info_ipv6(self):
        """Test getting network information for IPv6."""
        network = ipaddress.IPv6Network("2001:db8::/32")
        info = self.calculator.get_network_info(network)

        assert info["Network Address"] == "2001:db8::"
        assert info["CIDR Notation"] == "2001:db8::/32"
        assert info["Prefix Length"] == "32"
        assert info["IP Version"] == "IPv6"

    def test_subnet_split_ipv4(self):
        """Test splitting IPv4 subnet."""
        network = ipaddress.IPv4Network("192.168.1.0/24")
        subnets = self.calculator.subnet_split(network, 26)

        assert len(subnets) == 4
        assert str(subnets[0]) == "192.168.1.0/26"
        assert str(subnets[1]) == "192.168.1.64/26"
        assert str(subnets[2]) == "192.168.1.128/26"
        assert str(subnets[3]) == "192.168.1.192/26"

    def test_subnet_split_invalid_prefix(self):
        """Test splitting subnet with invalid prefix."""
        network = ipaddress.IPv4Network("192.168.1.0/24")
        subnets = self.calculator.subnet_split(network, 20)  # Smaller prefix

        assert len(subnets) == 0

    def test_supernet_summary_ipv4(self):
        """Test creating supernet from IPv4 networks."""
        networks = ["192.168.1.0/26", "192.168.1.64/26", "192.168.1.128/26", "192.168.1.192/26"]
        supernet = self.calculator.supernet_summary(networks)

        assert supernet is not None
        assert str(supernet) == "192.168.1.0/24"

    def test_supernet_summary_mixed_versions(self):
        """Test creating supernet from mixed IP versions."""
        networks = ["192.168.1.0/24", "2001:db8::/32"]
        supernet = self.calculator.supernet_summary(networks)

        assert supernet is None

    def test_get_address_range(self):
        """Test getting address range from network."""
        network = ipaddress.IPv4Network("192.168.1.0/30")
        addresses = self.calculator.get_address_range(network, limit=5)

        assert len(addresses) == 2  # Only 2 host addresses in /30
        assert "192.168.1.1" in addresses
        assert "192.168.1.2" in addresses

    def test_ipv4_class_detection(self):
        """Test IPv4 class detection."""
        # Class A
        assert self.calculator._get_ipv4_class(ipaddress.IPv4Address("10.0.0.1")) == "A"

        # Class B
        assert self.calculator._get_ipv4_class(ipaddress.IPv4Address("172.16.0.1")) == "B"

        # Class C
        assert self.calculator._get_ipv4_class(ipaddress.IPv4Address("192.168.1.1")) == "C"

        # Multicast
        assert self.calculator._get_ipv4_class(ipaddress.IPv4Address("224.0.0.1")) == "D (Multicast)"

    def test_ip_to_binary_ipv4(self):
        """Test IPv4 to binary conversion."""
        ip = ipaddress.IPv4Address("192.168.1.1")
        binary = self.calculator._ip_to_binary(ip)

        assert binary == "11000000.10101000.00000001.00000001"


class TestIPConverter:
    """Test cases for IPConverter class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.converter = IPConverter()

    def test_ipv4_to_decimal(self):
        """Test IPv4 to decimal conversion."""
        result = self.converter.ipv4_to_decimal("192.168.1.1")
        assert result == "3232235777"

    def test_decimal_to_ipv4(self):
        """Test decimal to IPv4 conversion."""
        result = self.converter.decimal_to_ipv4("3232235777")
        assert result == "192.168.1.1"

    def test_ipv4_to_hex(self):
        """Test IPv4 to hexadecimal conversion."""
        result = self.converter.ipv4_to_hex("192.168.1.1")
        assert result == "C0A80101"

    def test_hex_to_ipv4(self):
        """Test hexadecimal to IPv4 conversion."""
        result = self.converter.hex_to_ipv4("C0A80101")
        assert result == "192.168.1.1"

    def test_ipv4_to_binary(self):
        """Test IPv4 to binary conversion."""
        result = self.converter.ipv4_to_binary("192.168.1.1")
        assert result == "11000000101010000000000100000001"

    def test_binary_to_ipv4(self):
        """Test binary to IPv4 conversion."""
        result = self.converter.binary_to_ipv4("11000000101010000000000100000001")
        assert result == "192.168.1.1"

    def test_ipv6_compress(self):
        """Test IPv6 compression."""
        result = self.converter.ipv6_compress("2001:0db8:0000:0000:0000:0000:0000:0001")
        assert result == "2001:db8::1"

    def test_ipv6_expand(self):
        """Test IPv6 expansion."""
        result = self.converter.ipv6_expand("2001:db8::1")
        assert result == "2001:0db8:0000:0000:0000:0000:0000:0001"

    def test_invalid_ipv4_conversion(self):
        """Test invalid IPv4 conversion."""
        result = self.converter.ipv4_to_decimal("invalid.ip")
        assert result == "Invalid IPv4 address"

    def test_invalid_decimal_conversion(self):
        """Test invalid decimal conversion."""
        result = self.converter.decimal_to_ipv4("invalid")
        assert result == "Invalid decimal value"

    def test_invalid_hex_conversion(self):
        """Test invalid hex conversion."""
        result = self.converter.hex_to_ipv4("invalid")
        assert result == "Invalid hexadecimal value"

    def test_invalid_binary_conversion(self):
        """Test invalid binary conversion."""
        result = self.converter.binary_to_ipv4("invalid")
        assert result == "Invalid binary value (must be 32 bits)"

    def test_invalid_ipv6_conversion(self):
        """Test invalid IPv6 conversion."""
        result = self.converter.ipv6_compress("invalid::ipv6")
        assert result == "Invalid IPv6 address"
