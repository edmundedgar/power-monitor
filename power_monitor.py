#!/usr/bin/env python3
"""
Power Manager Bot - Monitor electricity usage from Nature.global Remo Lite device
"""

import os
import sys
import time
import signal
from datetime import datetime
from dateutil import parser as date_parser
from dotenv import load_dotenv
from nature_api import NatureAPI

# Load environment variables from .env file
load_dotenv()

# Global flag for graceful shutdown
shutdown_requested = False


def signal_handler(sig, frame):
    """Handle Ctrl+C gracefully"""
    global shutdown_requested
    print("\n\nShutting down gracefully...")
    shutdown_requested = True


def main():
    """Main entry point for the power monitor bot"""
    print("Power Manager Bot - Starting...")
    
    # Check if API token is configured
    api_token = os.getenv('NATURE_API_TOKEN')
    if not api_token or api_token == 'your_access_token_here':
        print("ERROR: NATURE_API_TOKEN not set in .env file")
        print("Please copy .env.example to .env and add your token")
        sys.exit(1)
    
    # Initialize API client
    api = NatureAPI(api_token)
    
    # Test connection by fetching devices
    print("\nTesting API connection...")
    devices = api.get_devices()
    if devices:
        print(f"✓ Successfully connected! Found {len(devices)} device(s)")
        for device in devices:
            device_name = device.get('name', 'Unknown')
            device_id = device.get('id', 'Unknown')
            print(f"  - Device: {device_name} (ID: {device_id})")
    else:
        print("✗ Failed to connect or no devices found")
        sys.exit(1)
    
    # Fetch appliances
    print("\nFetching appliances...")
    appliances = api.get_appliances()
    if appliances:
        print(f"Found {len(appliances)} appliance(s)")
        for appliance in appliances:
            appliance_name = appliance.get('nickname', 'Unknown')
            appliance_type = appliance.get('type', 'Unknown')
            print(f"  - {appliance_name} (Type: {appliance_type})")
    
    # Fetch ECHONET Lite appliances (for electricity monitoring)
    print("\nFetching ECHONET Lite appliances (for electricity monitoring)...")
    echonet_appliances = api.get_echonetlite_appliances()
    if echonet_appliances:
        print(f"Found {len(echonet_appliances)} ECHONET Lite appliance(s)")
        for appliance in echonet_appliances:
            appliance_name = appliance.get('nickname', 'Unknown')
            appliance_type = appliance.get('type', 'Unknown')
            print(f"\n  Appliance: {appliance_name} (Type: {appliance_type})")
            
            # Extract electricity usage from properties
            properties = appliance.get('properties', [])
            if properties:
                print("  Electricity Data:")
                for prop in properties:
                    epc = prop.get('epc', '').lower()
                    val = prop.get('val', '')
                    updated = prop.get('updated_at', '')
                    
                    try:
                        # Parse EPC codes based on ECHONET Lite smart meter specifications
                        if epc == 'e7':
                            # Instantaneous electric power (in hex, watts)
                            power_watts = int(val, 16)
                            print(f"    ⚡ Instantaneous Power: {power_watts} W ({power_watts/1000:.3f} kW)")
                        elif epc == 'e0':
                            # Cumulative electric energy (normal direction) - in Wh
                            energy_wh = int(val, 16)
                            energy_kwh = energy_wh / 1000.0
                            print(f"    📊 Cumulative Energy (normal): {energy_kwh:.3f} kWh ({energy_wh:,} Wh)")
                        elif epc == 'e3':
                            # Cumulative electric energy (reverse direction) - in Wh
                            energy_wh = int(val, 16)
                            energy_kwh = energy_wh / 1000.0
                            print(f"    🔄 Cumulative Energy (reverse): {energy_kwh:.3f} kWh ({energy_wh:,} Wh)")
                        elif epc == 'd3':
                            # Measured cumulative electric energy (effective power) - in Wh
                            energy_wh = int(val, 16)
                            energy_kwh = energy_wh / 1000.0
                            print(f"    📈 Cumulative Energy (effective): {energy_kwh:.3f} kWh ({energy_wh:,} Wh)")
                        elif epc == 'd7':
                            # Unit for cumulative electric energy (effective power)
                            unit_code = int(val, 16) if val else 0
                            unit_map = {0: 'Wh', 1: '0.1 kWh', 2: '0.01 kWh', 3: '0.001 kWh', 4: '0.0001 kWh'}
                            unit_str = unit_map.get(unit_code, f'Unknown (code: {unit_code})')
                            print(f"    📏 Energy Unit (effective): {unit_str}")
                        elif epc == 'e1':
                            # Unit for cumulative electric energy
                            unit_code = int(val, 16) if val else 0
                            unit_map = {0: 'Wh', 1: '0.1 kWh', 2: '0.01 kWh', 3: '0.001 kWh', 4: '0.0001 kWh'}
                            unit_str = unit_map.get(unit_code, f'Unknown (code: {unit_code})')
                            print(f"    📏 Energy Unit: {unit_str}")
                        else:
                            # Unknown EPC code - display raw value
                            print(f"    ❓ EPC {epc}: {val} (hex, updated: {updated})")
                    except (ValueError, TypeError) as e:
                        print(f"    ⚠️  EPC {epc}: {val} (could not parse: {e})")
    else:
        print("No ECHONET Lite appliances found")
    
    print("\nAPI client is ready!")
    
    # Find the smart meter appliance
    echonet_appliances = api.get_echonetlite_appliances()
    if not echonet_appliances:
        print("No ECHONET Lite appliances found. Cannot start monitoring.")
        sys.exit(1)
    
    # Use the first smart meter found
    smart_meter = echonet_appliances[0]
    appliance_id = smart_meter.get('id', '')
    appliance_name = smart_meter.get('nickname', 'Unknown')
    
    print(f"\n{'='*60}")
    print(f"Starting continuous monitoring for: {appliance_name}")
    print(f"{'='*60}")
    print("Press Ctrl+C to stop\n")
    
    # Set up signal handler for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    
    # Polling configuration
    # API updates data every 60 seconds
    # Poll 60 seconds after last updated time + 1 second buffer
    UPDATE_INTERVAL = 60  # seconds
    BUFFER_SECONDS = 1    # buffer to account for slight delays
    last_updated_at_str = None
    last_updated_timestamp = None
    
    # Backoff configuration for when updates don't arrive
    backoff_count = 0
    BACKOFF_INITIAL = 5   # Start with 5 seconds
    BACKOFF_MAX = 60      # Max 60 seconds between polls
    BACKOFF_MULTIPLIER = 1.5  # Multiply by this each time
    
    try:
        while not shutdown_requested:
            # Fetch instantaneous power (quiet mode to reduce log noise)
            power_data = api.get_instantaneous_power(appliance_id, quiet=True)
            
            if power_data:
                power_watts = power_data['power_watts']
                power_kw = power_data['power_kw']
                updated_at_str = power_data['updated_at']
                timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                
                # Parse the updated_at timestamp
                try:
                    updated_at_dt = date_parser.parse(updated_at_str)
                    # Convert to Unix timestamp
                    updated_at_ts = updated_at_dt.timestamp()
                except (ValueError, TypeError) as e:
                    print(f"[{timestamp}] ⚠️  Failed to parse updated_at timestamp: {e}")
                    updated_at_ts = time.time()
                
                # Check if this is new data
                is_new_data = (updated_at_str != last_updated_at_str) if last_updated_at_str else True
                
                if is_new_data:
                    # New data arrived - reset backoff and display
                    new_indicator = "🆕"
                    print(f"[{timestamp}] {new_indicator} Instantaneous Power: {power_watts:>6} W ({power_kw:>7.3f} kW) | Updated: {updated_at_str}")
                    last_updated_at_str = updated_at_str
                    last_updated_timestamp = updated_at_ts
                    backoff_count = 0  # Reset backoff counter
                else:
                    # Same data - we're waiting for an update
                    backoff_count += 1
                    # Calculate backoff wait time (exponential backoff with max cap)
                    backoff_wait = min(BACKOFF_INITIAL * (BACKOFF_MULTIPLIER ** (backoff_count - 1)), BACKOFF_MAX)
                    print(f"[{timestamp}] ⏳ Waiting for update... (backoff: {backoff_wait:.1f}s) | Current: {power_watts} W | Last updated: {updated_at_str}")
                    
                    # Sleep with backoff
                    sleep_until = time.time() + backoff_wait
                    while time.time() < sleep_until and not shutdown_requested:
                        time.sleep(min(1.0, sleep_until - time.time()))
                    continue  # Skip the normal sleep calculation below
            else:
                timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                print(f"[{timestamp}] ⚠️  Failed to fetch power data")
                # If we failed but have a previous timestamp, use that for next poll
                if last_updated_timestamp is None:
                    # No previous data, wait a short time before retry
                    time.sleep(5)
                    continue
            
            # Calculate next poll time: 60 seconds after last update + 1 second buffer
            # (Only reached if we got new data)
            if last_updated_timestamp is not None:
                next_poll_time = last_updated_timestamp + UPDATE_INTERVAL + BUFFER_SECONDS
                current_time = time.time()
                sleep_duration = max(0, next_poll_time - current_time)
                
                if sleep_duration > 0:
                    # Sleep in small increments to allow for graceful shutdown
                    sleep_until = time.time() + sleep_duration
                    while time.time() < sleep_until and not shutdown_requested:
                        time.sleep(min(1.0, sleep_until - time.time()))
                else:
                    # We're already past the expected time, poll immediately (just a tiny delay)
                    time.sleep(0.1)
            else:
                # No timestamp available, wait a default interval
                time.sleep(UPDATE_INTERVAL)
                
    except KeyboardInterrupt:
        pass
    finally:
        print("\n\nMonitoring stopped.")


if __name__ == '__main__':
    main()

