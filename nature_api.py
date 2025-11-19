#!/usr/bin/env python3
"""
Nature.global API Client
Handles communication with the Nature Remo Cloud API
"""

import requests
import time
import logging
from typing import Dict, List, Optional

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class NatureAPI:
    """Client for Nature.global Cloud API"""
    
    BASE_URL = "https://api.nature.global"
    
    def __init__(self, access_token: str):
        """
        Initialize the API client
        
        Args:
            access_token: OAuth 2.0 Bearer token from home.nature.global
        """
        self.access_token = access_token
        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        })
    
    def _make_request(self, endpoint: str, method: str = 'GET', **kwargs) -> Optional[Dict]:
        """
        Make an API request with error handling and rate limit management
        
        Args:
            endpoint: API endpoint (e.g., '/1/devices')
            method: HTTP method (default: 'GET')
            **kwargs: Additional arguments to pass to requests
            
        Returns:
            JSON response as dict, or None if error occurred
        """
        url = f"{self.BASE_URL}{endpoint}"
        
        try:
            response = self.session.request(method, url, **kwargs)
            
            # Log rate limit information
            rate_limit = response.headers.get('X-Rate-Limit-Limit')
            rate_remaining = response.headers.get('X-Rate-Limit-Remaining')
            rate_reset = response.headers.get('X-Rate-Limit-Reset')
            
            if rate_limit:
                logger.debug(f"Rate limit: {rate_remaining}/{rate_limit}, resets at {rate_reset}")
            
            # Handle rate limiting (429 status)
            if response.status_code == 429:
                logger.warning("Rate limit exceeded. Waiting before retry...")
                reset_time = int(rate_reset) if rate_reset else int(time.time()) + 300
                wait_time = max(0, reset_time - int(time.time()))
                if wait_time > 0:
                    logger.info(f"Waiting {wait_time} seconds before retry...")
                    time.sleep(wait_time)
                # Retry once after waiting
                response = self.session.request(method, url, **kwargs)
            
            # Check for other errors
            response.raise_for_status()
            
            return response.json()
            
        except requests.exceptions.HTTPError as e:
            logger.error(f"HTTP error {response.status_code}: {e}")
            if response.status_code == 401:
                logger.error("Authentication failed. Check your access token.")
            elif response.status_code == 429:
                logger.error("Rate limit exceeded even after retry.")
            return None
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed: {e}")
            return None
    
    def get_devices(self) -> List[Dict]:
        """
        Get list of all devices
        
        Returns:
            List of device dictionaries
        """
        logger.info("Fetching devices...")
        response = self._make_request('/1/devices')
        if response:
            logger.info(f"Found {len(response)} device(s)")
            return response
        return []
    
    def get_appliances(self) -> List[Dict]:
        """
        Get list of all appliances
        
        Returns:
            List of appliance dictionaries
        """
        logger.info("Fetching appliances...")
        response = self._make_request('/1/appliances')
        if response:
            logger.info(f"Found {len(response)} appliance(s)")
            return response
        return []
    
    def get_echonetlite_appliances(self) -> List[Dict]:
        """
        Get list of ECHONET Lite appliances (for electricity monitoring)
        
        Returns:
            List of ECHONET Lite appliance dictionaries
        """
        logger.info("Fetching ECHONET Lite appliances...")
        response = self._make_request('/1/echonetlite/appliances')
        if response:
            # Response is a dict with 'appliances' key containing a list
            if isinstance(response, dict) and 'appliances' in response:
                appliances = response['appliances']
                logger.info(f"Found {len(appliances)} ECHONET Lite appliance(s)")
                return appliances
            elif isinstance(response, list):
                logger.info(f"Found {len(response)} ECHONET Lite appliance(s)")
                return response
            else:
                logger.warning(f"Unexpected response format: {type(response)}")
                return []
        return []

