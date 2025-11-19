#!/usr/bin/env python3
"""
Power Manager Bot - Monitor electricity usage from Nature.global Remo Lite device
"""

import os
import sys
from dotenv import load_dotenv
from nature_api import NatureAPI

# Load environment variables from .env file
load_dotenv()


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
    # TODO: Implement monitoring logic


if __name__ == '__main__':
    main()

