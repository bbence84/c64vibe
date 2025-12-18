#!/usr/bin/env python3
"""
KungFuFlash USB Interface Library

This module provides a Python interface to communicate with the KungFuFlash2
cartridge via USB serial, implementing the EasyFlash 3 USB protocol.

Based on the EF3 USB utilities by Tom-Cat.
"""

import serial
import serial.tools.list_ports
import time
import struct
from pathlib import Path
from typing import Optional, Union


class KungFuFlashUSB:
    """
    Interface for communicating with KungFuFlash2 cartridge via USB serial.
    
    This class implements the EasyFlash 3 USB protocol for sending PRG files
    and controlling the cartridge.
    """
    
    def __init__(self, port: Optional[str] = None, baudrate: int = 115200, timeout: float = 5.0):
        """
        Initialize the KungFuFlash USB interface.
        
        Args:
            port: Serial port name (e.g., 'COM3' on Windows, '/dev/ttyACM0' on Linux)
            baudrate: Baud rate for serial communication (default: 115200)
            timeout: Timeout in seconds for serial operations (default: 5.0)
        """
        if port is None:
            self.port = self.find_kungfuflash()
            if self.port is None:
                raise RuntimeError("Could not find KungFuFlash device automatically. Please specify the port.")
        else:
            self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self.serial: Optional[serial.Serial] = None

    def get_port(self) -> str:
        """Get the current serial port."""
        return self.port

    def find_kungfuflash(self) -> Optional[str]:
        """
        Attempt to find a KungFuFlash2 device automatically.
        
        Returns:
            str: Port name if found, None otherwise
        """
        ports = serial.tools.list_ports.comports()
        for port in ports:
            # KungFuFlash2 shows up as a standard CDC/ACM serial device
            # You might need to adjust this detection logic
            if 'USB' in port.description or 'Serial' in port.description:
                print(f"Found potential device: {port.device} - {port.description}")
                return port.device
        return None

    def __enter__(self):
        """Context manager entry."""
        self.connect()
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.disconnect()
        
    def connect(self) -> None:
        """
        Open the serial connection to the KungFuFlash cartridge.
        
        Raises:
            serial.SerialException: If connection fails
        """
        if self.serial and self.serial.is_open:
            return
            
        self.serial = serial.Serial(
            port=self.port,
            baudrate=self.baudrate,
            timeout=self.timeout,
            bytesize=serial.EIGHTBITS,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE
        )
        
        # Small delay to let the connection stabilize
        time.sleep(0.1)
        
        # Flush any existing data
        self.serial.reset_input_buffer()
        self.serial.reset_output_buffer()
        
    def disconnect(self) -> None:
        """Close the serial connection."""
        if self.serial and self.serial.is_open:
            self.serial.close()
            self.serial = None
            
    def _send_handshake(self, command: str, max_retries: int = 4) -> bool:
        """
        Send a handshake command and wait for response.
        
        Args:
            command: Command string (e.g., "PRG", "CRT", "MENU")
            max_retries: Maximum number of retry attempts
            
        Returns:
            True if handshake successful, False otherwise
        """
        if not self.serial or not self.serial.is_open:
            raise RuntimeError("Serial port not connected")
            
        # The handshake is exactly 12 bytes: "EFSTART:PRG" + null byte
        handshake = f"EFSTART:{command.upper()}\x00".encode('ascii')
        
        if len(handshake) != 12:
            raise RuntimeError(f"Handshake must be exactly 12 bytes, got {len(handshake)}")
        
        for attempt in range(max_retries):
            # Flush any stale data before attempting handshake
            self.serial.reset_input_buffer()
            self.serial.reset_output_buffer()
            
            # Send handshake (12 bytes)
            bytes_written = self.serial.write(handshake)
            if bytes_written != 12:
                print(f"Handshake attempt {attempt + 1}: Failed to write all bytes ({bytes_written}/12)")
                time.sleep(0.5)
                continue
                
            self.serial.flush()
            
            # Give the C64 launcher time to process and respond
            # The C64 needs to switch modes and load the ef3usb handler
            if attempt == 0:
                time.sleep(1.5)  # First attempt needs more time for C64 to initialize
            else:
                time.sleep(0.5)
            
            # Read response (4 bytes + null terminator = 5 bytes)
            try:
                response = self.serial.read(5)
                
                if len(response) == 0:
                    print(f"Handshake attempt {attempt + 1}: No response from device (may still be initializing)")
                    time.sleep(1)
                    continue
                elif len(response) != 5:
                    print(f"Handshake attempt {attempt + 1}: Invalid response length ({len(response)} bytes): {response.hex()}")
                    time.sleep(0.5)
                    continue
                    
                response_str = response[:4].decode('ascii', errors='ignore')
                print(f"Handshake response: [{response_str}]")
                
                if response_str == "WAIT":
                    print("Device busy, waiting...")
                    time.sleep(1)
                    continue
                elif response_str == "LOAD" or response_str.startswith("L"):
                    return True
                else:
                    print(f"Unexpected response: {response_str} (hex: {response.hex()})")
                    # Don't return False yet, retry
                    time.sleep(0.5)
                    continue
                    
            except (serial.SerialTimeoutException, UnicodeDecodeError) as e:
                print(f"Handshake attempt {attempt + 1} failed: {e}")
                time.sleep(0.5)
                continue
                
        return False
        
    def send_prg(self, filename: Union[str, Path], verbose: bool = False) -> bool:
        """
        Send a PRG file to the KungFuFlash cartridge and execute it.
        
        This function sends a PRG file via USB and starts it on the C64.
        The cartridge must be in the launcher menu for this to work.
        
        Args:
            filename: Path to the PRG file to send
            verbose: Print progress information
            
        Returns:
            True if successful, False otherwise
            
        Raises:
            FileNotFoundError: If the PRG file doesn't exist
            RuntimeError: If serial port is not connected
        """
        if not self.serial or not self.serial.is_open:
            raise RuntimeError("Serial port not connected")
            
        filepath = Path(filename)
        if not filepath.exists():
            raise FileNotFoundError(f"PRG file not found: {filename}")
            
        # Read the PRG file
        with open(filepath, 'rb') as f:
            prg_data = f.read()
            
        if len(prg_data) < 2:
            print("Error: PRG file too small (must be at least 2 bytes)")
            return False
            
        if verbose:
            print(f"Loaded PRG file: {filepath.name} ({len(prg_data)} bytes)")
            
        # Send handshake
        if verbose:
            print("Sending handshake: EFSTART:PRG")
            
        if not self._send_handshake("PRG"):
            print("Handshake failed")
            return False
            
        if verbose:
            print("Sending PRG file...")
            
        # Read how many bytes the device wants
        chunk_size_bytes = self.serial.read(2)
        if len(chunk_size_bytes) != 2:
            print("Error: Could not read chunk size")
            return False
            
        chunk_size = struct.unpack('<H', chunk_size_bytes)[0]
        
        total_sent = 0
        offset = 0
        
        while offset < len(prg_data):
            # Determine how many bytes to send in this chunk
            remaining = len(prg_data) - offset
            send_size = min(remaining, chunk_size)
            
            chunk = prg_data[offset:offset + send_size]
            
            # Send chunk size (little-endian 16-bit)
            size_bytes = struct.pack('<H', len(chunk))
            if self.serial.write(size_bytes) != 2:
                print("\nError: Failed to send chunk size")
                return False
                
            # Send chunk data
            if self.serial.write(chunk) != len(chunk):
                print("\nError: Failed to send chunk data")
                return False
                
            total_sent += len(chunk)
            offset += len(chunk)
            
            if verbose:
                print(f"\rBytes sent: {total_sent:6d}", end='', flush=True)
                
            # If we sent less than chunk_size, we're done
            if len(chunk) < chunk_size:
                break
                
        if verbose:
            print("\n\nDONE!")
            
        return True
        
    def return_to_menu(self, verbose: bool = False, reconnect: bool = True) -> bool:
        """
        Send the command to return to the launcher menu.
        
        The firmware monitors the USB stream for the menu command and will
        restart to the menu when detected. This works during PRG execution
        and in the main USB forwarding loop.
        
        Note: The cartridge will perform a system reset, which disconnects USB.
        By default, this function will automatically reconnect after the reset.
        
        Args:
            verbose: Print status information
            reconnect: Automatically reconnect after reset (default: True)
            
        Returns:
            True if command sent successfully
            
        Raises:
            RuntimeError: If serial port is not connected
        """
        if not self.serial or not self.serial.is_open:
            raise RuntimeError("Serial port not connected")
            
        if verbose:
            print("Sending return to menu command...")
            
        # Send the efstart:mnu command (must be exactly 12 bytes with null terminator)
        # Format: "efstart:" (8 bytes) + "mnu" (3 bytes) + "\x00" (1 byte) = 12 bytes
        # Note: Using "mnu" instead of "menu" to fit the 12-byte protocol limit
        command = b"efstart:mnu\x00"
        
        if len(command) != 12:
            raise RuntimeError(f"Menu command must be exactly 12 bytes, got {len(command)}")
            
        self.serial.write(command)
        self.serial.flush()
        
        if verbose:
            print("Menu command sent. Cartridge is restarting...")
        
        # The cartridge will reset, which disconnects USB
        # Close our connection and wait for the device to reset
        self.disconnect()
        
        if reconnect:
            # Wait for the cartridge to reset and USB to reinitialize
            if verbose:
                print("Waiting for cartridge to restart...")
            time.sleep(2.0)  # Give the device time to reset
            
            # Reconnect
            if verbose:
                print("Reconnecting...")
            
            max_retries = 4
            for attempt in range(max_retries):
                try:
                    self.connect()
                    if verbose:
                        print(f"Reconnected to {self.port}")
                    return True
                except Exception as e:
                    if attempt < max_retries - 1:
                        if verbose:
                            print(f"Reconnect attempt {attempt + 1} failed, retrying...")
                        time.sleep(0.5)
                    else:
                        if verbose:
                            print(f"Failed to reconnect: {e}")
                        return False
        
        return True
        
    def send_crt(self, filename: Union[str, Path], verbose: bool = False) -> bool:
        """
        Send a CRT file to the KungFuFlash cartridge.
        
        Note: This is a basic implementation. The full CRT protocol is more complex.
        
        Args:
            filename: Path to the CRT file to send
            verbose: Print progress information
            
        Returns:
            True if successful, False otherwise
            
        Raises:
            FileNotFoundError: If the CRT file doesn't exist
            RuntimeError: If serial port is not connected
        """
        if not self.serial or not self.serial.is_open:
            raise RuntimeError("Serial port not connected")
            
        filepath = Path(filename)
        if not filepath.exists():
            raise FileNotFoundError(f"CRT file not found: {filename}")
            
        # Read the CRT file
        with open(filepath, 'rb') as f:
            crt_data = f.read()
            
        if verbose:
            print(f"Loaded CRT file: {filepath.name} ({len(crt_data)} bytes)")
            
        # Send handshake
        if verbose:
            print("Sending handshake: EFSTART:CRT")
            
        if not self._send_handshake("CRT"):
            print("Handshake failed")
            return False
            
        if verbose:
            print("Sending CRT file...")
            
        # Send the entire file
        total_sent = 0
        chunk_size = 4096  # Send in 4KB chunks
        
        for i in range(0, len(crt_data), chunk_size):
            chunk = crt_data[i:i + chunk_size]
            sent = self.serial.write(chunk)
            total_sent += sent
            
            if verbose:
                print(f"\rBytes sent: {total_sent:6d}", end='', flush=True)
                
        if verbose:
            print("\n\nDONE!")
            
        return True


def main():
    """Example usage of the KungFuFlashUSB class."""
    import sys
    
    if len(sys.argv) < 3:
        print("Usage: python kungfuflash_usb.py <port> <command> [file]")
        print("\nCommands:")
        print("  send <file.prg>   - Send and execute a PRG file")
        print("  menu              - Return to launcher menu")
        print("\nExamples:")
        print("  python kungfuflash_usb.py COM3 send myprogram.prg")
        print("  python kungfuflash_usb.py /dev/ttyACM0 menu")
        sys.exit(1)
        
    port = sys.argv[1]
    command = sys.argv[2].lower()
    
    try:
        with KungFuFlashUSB(port) as kff:
            if command == "send":
                if len(sys.argv) < 4:
                    print("Error: PRG filename required")
                    sys.exit(1)
                filename = sys.argv[3]
                success = kff.send_prg(filename)
                sys.exit(0 if success else 1)
                
            elif command == "menu":
                success = kff.return_to_menu()
                sys.exit(0 if success else 1)
                
            else:
                print(f"Unknown command: {command}")
                sys.exit(1)
                
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
