#!/usr/bin/env python3
"""
Example usage of the KungFuFlashUSB library.

This demonstrates how to use the library to send PRG files and control
the KungFuFlash2 cartridge programmatically.
"""

from kungfuflash_usb import KungFuFlashUSB
from pathlib import Path
import time


def example_send_prg(file: str = 'word.prg'):
    """Example: Send a PRG file to the cartridge."""
    
    # Create interface (adjust port for your system)
    # Windows: 'COM3', 'COM4', etc.
    # Linux: '/dev/ttyACM0', '/dev/ttyACM1', etc.
    # macOS: '/dev/cu.usbmodem1234', etc.
    
    prg_file = file  # Change this to your PRG file
    
    try:
        # Using context manager (recommended)
        with KungFuFlashUSB() as kff:
            print(f"Connected to KungFuFlash on {kff.get_port()}")
            print(f"Sending {prg_file}...")
            
            # Send and execute the PRG file
            success = kff.send_prg(prg_file)
            
            if success:
                print("Program sent and started successfully!")
            else:
                print("Failed to send program.")
                
    except FileNotFoundError as e:
        print(f"Error: {e}")
    except Exception as e:
        print(f"Communication error: {e}")

def return_to_menu():
    """Example: Return to the KungFuFlash menu.
    
    The firmware monitors the USB stream for the 'efstart:mnu\x00' command.
    This allows you to return to the menu programmatically without pressing 
    the physical menu button.
    
    IMPORTANT: 
    - USB must be connected and active
    - The firmware will detect the command and restart to the menu
    - This works during PRG execution and in the main USB forwarding loop
    """
    
    try:
        with KungFuFlashUSB() as kff:
            print(f"Connected to KungFuFlash on {kff.get_port()}")
            print("Returning to menu...")
            kff.return_to_menu()
            print("Menu command sent!")
            
    except Exception as e:
        print(f"Error: {e}")

def example_send_and_return():
    """Example: Send a PRG file, wait, then return to menu.
    
    This demonstrates the complete workflow:
    1. Load a PRG via USB
    2. Let the program run
    3. Send the menu command to return to the launcher
    
    The firmware monitors the USB stream for the 'efstart:mnu\x00' command
    and will restart to the menu when it detects this command.
    """
    
    prg_file = 'word.prg'
    
    try:
        with KungFuFlashUSB() as kff:
            # Send the program via USB - USB stays active for menu command
            print("Sending program via USB...")
            if not kff.send_prg(prg_file):
                print("Failed to send program")
                return
                
            print("Program is running on C64 with USB active...")
            print("Firmware is monitoring USB for menu command...")
            
            # Wait for some time (let the program run)
            print("Waiting 10 seconds...")
            time.sleep(10)
            
            # Now return to menu - firmware will detect this command
            print("Returning to menu...")
            kff.return_to_menu()
            
            print("Done! The C64 should restart to the menu within a moment.")
            print("(The menu command is detected on the next IRQ interrupt)")
            
    except Exception as e:
        print(f"Error: {e}")


def example_manual_connection():
    """Example: Manual connection management."""

    
    # Create interface without context manager
    kff = KungFuFlashUSB(baudrate=115200, timeout=5.0)
    
    try:
        # Manually connect
        kff.connect()
        print(f"Connected to {kff.get_port()}")
        
        # Do something
        kff.return_to_menu()
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        # Always disconnect when done
        kff.disconnect()
        print("Disconnected")


def example_batch_send():
    """Example: Send multiple PRG files in sequence."""
    
    prg_files = ['demo1.prg', 'demo2.prg', 'demo3.prg']
    
    try:
        with KungFuFlashUSB() as kff:
            for prg_file in prg_files:
                if not Path(prg_file).exists():
                    print(f"Skipping {prg_file} (not found)")
                    continue
                    
                print(f"\nSending {prg_file}...")
                if kff.send_prg(prg_file):
                    print(f"✓ {prg_file} sent successfully")
                    
                    # Wait a bit
                    time.sleep(2)
                    
                    # Return to menu for next file
                    kff.return_to_menu()
                    time.sleep(1)
                else:
                    print(f"✗ Failed to send {prg_file}")
                    
    except Exception as e:
        print(f"Error: {e}")


def example_automated_testing():
    """Example: Automated testing workflow."""
    
    test_program = 'unittest.prg'
    
    try:
        with KungFuFlashUSB() as kff:
            print("Starting automated test...")
            
            # 1. Send test program
            print("Step 1: Sending test program...")
            if not kff.send_prg(test_program):
                print("ERROR: Could not send test program")
                return False
                
            # 2. Wait for test to complete (hypothetical)
            print("Step 2: Running tests...")
            time.sleep(5)
            
            # 3. Return to menu
            print("Step 3: Returning to menu...")
            kff.return_to_menu()
            time.sleep(1)
            
            print("Test cycle complete!")
            return True
            
    except Exception as e:
        print(f"Test failed with error: {e}")
        return False


if __name__ == '__main__':
    print("KungFuFlash USB Library Examples")
    print("=" * 50)
    print("\nThese are example functions. Edit the script to:")
    print("1. Set your correct serial port")
    print("2. Specify your PRG files")
    print("3. Uncomment the example you want to run\n")
    
    # Uncomment one of these to run:
    
    # Use this to test sending a PRG and returning to menu
    return_to_menu()
    time.sleep(3)

    example_send_prg('temp_program.prg')

    time.sleep(5)

    #return_to_menu()
    #example_send_prg()
    
    # Other examples:
    #example_send_prg()
    # example_manual_connection()
    # example_batch_send()
    # example_automated_testing()

    
