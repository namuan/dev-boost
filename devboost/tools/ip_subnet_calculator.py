import ipaddress
import logging

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QApplication,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QTabWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from devboost.styles import get_tool_style

logger = logging.getLogger(__name__)


class IPSubnetCalculator:
    """Backend class for IP subnet calculations and CIDR operations."""

    def __init__(self):
        """Initialize the IPSubnetCalculator."""
        logger.info("Initializing IPSubnetCalculator")

    def parse_ip_input(self, ip_input: str) -> ipaddress.IPv4Network | ipaddress.IPv6Network | None:
        """Parse IP input string and return network object."""
        try:
            ip_input = ip_input.strip()
            if not ip_input:
                return None

            # Try to parse as network first (with CIDR notation)
            try:
                if ":" in ip_input:
                    # IPv6
                    if "/" not in ip_input:
                        ip_input += "/128"  # Default to host
                    network = ipaddress.IPv6Network(ip_input, strict=False)
                else:
                    # IPv4
                    if "/" not in ip_input:
                        ip_input += "/32"  # Default to host
                    network = ipaddress.IPv4Network(ip_input, strict=False)

                logger.debug("Parsed %s as network %s", ip_input, network)
                return network

            except ipaddress.AddressValueError:
                # Try to parse as address only
                if ":" in ip_input:
                    addr = ipaddress.IPv6Address(ip_input)
                    network = ipaddress.IPv6Network(f"{addr}/128", strict=False)
                else:
                    addr = ipaddress.IPv4Address(ip_input)
                    network = ipaddress.IPv4Network(f"{addr}/32", strict=False)

                logger.debug("Parsed %s as address, converted to network %s", ip_input, network)
                return network

        except Exception:
            logger.exception("Error parsing IP input %s", ip_input)
            return None

    def get_network_info(self, network: ipaddress.IPv4Network | ipaddress.IPv6Network) -> dict[str, str]:
        """Get comprehensive network information."""
        try:
            info = {}

            # Basic network info
            info["Network Address"] = str(network.network_address)
            info["Broadcast Address"] = (
                str(network.broadcast_address) if hasattr(network, "broadcast_address") else "N/A"
            )
            info["Netmask"] = str(network.netmask)
            info["Hostmask"] = str(network.hostmask)
            info["CIDR Notation"] = str(network)
            info["Prefix Length"] = str(network.prefixlen)
            info["Total Addresses"] = str(network.num_addresses)
            info["Usable Hosts"] = (
                str(max(0, network.num_addresses - 2))
                if isinstance(network, ipaddress.IPv4Network)
                else str(network.num_addresses)
            )

            # IP version specific info
            if isinstance(network, ipaddress.IPv4Network):
                info["IP Version"] = "IPv4"
                info["Network Class"] = self._get_ipv4_class(network.network_address)
                info["Is Private"] = str(network.is_private)
                info["Is Multicast"] = str(network.is_multicast)
                info["Is Loopback"] = str(network.is_loopback)
                info["Is Link Local"] = str(network.is_link_local)

                # Binary representations
                info["Network (Binary)"] = self._ip_to_binary(network.network_address)
                info["Netmask (Binary)"] = self._ip_to_binary(network.netmask)
                info["Broadcast (Binary)"] = self._ip_to_binary(network.broadcast_address)

                # Decimal representations
                info["Network (Decimal)"] = str(int(network.network_address))
                info["Broadcast (Decimal)"] = str(int(network.broadcast_address))

            else:  # IPv6
                info["IP Version"] = "IPv6"
                info["Is Private"] = str(network.is_private)
                info["Is Multicast"] = str(network.is_multicast)
                info["Is Loopback"] = str(network.is_loopback)
                info["Is Link Local"] = str(network.is_link_local)
                info["Is Global"] = str(network.is_global)

                # IPv6 specific
                info["Compressed"] = str(network.compressed)
                info["Exploded"] = str(network.exploded)

            logger.debug("Generated network info for %s", network)
            return info

        except Exception:
            logger.exception("Error getting network info")
            return {}

    def _get_ipv4_class(self, ip: ipaddress.IPv4Address) -> str:
        """Determine IPv4 address class."""
        first_octet = int(str(ip).split(".")[0])

        if 1 <= first_octet <= 126:
            return "A"
        if 128 <= first_octet <= 191:
            return "B"
        if 192 <= first_octet <= 223:
            return "C"
        if 224 <= first_octet <= 239:
            return "D (Multicast)"
        if 240 <= first_octet <= 255:
            return "E (Reserved)"
        return "Unknown"

    def _ip_to_binary(self, ip: ipaddress.IPv4Address | ipaddress.IPv6Address) -> str:
        """Convert IP address to binary representation."""
        if isinstance(ip, ipaddress.IPv4Address):
            octets = str(ip).split(".")
            binary_octets = [format(int(octet), "08b") for octet in octets]
            return ".".join(binary_octets)
        # IPv6 - simplified binary representation
        return format(int(ip), "0128b")

    def subnet_split(
        self, network: ipaddress.IPv4Network | ipaddress.IPv6Network, new_prefix: int
    ) -> list[ipaddress.IPv4Network | ipaddress.IPv6Network]:
        """Split network into smaller subnets."""
        try:
            if new_prefix <= network.prefixlen:
                logger.warning("New prefix %s must be larger than current prefix %s", new_prefix, network.prefixlen)
                return []

            subnets = list(network.subnets(new_prefix=new_prefix))
            logger.debug("Split %s into %s subnets with prefix /%s", network, len(subnets), new_prefix)
            return subnets

        except Exception:
            logger.exception("Error splitting subnet")
            return []

    def classify_ip_address(self, ip_input: str) -> dict[str, str]:
        """Classify an IP address with comprehensive information."""
        try:
            # Parse the IP input
            if not ip_input.strip():
                return {"Error": "No IP address provided"}

            # Try to parse as address first
            try:
                if ":" in ip_input:
                    addr = ipaddress.IPv6Address(ip_input.strip())
                    return self._classify_ipv6_address(addr)
                addr = ipaddress.IPv4Address(ip_input.strip())
                return self._classify_ipv4_address(addr)
            except ipaddress.AddressValueError:
                # Try to parse as network and get network address
                network = self.parse_ip_input(ip_input)
                if network:
                    if isinstance(network, ipaddress.IPv6Network):
                        return self._classify_ipv6_address(network.network_address)
                    return self._classify_ipv4_address(network.network_address)
                return {"Error": f"Invalid IP address format: {ip_input}"}

        except Exception as e:
            logger.exception("Error classifying IP address")
            return {"Error": f"Classification error: {e!s}"}

    def _classify_ipv4_address(self, addr: ipaddress.IPv4Address) -> dict[str, str]:
        """Classify IPv4 address with detailed information."""
        classification = {}

        # Basic info
        classification["IP Address"] = str(addr)
        classification["IP Version"] = "IPv4"
        classification["Address Class"] = self._get_ipv4_class(addr)

        # RFC classifications
        classification["Is Private"] = "Yes" if addr.is_private else "No"
        classification["Is Public"] = "No" if addr.is_private else "Yes"
        classification["Is Loopback"] = "Yes" if addr.is_loopback else "No"
        classification["Is Multicast"] = "Yes" if addr.is_multicast else "No"
        classification["Is Link Local"] = "Yes" if addr.is_link_local else "No"
        classification["Is Reserved"] = "Yes" if addr.is_reserved else "No"

        # Detailed private network classification
        if addr.is_private:
            classification["Private Network Type"] = self._get_private_network_type_ipv4(addr)

        # Special address ranges
        classification["Special Range"] = self._get_special_range_ipv4(addr)

        # Binary and decimal representations
        classification["Binary"] = self._ip_to_binary(addr)
        classification["Decimal"] = str(int(addr))
        classification["Hexadecimal"] = hex(int(addr))

        return classification

    def _classify_ipv6_address(self, addr: ipaddress.IPv6Address) -> dict[str, str]:
        """Classify IPv6 address with detailed information."""
        classification = {}

        # Basic info
        classification["IP Address"] = str(addr)
        classification["IP Version"] = "IPv6"
        classification["Compressed"] = str(addr.compressed)
        classification["Exploded"] = str(addr.exploded)

        # RFC classifications
        classification["Is Private"] = "Yes" if addr.is_private else "No"
        classification["Is Public"] = "No" if addr.is_private else "Yes"
        classification["Is Loopback"] = "Yes" if addr.is_loopback else "No"
        classification["Is Multicast"] = "Yes" if addr.is_multicast else "No"
        classification["Is Link Local"] = "Yes" if addr.is_link_local else "No"
        classification["Is Global"] = "Yes" if addr.is_global else "No"
        classification["Is Reserved"] = "Yes" if addr.is_reserved else "No"

        # IPv6 specific classifications
        classification["Is Site Local"] = "Yes" if addr.is_site_local else "No"
        classification["Is Unspecified"] = "Yes" if addr.is_unspecified else "No"

        # Detailed private network classification
        if addr.is_private:
            classification["Private Network Type"] = self._get_private_network_type_ipv6(addr)

        # Special address ranges
        classification["Special Range"] = self._get_special_range_ipv6(addr)

        return classification

    def _get_private_network_type_ipv4(self, addr: ipaddress.IPv4Address) -> str:
        """Get specific private network type for IPv4."""
        # RFC 1918 private networks
        if ipaddress.IPv4Address("10.0.0.0") <= addr <= ipaddress.IPv4Address("10.255.255.255"):
            return "RFC 1918 - Class A Private (10.0.0.0/8)"
        if ipaddress.IPv4Address("172.16.0.0") <= addr <= ipaddress.IPv4Address("172.31.255.255"):
            return "RFC 1918 - Class B Private (172.16.0.0/12)"
        if ipaddress.IPv4Address("192.168.0.0") <= addr <= ipaddress.IPv4Address("192.168.255.255"):
            return "RFC 1918 - Class C Private (192.168.0.0/16)"

        # RFC 3927 Link-Local
        if ipaddress.IPv4Address("169.254.0.0") <= addr <= ipaddress.IPv4Address("169.254.255.255"):
            return "RFC 3927 - Link-Local (169.254.0.0/16)"

        # RFC 6598 Carrier-Grade NAT
        if ipaddress.IPv4Address("100.64.0.0") <= addr <= ipaddress.IPv4Address("100.127.255.255"):
            return "RFC 6598 - Carrier-Grade NAT (100.64.0.0/10)"

        return "Unknown Private Range"

    def _get_private_network_type_ipv6(self, addr: ipaddress.IPv6Address) -> str:
        """Get specific private network type for IPv6."""
        addr_str = str(addr)

        if addr_str.startswith("fc") or addr_str.startswith("fd"):
            return "RFC 4193 - Unique Local Address (fc00::/7)"
        if addr_str.startswith("fe80"):
            return "RFC 4291 - Link Local (fe80::/10)"

        return "Other private range"

    def _get_special_range_ipv4(self, addr: ipaddress.IPv4Address) -> str:
        """Get special address range information for IPv4."""
        # Special ranges
        if ipaddress.IPv4Address("127.0.0.0") <= addr <= ipaddress.IPv4Address("127.255.255.255"):
            return "RFC 1122 - Loopback (127.0.0.0/8)"
        if ipaddress.IPv4Address("169.254.0.0") <= addr <= ipaddress.IPv4Address("169.254.255.255"):
            return "RFC 3927 - Link Local (169.254.0.0/16)"
        if ipaddress.IPv4Address("224.0.0.0") <= addr <= ipaddress.IPv4Address("239.255.255.255"):
            return "RFC 3171 - Multicast Class D (224.0.0.0/4)"
        if ipaddress.IPv4Address("240.0.0.0") <= addr <= ipaddress.IPv4Address("255.255.255.255"):
            return "RFC 1112 - Reserved Class E (240.0.0.0/4)"
        if addr == ipaddress.IPv4Address("255.255.255.255"):
            return "RFC 919 - Limited Broadcast"

        return ""

    def _get_special_range_ipv6(self, addr: ipaddress.IPv6Address) -> str:
        """Get special address range information for IPv6."""
        addr_str = str(addr.compressed)

        if addr_str == "::":
            return "RFC 4291 - Unspecified Address"
        if addr_str == "::1":
            return "RFC 4291 - Loopback Address"
        if addr_str.startswith("::ffff:"):
            return "RFC 4291 - IPv4-mapped IPv6 Address"
        if addr_str.startswith("2001:db8"):
            return "RFC 3849 - Documentation (2001:db8::/32)"
        if addr_str.startswith("ff"):
            return "RFC 4291 - Multicast (ff00::/8)"
        if addr_str.startswith("fe80"):
            return "RFC 4291 - Link Local (fe80::/10)"
        if addr_str.startswith("fc") or addr_str.startswith("fd"):
            return "RFC 4193 - Unique Local (fc00::/7)"
        if addr_str.startswith("2001:"):
            return "RFC 4291 - Global Unicast"

        return "Standard unicast range"

    def supernet_summary(self, networks: list[str]) -> ipaddress.IPv4Network | ipaddress.IPv6Network | None:
        try:
            if not networks:
                return None

            # Parse all networks
            parsed_networks = []
            for net_str in networks:
                network = self.parse_ip_input(net_str)
                if network:
                    parsed_networks.append(network)

            if not parsed_networks:
                return None

            # Check if all networks are the same IP version
            ip_versions = {type(net) for net in parsed_networks}
            if len(ip_versions) > 1:
                logger.error("Cannot summarize networks of different IP versions")
                return None

            # Find supernet
            if isinstance(parsed_networks[0], ipaddress.IPv4Network):
                supernet = ipaddress.collapse_addresses(parsed_networks)
                supernet_list = list(supernet)
                if len(supernet_list) == 1:
                    result = supernet_list[0]
                else:
                    # Find common supernet manually
                    result = self._find_common_supernet_ipv4(parsed_networks)
            else:
                supernet = ipaddress.collapse_addresses(parsed_networks)
                supernet_list = list(supernet)
                if len(supernet_list) == 1:
                    result = supernet_list[0]
                else:
                    result = self._find_common_supernet_ipv6(parsed_networks)

            logger.debug("Summarized networks into supernet: %s", result)
            return result

        except Exception:
            logger.exception("Error creating supernet")
            return None

    def _find_common_supernet_ipv4(self, networks: list[ipaddress.IPv4Network]) -> ipaddress.IPv4Network | None:
        """Find common supernet for IPv4 networks."""
        try:
            if not networks:
                return None

            # Find the minimum and maximum addresses
            min_addr = min(net.network_address for net in networks)
            max_addr = max(net.broadcast_address for net in networks)

            # Find common prefix length
            min_int = int(min_addr)
            max_int = int(max_addr)

            # XOR to find differing bits
            xor_result = min_int ^ max_int

            # Count leading zeros to find common prefix
            prefix_len = 32 if xor_result == 0 else 32 - xor_result.bit_length()

            # Create supernet
            return ipaddress.IPv4Network(f"{min_addr}/{prefix_len}", strict=False)

        except Exception:
            logger.exception("Error finding IPv4 supernet")
            return None

    def _find_common_supernet_ipv6(self, networks: list[ipaddress.IPv6Network]) -> ipaddress.IPv6Network | None:
        """Find common supernet for IPv6 networks."""
        try:
            if not networks:
                return None

            # Find the minimum and maximum addresses
            min_addr = min(net.network_address for net in networks)
            max_addr = max(net.broadcast_address for net in networks)

            # Find common prefix length
            min_int = int(min_addr)
            max_int = int(max_addr)

            # XOR to find differing bits
            xor_result = min_int ^ max_int

            # Count leading zeros to find common prefix
            prefix_len = 128 if xor_result == 0 else 128 - xor_result.bit_length()

            # Create supernet
            return ipaddress.IPv6Network(f"{min_addr}/{prefix_len}", strict=False)

        except Exception:
            logger.exception("Error finding IPv6 supernet")
            return None

    def get_address_range(self, network: ipaddress.IPv4Network | ipaddress.IPv6Network, limit: int = 10) -> list[str]:
        """Get list of addresses in the network (limited for display)."""
        try:
            addresses = []

            for count, addr in enumerate(network.hosts() if network.num_addresses > 2 else network):
                if count >= limit:
                    addresses.append(f"... and {network.num_addresses - limit} more")
                    break
                addresses.append(str(addr))

            return addresses

        except Exception:
            logger.exception("Error getting address range")
            return []


class IPConverter:
    """Backend class for IP format conversions."""

    def __init__(self):
        """Initialize the IPConverter."""
        logger.info("Initializing IPConverter")

    def convert_formats(self, ip_input: str) -> dict[str, str]:
        """Convert IP to various formats."""
        try:
            formats = {}

            # Try to parse as IPv4 address
            try:
                ipv4_addr = ipaddress.IPv4Address(ip_input.strip())
                formats["IPv4 Decimal"] = str(ipv4_addr)
                formats["IPv4 Integer"] = str(int(ipv4_addr))
                formats["IPv4 Hexadecimal"] = f"0x{int(ipv4_addr):08x}"
                formats["IPv4 Binary"] = self._ipv4_to_binary(ipv4_addr)
                formats["IPv4 Octal"] = f"0o{int(ipv4_addr):011o}"

                # IPv6 mapped
                ipv6_mapped = ipaddress.IPv6Address(f"::ffff:{ipv4_addr}")
                formats["IPv6 Mapped"] = str(ipv6_mapped)
                formats["IPv6 Mapped Compressed"] = str(ipv6_mapped.compressed)
                formats["IPv6 Mapped Exploded"] = str(ipv6_mapped.exploded)

                return formats

            except ipaddress.AddressValueError:
                pass

            # Try to parse as IPv6 address
            try:
                ipv6_addr = ipaddress.IPv6Address(ip_input.strip())
                formats["IPv6 Compressed"] = str(ipv6_addr.compressed)
                formats["IPv6 Exploded"] = str(ipv6_addr.exploded)
                formats["IPv6 Integer"] = str(int(ipv6_addr))
                formats["IPv6 Hexadecimal"] = f"0x{int(ipv6_addr):032x}"

                # Check if it's an IPv4-mapped IPv6 address
                if ipv6_addr.ipv4_mapped:
                    formats["IPv4 Mapped"] = str(ipv6_addr.ipv4_mapped)

                return formats

            except ipaddress.AddressValueError:
                pass

            # Try to parse as integer
            try:
                ip_int = int(ip_input.strip())
                if 0 <= ip_int <= 0xFFFFFFFF:
                    # IPv4 range
                    ipv4_addr = ipaddress.IPv4Address(ip_int)
                    formats["IPv4 from Integer"] = str(ipv4_addr)
                    formats["IPv4 Binary"] = self._ipv4_to_binary(ipv4_addr)
                    formats["IPv4 Hexadecimal"] = f"0x{ip_int:08x}"
                elif 0 <= ip_int <= 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF:
                    # IPv6 range
                    ipv6_addr = ipaddress.IPv6Address(ip_int)
                    formats["IPv6 from Integer"] = str(ipv6_addr.compressed)
                    formats["IPv6 Exploded"] = str(ipv6_addr.exploded)

                return formats

            except (ValueError, ipaddress.AddressValueError):
                pass

            # Try to parse as hexadecimal
            try:
                hex_input = ip_input.strip()
                if hex_input.startswith("0x"):
                    hex_input = hex_input[2:]

                ip_int = int(hex_input, 16)
                if 0 <= ip_int <= 0xFFFFFFFF:
                    # IPv4 range
                    ipv4_addr = ipaddress.IPv4Address(ip_int)
                    formats["IPv4 from Hex"] = str(ipv4_addr)
                    formats["IPv4 Integer"] = str(ip_int)
                    formats["IPv4 Binary"] = self._ipv4_to_binary(ipv4_addr)
                elif 0 <= ip_int <= 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF:
                    # IPv6 range
                    ipv6_addr = ipaddress.IPv6Address(ip_int)
                    formats["IPv6 from Hex"] = str(ipv6_addr.compressed)
                    formats["IPv6 Exploded"] = str(ipv6_addr.exploded)

                return formats

            except (ValueError, ipaddress.AddressValueError):
                pass

            logger.warning("Could not parse IP input: %s", ip_input)
            return {"Error": "Invalid IP address format"}

        except Exception as e:
            logger.exception("Error converting IP formats")
            return {"Error": str(e)}

    def _ipv4_to_binary(self, ip: ipaddress.IPv4Address) -> str:
        """Convert IPv4 address to binary representation."""
        octets = str(ip).split(".")
        binary_octets = [format(int(octet), "08b") for octet in octets]
        return ".".join(binary_octets)

    def ipv4_to_decimal(self, ip_str: str) -> str:
        """Convert IPv4 address to decimal."""
        try:
            ip = ipaddress.IPv4Address(ip_str.strip())
            return str(int(ip))
        except ipaddress.AddressValueError:
            return "Invalid IPv4 address"

    def decimal_to_ipv4(self, decimal_str: str) -> str:
        """Convert decimal to IPv4 address."""
        try:
            decimal_val = int(decimal_str.strip())
            if 0 <= decimal_val <= 0xFFFFFFFF:
                ip = ipaddress.IPv4Address(decimal_val)
                return str(ip)
            return "Decimal value out of IPv4 range"
        except ValueError:
            return "Invalid decimal value"

    def ipv4_to_hex(self, ip_str: str) -> str:
        """Convert IPv4 address to hexadecimal."""
        try:
            ip = ipaddress.IPv4Address(ip_str.strip())
            return f"{int(ip):08X}"
        except ipaddress.AddressValueError:
            return "Invalid IPv4 address"

    def hex_to_ipv4(self, hex_str: str) -> str:
        """Convert hexadecimal to IPv4 address."""
        try:
            hex_input = hex_str.strip()
            if hex_input.startswith("0x") or hex_input.startswith("0X"):
                hex_input = hex_input[2:]

            decimal_val = int(hex_input, 16)
            if 0 <= decimal_val <= 0xFFFFFFFF:
                ip = ipaddress.IPv4Address(decimal_val)
                return str(ip)
            return "Hexadecimal value out of IPv4 range"
        except ValueError:
            return "Invalid hexadecimal value"

    def ipv4_to_binary(self, ip_str: str) -> str:
        """Convert IPv4 address to binary."""
        try:
            ip = ipaddress.IPv4Address(ip_str.strip())
            return format(int(ip), "032b")
        except ipaddress.AddressValueError:
            return "Invalid IPv4 address"

    def binary_to_ipv4(self, binary_str: str) -> str:
        """Convert binary to IPv4 address."""
        try:
            binary_input = binary_str.strip().replace(".", "").replace(" ", "")
            if len(binary_input) != 32 or not all(c in "01" for c in binary_input):
                return "Invalid binary value (must be 32 bits)"

            decimal_val = int(binary_input, 2)
            ip = ipaddress.IPv4Address(decimal_val)
            return str(ip)
        except (ValueError, ipaddress.AddressValueError):
            return "Invalid binary value"

    def ipv6_compress(self, ipv6_str: str) -> str:
        """Compress IPv6 address."""
        try:
            ip = ipaddress.IPv6Address(ipv6_str.strip())
            return str(ip.compressed)
        except ipaddress.AddressValueError:
            return "Invalid IPv6 address"

    def ipv6_expand(self, ipv6_str: str) -> str:
        """Expand IPv6 address."""
        try:
            ip = ipaddress.IPv6Address(ipv6_str.strip())
            return str(ip.exploded)
        except ipaddress.AddressValueError:
            return "Invalid IPv6 address"


def create_ip_subnet_calculator_widget(style_func, scratch_pad=None):
    """Create the IP subnet calculator widget."""
    logger.info("Creating IP subnet calculator widget")

    # Create main widget
    main_widget = QWidget()
    main_layout = QVBoxLayout(main_widget)
    main_layout.setContentsMargins(10, 10, 10, 10)
    main_layout.setSpacing(10)

    # Set widget properties
    main_widget.setObjectName("mainWidget")
    main_widget.setStyleSheet(get_tool_style())

    # Initialize calculators
    subnet_calculator = IPSubnetCalculator()
    ip_converter = IPConverter()

    # Tab widget for different modes
    tabs = QTabWidget()
    main_layout.addWidget(tabs)

    # Create tabs
    subnet_tab = _create_subnet_tab(subnet_calculator, scratch_pad)
    converter_tab = _create_converter_tab(ip_converter, scratch_pad)
    splitter_tab = _create_splitter_tab(subnet_calculator, scratch_pad)
    summarizer_tab = _create_summarizer_tab(subnet_calculator, scratch_pad)
    classifier_tab = _create_classifier_tab(subnet_calculator, scratch_pad)

    tabs.addTab(subnet_tab, "Subnet Calculator")
    tabs.addTab(converter_tab, "IP Converter")
    tabs.addTab(splitter_tab, "Subnet Splitter")
    tabs.addTab(summarizer_tab, "Supernet Summarizer")
    tabs.addTab(classifier_tab, "IP Classifier")

    return main_widget


def _create_subnet_tab(subnet_calculator, scratch_pad):
    """Create the subnet calculator tab."""
    subnet_tab = QWidget()
    layout = QVBoxLayout(subnet_tab)
    layout.setContentsMargins(10, 10, 10, 10)
    layout.setSpacing(10)

    # Input section
    input_layout = QHBoxLayout()
    input_layout.addWidget(QLabel("IP/Network:"))

    ip_input = QLineEdit()
    ip_input.setPlaceholderText("Enter IP address or network (e.g., 192.168.1.0/24, 2001:db8::/32)")
    input_layout.addWidget(ip_input)

    calculate_btn = QPushButton("Calculate")
    input_layout.addWidget(calculate_btn)

    layout.addLayout(input_layout)

    # Results area
    results_scroll = QScrollArea()
    results_scroll.setWidgetResizable(True)
    results_widget = QWidget()
    results_layout = QVBoxLayout(results_widget)
    results_scroll.setWidget(results_widget)
    layout.addWidget(results_scroll)

    # Copy buttons section
    copy_layout = QHBoxLayout()
    copy_network_btn = QPushButton("Copy Network")
    copy_broadcast_btn = QPushButton("Copy Broadcast")
    copy_all_btn = QPushButton("Copy All Info")

    copy_layout.addWidget(copy_network_btn)
    copy_layout.addWidget(copy_broadcast_btn)
    copy_layout.addWidget(copy_all_btn)
    copy_layout.addStretch()

    layout.addLayout(copy_layout)

    # Event handlers
    def calculate_subnet():
        """Calculate subnet information."""
        try:
            ip_text = ip_input.text().strip()
            if not ip_text:
                return

            network = subnet_calculator.parse_ip_input(ip_text)
            if not network:
                _show_error_in_results(results_layout, "Invalid IP address or network format")
                return

            info = subnet_calculator.get_network_info(network)
            _display_network_info(results_layout, info)

            # Store current network for copy operations
            calculate_subnet.current_network = network
            calculate_subnet.current_info = info

        except Exception as e:
            logger.exception("Error calculating subnet")
            _show_error_in_results(results_layout, f"Error: {e!s}")

    def copy_network():
        """Copy network address to clipboard."""
        if hasattr(calculate_subnet, "current_info"):
            network_addr = calculate_subnet.current_info.get("Network Address", "")
            if network_addr:
                QApplication.clipboard().setText(network_addr)
                logger.info("Copied network address to clipboard: %s", network_addr)

    def copy_broadcast():
        """Copy broadcast address to clipboard."""
        if hasattr(calculate_subnet, "current_info"):
            broadcast_addr = calculate_subnet.current_info.get("Broadcast Address", "")
            if broadcast_addr and broadcast_addr != "N/A":
                QApplication.clipboard().setText(broadcast_addr)
                logger.info("Copied broadcast address to clipboard: %s", broadcast_addr)

    def copy_all():
        """Copy all network information to clipboard."""
        if hasattr(calculate_subnet, "current_info"):
            info_text = "\n".join([f"{k}: {v}" for k, v in calculate_subnet.current_info.items()])
            QApplication.clipboard().setText(info_text)
            logger.info("Copied all network info to clipboard")

    # Connect events
    calculate_btn.clicked.connect(calculate_subnet)
    ip_input.returnPressed.connect(calculate_subnet)
    copy_network_btn.clicked.connect(copy_network)
    copy_broadcast_btn.clicked.connect(copy_broadcast)
    copy_all_btn.clicked.connect(copy_all)

    return subnet_tab


def _create_converter_tab(ip_converter, scratch_pad):
    """Create the IP converter tab."""
    converter_tab = QWidget()
    layout = QVBoxLayout(converter_tab)
    layout.setContentsMargins(10, 10, 10, 10)
    layout.setSpacing(10)

    # Input section
    input_layout = QHBoxLayout()
    input_layout.addWidget(QLabel("IP Address:"))

    ip_input = QLineEdit()
    ip_input.setPlaceholderText("Enter IP address, integer, or hex value")
    input_layout.addWidget(ip_input)

    convert_btn = QPushButton("Convert")
    input_layout.addWidget(convert_btn)

    layout.addLayout(input_layout)

    # Results area
    results_scroll = QScrollArea()
    results_scroll.setWidgetResizable(True)
    results_widget = QWidget()
    results_layout = QVBoxLayout(results_widget)
    results_scroll.setWidget(results_widget)
    layout.addWidget(results_scroll)

    # Copy all button
    copy_layout = QHBoxLayout()
    copy_all_btn = QPushButton("Copy All Formats")
    copy_layout.addWidget(copy_all_btn)
    copy_layout.addStretch()
    layout.addLayout(copy_layout)

    # Event handlers
    def convert_ip():
        """Convert IP to various formats."""
        try:
            ip_text = ip_input.text().strip()
            if not ip_text:
                return

            formats = ip_converter.convert_formats(ip_text)
            _display_conversion_results(results_layout, formats)

            # Store current formats for copy operation
            convert_ip.current_formats = formats

        except Exception as e:
            logger.exception("Error converting IP")
            _show_error_in_results(results_layout, f"Error: {e!s}")

    def copy_all_formats():
        """Copy all format conversions to clipboard."""
        if hasattr(convert_ip, "current_formats"):
            formats_text = "\n".join([f"{k}: {v}" for k, v in convert_ip.current_formats.items()])
            QApplication.clipboard().setText(formats_text)
            logger.info("Copied all IP formats to clipboard")

    # Connect events
    convert_btn.clicked.connect(convert_ip)
    ip_input.returnPressed.connect(convert_ip)
    copy_all_btn.clicked.connect(copy_all_formats)

    return converter_tab


def _create_splitter_tab(subnet_calculator, scratch_pad):
    """Create the subnet splitter tab."""
    splitter_tab = QWidget()
    layout = QVBoxLayout(splitter_tab)
    layout.setContentsMargins(10, 10, 10, 10)
    layout.setSpacing(10)

    # Input section
    input_layout = QVBoxLayout()

    # Network input
    network_layout = QHBoxLayout()
    network_layout.addWidget(QLabel("Network:"))
    network_input = QLineEdit()
    network_input.setPlaceholderText("Enter network (e.g., 192.168.1.0/24)")
    network_layout.addWidget(network_input)
    input_layout.addLayout(network_layout)

    # Split options
    split_layout = QHBoxLayout()
    split_layout.addWidget(QLabel("New Prefix Length:"))
    prefix_input = QLineEdit()
    prefix_input.setPlaceholderText("e.g., 26 for /26 subnets")
    split_layout.addWidget(prefix_input)

    split_btn = QPushButton("Split Network")
    split_layout.addWidget(split_btn)
    input_layout.addLayout(split_layout)

    layout.addLayout(input_layout)

    # Results area
    results_scroll = QScrollArea()
    results_scroll.setWidgetResizable(True)
    results_widget = QWidget()
    results_layout = QVBoxLayout(results_widget)
    results_scroll.setWidget(results_widget)
    layout.addWidget(results_scroll)

    # Copy button
    copy_layout = QHBoxLayout()
    copy_subnets_btn = QPushButton("Copy All Subnets")
    copy_layout.addWidget(copy_subnets_btn)
    copy_layout.addStretch()
    layout.addLayout(copy_layout)

    # Event handlers
    def split_network():
        """Split network into subnets."""
        try:
            network_text = network_input.text().strip()
            prefix_text = prefix_input.text().strip()

            if not network_text or not prefix_text:
                return

            network = subnet_calculator.parse_ip_input(network_text)
            if not network:
                _show_error_in_results(results_layout, "Invalid network format")
                return

            try:
                new_prefix = int(prefix_text)
            except ValueError:
                _show_error_in_results(results_layout, "Invalid prefix length")
                return

            subnets = subnet_calculator.subnet_split(network, new_prefix)
            if not subnets:
                _show_error_in_results(results_layout, "Cannot split network with given prefix")
                return

            _display_subnet_list(results_layout, subnets)

            # Store current subnets for copy operation
            split_network.current_subnets = subnets

        except Exception as e:
            logger.exception("Error splitting network")
            _show_error_in_results(results_layout, f"Error: {e!s}")

    def copy_all_subnets():
        """Copy all subnets to clipboard."""
        if hasattr(split_network, "current_subnets"):
            subnets_text = "\n".join([str(subnet) for subnet in split_network.current_subnets])
            QApplication.clipboard().setText(subnets_text)
            logger.info("Copied all subnets to clipboard")

    # Connect events
    split_btn.clicked.connect(split_network)
    network_input.returnPressed.connect(split_network)
    prefix_input.returnPressed.connect(split_network)
    copy_subnets_btn.clicked.connect(copy_all_subnets)

    return splitter_tab


def _create_summarizer_tab(subnet_calculator, scratch_pad):
    """Create the supernet summarizer tab."""
    summarizer_tab = QWidget()
    layout = QVBoxLayout(summarizer_tab)
    layout.setContentsMargins(10, 10, 10, 10)
    layout.setSpacing(10)

    # Input section
    input_layout = QVBoxLayout()

    # Networks input
    networks_layout = QVBoxLayout()
    networks_layout.addWidget(QLabel("Networks to Summarize:"))
    networks_input = QTextEdit()
    networks_input.setPlaceholderText("Enter networks, one per line:\n192.168.1.0/24\n192.168.2.0/24\n192.168.3.0/24")
    networks_input.setMaximumHeight(120)
    networks_layout.addWidget(networks_input)
    input_layout.addLayout(networks_layout)

    # Summarize button
    summarize_layout = QHBoxLayout()
    summarize_btn = QPushButton("Summarize Networks")
    summarize_layout.addWidget(summarize_btn)
    summarize_layout.addStretch()
    input_layout.addLayout(summarize_layout)

    layout.addLayout(input_layout)

    # Results area
    results_scroll = QScrollArea()
    results_scroll.setWidgetResizable(True)
    results_widget = QWidget()
    results_layout = QVBoxLayout(results_widget)
    results_scroll.setWidget(results_widget)
    layout.addWidget(results_scroll)

    # Copy button
    copy_layout = QHBoxLayout()
    copy_supernet_btn = QPushButton("Copy Supernet")
    copy_layout.addWidget(copy_supernet_btn)
    copy_layout.addStretch()
    layout.addLayout(copy_layout)

    # Event handlers
    def summarize_networks():
        """Summarize networks into supernet."""
        try:
            networks_text = networks_input.toPlainText().strip()
            if not networks_text:
                return

            # Parse networks from input
            network_lines = [line.strip() for line in networks_text.split("\n") if line.strip()]
            if not network_lines:
                _show_error_in_results(results_layout, "No networks provided")
                return

            supernet = subnet_calculator.supernet_summary(network_lines)
            if not supernet:
                _show_error_in_results(results_layout, "Cannot create supernet from provided networks")
                return

            # Display supernet info
            supernet_info = subnet_calculator.get_network_info(supernet)
            _display_supernet_summary(results_layout, supernet, network_lines, supernet_info)

            # Store current supernet for copy operation
            summarize_networks.current_supernet = supernet

        except Exception as e:
            logger.exception("Error summarizing networks")
            _show_error_in_results(results_layout, f"Error: {e!s}")

    def copy_supernet():
        """Copy supernet to clipboard."""
        if hasattr(summarize_networks, "current_supernet"):
            QApplication.clipboard().setText(str(summarize_networks.current_supernet))
            logger.info("Copied supernet to clipboard")

    # Connect events
    summarize_btn.clicked.connect(summarize_networks)
    copy_supernet_btn.clicked.connect(copy_supernet)

    return summarizer_tab


def _display_supernet_summary(layout, supernet, original_networks, supernet_info):
    """Display supernet summarization results."""
    # Clear previous results
    _clear_layout(layout)

    # Supernet header
    header = QLabel(f"Supernet: {supernet}")
    header.setStyleSheet("font-weight: bold; font-size: 16px; color: #2196F3; margin-bottom: 10px;")
    layout.addWidget(header)

    # Original networks
    original_label = QLabel("Original Networks:")
    original_label.setStyleSheet("font-weight: bold; color: #666; margin-top: 10px;")
    layout.addWidget(original_label)

    for network in original_networks:
        network_label = QLabel(f"  • {network}")
        network_label.setStyleSheet("font-family: monospace; color: #333; margin-left: 10px;")
        layout.addWidget(network_label)

    # Supernet details
    details_label = QLabel("Supernet Details:")
    details_label.setStyleSheet("font-weight: bold; color: #666; margin-top: 15px;")
    layout.addWidget(details_label)

    # Create grid for supernet info
    grid = QGridLayout()
    for row, (key, value) in enumerate(supernet_info.items()):
        if key in ["Network Address", "Broadcast Address", "Subnet Mask", "Prefix Length", "Total Addresses"]:
            label = QLabel(f"{key}:")
            label.setStyleSheet("font-weight: bold; color: #2196F3; margin-left: 10px;")
            value_label = QLabel(str(value))
            value_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
            value_label.setStyleSheet("font-family: monospace;")

            grid.addWidget(label, row, 0)
            grid.addWidget(value_label, row, 1)

    grid_widget = QWidget()
    grid_widget.setLayout(grid)
    layout.addWidget(grid_widget)
    layout.addStretch()


def _display_network_info(layout, info):
    """Display network information in the results area."""
    # Clear previous results
    _clear_layout(layout)

    # Create grid layout for info
    grid = QGridLayout()

    for row, (key, value) in enumerate(info.items()):
        label = QLabel(f"{key}:")
        label.setStyleSheet("font-weight: bold; color: #2196F3;")
        value_label = QLabel(str(value))
        value_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)

        grid.addWidget(label, row, 0)
        grid.addWidget(value_label, row, 1)

    widget = QWidget()
    widget.setLayout(grid)
    layout.addWidget(widget)
    layout.addStretch()


def _display_conversion_results(layout, formats):
    """Display IP conversion results."""
    # Clear previous results
    _clear_layout(layout)

    # Create grid layout for formats
    grid = QGridLayout()

    for row, (format_name, value) in enumerate(formats.items()):
        label = QLabel(f"{format_name}:")
        label.setStyleSheet("font-weight: bold; color: #2196F3;")
        value_label = QLabel(str(value))
        value_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)

        grid.addWidget(label, row, 0)
        grid.addWidget(value_label, row, 1)

    widget = QWidget()
    widget.setLayout(grid)
    layout.addWidget(widget)
    layout.addStretch()


def _display_subnet_list(layout, subnets):
    """Display list of subnets."""
    # Clear previous results
    _clear_layout(layout)

    # Add header
    header = QLabel(f"Generated {len(subnets)} subnets:")
    header.setStyleSheet("font-weight: bold; font-size: 14px; color: #2196F3; margin-bottom: 10px;")
    layout.addWidget(header)

    # Add subnets
    for i, subnet in enumerate(subnets, 1):
        subnet_label = QLabel(f"{i:3d}. {subnet}")
        subnet_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        subnet_label.setStyleSheet("font-family: monospace; padding: 2px;")
        layout.addWidget(subnet_label)

    layout.addStretch()


def _show_error_in_results(layout, error_message):
    """Show error message in results area."""
    # Clear previous results
    _clear_layout(layout)

    error_label = QLabel(error_message)
    error_label.setStyleSheet("color: #d32f2f; font-weight: bold; padding: 10px;")
    layout.addWidget(error_label)
    layout.addStretch()


def _create_classifier_tab(subnet_calculator, scratch_pad):
    """Create the IP address classifier tab."""
    classifier_tab = QWidget()
    layout = QVBoxLayout(classifier_tab)
    layout.setContentsMargins(10, 10, 10, 10)
    layout.setSpacing(10)

    # Input section
    input_layout = QVBoxLayout()

    # IP address input
    ip_layout = QHBoxLayout()
    ip_layout.addWidget(QLabel("IP Address:"))
    ip_input = QLineEdit()
    ip_input.setPlaceholderText("Enter IP address (e.g., 192.168.1.1, 2001:db8::1)")
    ip_layout.addWidget(ip_input)
    input_layout.addLayout(ip_layout)

    # Classify button
    classify_layout = QHBoxLayout()
    classify_btn = QPushButton("Classify IP Address")
    classify_layout.addWidget(classify_btn)
    classify_layout.addStretch()
    input_layout.addLayout(classify_layout)

    layout.addLayout(input_layout)

    # Results area
    results_scroll = QScrollArea()
    results_scroll.setWidgetResizable(True)
    results_widget = QWidget()
    results_layout = QVBoxLayout(results_widget)
    results_scroll.setWidget(results_widget)
    layout.addWidget(results_scroll)

    # Copy button
    copy_layout = QHBoxLayout()
    copy_classification_btn = QPushButton("Copy Classification")
    copy_layout.addWidget(copy_classification_btn)
    copy_layout.addStretch()
    layout.addLayout(copy_layout)

    # Event handlers
    def classify_ip():
        """Classify the IP address."""
        try:
            ip_address = ip_input.text().strip()
            if not ip_address:
                return

            classification = subnet_calculator.classify_ip_address(ip_address)
            if "Error" in classification:
                _show_error_in_results(results_layout, classification["Error"])
                return

            # Display classification results
            _display_ip_classification(results_layout, classification)

            # Store current classification for copy operation
            classify_ip.current_classification = classification

        except Exception as e:
            logger.exception("Error classifying IP address")
            _show_error_in_results(results_layout, f"Error: {e!s}")

    def copy_classification():
        """Copy classification to clipboard."""
        if hasattr(classify_ip, "current_classification"):
            classification_text = "\n".join([
                f"{key}: {value}" for key, value in classify_ip.current_classification.items()
            ])
            QApplication.clipboard().setText(classification_text)
            logger.info("Copied IP classification to clipboard")

    # Connect events
    classify_btn.clicked.connect(classify_ip)
    ip_input.returnPressed.connect(classify_ip)
    copy_classification_btn.clicked.connect(copy_classification)

    return classifier_tab


def _display_ip_classification(layout, classification):
    """Display IP address classification results."""
    # Clear previous results
    _clear_layout(layout)

    # Classification header
    ip_address = classification.get("IP Address", "Unknown")
    header = QLabel(f"IP Classification: {ip_address}")
    header.setStyleSheet("font-weight: bold; font-size: 16px; color: #2196F3; margin-bottom: 10px;")
    layout.addWidget(header)

    # Basic information section
    basic_info = ["IP Address", "IP Version", "Address Class", "Compressed", "Exploded"]
    basic_section = _create_classification_section("Basic Information", classification, basic_info)
    layout.addWidget(basic_section)

    # Classification section
    classification_info = [
        "Is Private",
        "Is Public",
        "Is Loopback",
        "Is Multicast",
        "Is Link Local",
        "Is Reserved",
        "Is Global",
        "Is Site Local",
        "Is Unspecified",
    ]
    classification_section = _create_classification_section(
        "Address Classification", classification, classification_info
    )
    layout.addWidget(classification_section)

    # Network type section
    network_info = ["Private Network Type", "Special Range"]
    network_section = _create_classification_section("Network Information", classification, network_info)
    layout.addWidget(network_section)

    # Technical details section
    technical_info = ["Binary", "Decimal", "Hexadecimal"]
    technical_section = _create_classification_section("Technical Details", classification, technical_info)
    layout.addWidget(technical_section)

    layout.addStretch()


def _create_classification_section(title, classification, keys):
    """Create a section widget for classification results."""
    section_widget = QWidget()
    section_layout = QVBoxLayout(section_widget)
    section_layout.setContentsMargins(0, 5, 0, 15)

    # Section title
    title_label = QLabel(title)
    title_label.setStyleSheet("font-weight: bold; color: #666; font-size: 14px; margin-bottom: 5px;")
    section_layout.addWidget(title_label)

    # Create grid for section info
    grid = QGridLayout()
    row = 0
    for key in keys:
        if key in classification:
            label = QLabel(f"{key}:")
            label.setStyleSheet("font-weight: bold; color: #2196F3; margin-left: 10px;")
            value_label = QLabel(str(classification[key]))
            value_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
            value_label.setStyleSheet("font-family: monospace;")

            grid.addWidget(label, row, 0)
            grid.addWidget(value_label, row, 1)
            row += 1

    if row > 0:  # Only add grid if there are items
        grid_widget = QWidget()
        grid_widget.setLayout(grid)
        section_layout.addWidget(grid_widget)

    return section_widget


def _clear_layout(layout):
    """Clear all widgets from layout."""
    while layout.count():
        child = layout.takeAt(0)
        if child.widget():
            child.widget().deleteLater()


def get_error_input_style():
    """Get error styling for input fields."""
    return "border: 2px solid #d32f2f; background-color: #ffebee;"
