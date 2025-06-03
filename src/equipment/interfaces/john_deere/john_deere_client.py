"""
John Deere API client for accessing equipment data.
"""

import requests
import json
import logging
import os
import time
from datetime import datetime, timedelta
from urllib.parse import urljoin

logger = logging.getLogger(__name__)

class JohnDeereClient:
    """Client for interacting with the John Deere API."""
    
    # API endpoints
    BASE_URL = "https://sandboxapi.deere.com/platform/"
    AUTH_URL = "https://signin.johndeere.com/oauth2/aus78jtfhuot7t/v1/token"
    
    def __init__(self, client_id, client_secret, redirect_uri, config_file=None):
        """
        Initialize the John Deere API client.
        
        Args:
            client_id (str): OAuth client ID
            client_secret (str): OAuth client secret
            redirect_uri (str): OAuth redirect URI
            config_file (str, optional): Path to configuration file
        """
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri
        self.access_token = None
        self.refresh_token = None
        self.token_expiry = None
        self.organization_id = None
        self.equipment_data = {}
        
        # Load configuration if provided
        if config_file and os.path.exists(config_file):
            with open(config_file, 'r') as f:
                self.config = json.load(f)
                
                # Load saved tokens if available
                if 'access_token' in self.config:
                    self.access_token = self.config['access_token']
                if 'refresh_token' in self.config:
                    self.refresh_token = self.config['refresh_token']
                if 'token_expiry' in self.config:
                    self.token_expiry = datetime.fromisoformat(self.config['token_expiry'])
                if 'organization_id' in self.config:
                    self.organization_id = self.config['organization_id']
        
        logger.info("Initialized John Deere API client")
    
    def get_authorization_url(self, scope="ag1 eq1"):
        """
        Get the authorization URL for OAuth flow.
        
        Args:
            scope (str): OAuth scopes to request
            
        Returns:
            str: Authorization URL
        """
        auth_url = "https://signin.johndeere.com/oauth2/aus78jtfhuot7t/v1/authorize"
        params = {
            "client_id": self.client_id,
            "response_type": "code",
            "scope": scope,
            "redirect_uri": self.redirect_uri
        }
        
        # Build URL with parameters
        url_params = "&".join([f"{k}={v}" for k, v in params.items()])
        full_url = f"{auth_url}?{url_params}"
        
        return full_url
    
    def exchange_code_for_tokens(self, auth_code):
        """
        Exchange authorization code for access and refresh tokens.
        
        Args:
            auth_code (str): Authorization code from OAuth redirect
            
        Returns:
            bool: Success status
        """
        try:
            headers = {
                "Content-Type": "application/x-www-form-urlencoded"
            }
            
            data = {
                "grant_type": "authorization_code",
                "code": auth_code,
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "redirect_uri": self.redirect_uri
            }
            
            response = requests.post(self.AUTH_URL, headers=headers, data=data)
            response.raise_for_status()
            
            token_data = response.json()
            self.access_token = token_data.get("access_token")
            self.refresh_token = token_data.get("refresh_token")
            expires_in = token_data.get("expires_in", 3600)
            self.token_expiry = datetime.now() + timedelta(seconds=expires_in)
            
            logger.info("Successfully obtained access and refresh tokens")
            self._save_tokens()
            return True
        except Exception as e:
            logger.error(f"Failed to exchange code for tokens: {e}")
            return False
    
    def refresh_access_token(self):
        """
        Refresh the access token using the refresh token.
        
        Returns:
            bool: Success status
        """
        if not self.refresh_token:
            logger.error("No refresh token available")
            return False
            
        try:
            headers = {
                "Content-Type": "application/x-www-form-urlencoded"
            }
            
            data = {
                "grant_type": "refresh_token",
                "refresh_token": self.refresh_token,
                "client_id": self.client_id,
                "client_secret": self.client_secret
            }
            
            response = requests.post(self.AUTH_URL, headers=headers, data=data)
            response.raise_for_status()
            
            token_data = response.json()
            self.access_token = token_data.get("access_token")
            expires_in = token_data.get("expires_in", 3600)
            self.token_expiry = datetime.now() + timedelta(seconds=expires_in)
            
            # Update refresh token if provided
            if "refresh_token" in token_data:
                self.refresh_token = token_data["refresh_token"]
            
            logger.info("Successfully refreshed access token")
            self._save_tokens()
            return True
        except Exception as e:
            logger.error(f"Failed to refresh access token: {e}")
            return False
    
    def _save_tokens(self):
        """
        Save tokens to config file if available.
        """
        if hasattr(self, 'config'):
            self.config["access_token"] = self.access_token
            self.config["refresh_token"] = self.refresh_token
            if self.token_expiry:
                self.config["token_expiry"] = self.token_expiry.isoformat()
            if self.organization_id:
                self.config["organization_id"] = self.organization_id
                
            if hasattr(self, 'config_file') and self.config_file:
                try:
                    with open(self.config_file, 'w') as f:
                        json.dump(self.config, f, indent=2)
                    logger.info("Saved tokens to config file")
                except Exception as e:
                    logger.error(f"Failed to save tokens to config file: {e}")
    
    def _ensure_valid_token(self):
        """
        Ensure the access token is valid, refreshing if necessary.
        
        Returns:
            bool: True if a valid token is available
        """
        if not self.access_token:
            logger.error("No access token available")
            return False
            
        if self.token_expiry and datetime.now() >= self.token_expiry:
            logger.info("Access token expired, refreshing")
            return self.refresh_access_token()
            
        return True
    
    def _make_api_request(self, endpoint, method="GET", params=None, data=None):
        """
        Make a request to the John Deere API.
        
        Args:
            endpoint (str): API endpoint (appended to BASE_URL)
            method (str): HTTP method
            params (dict, optional): Query parameters
            data (dict, optional): Request body data
            
        Returns:
            dict or None: Response data or None on error
        """
        if not self._ensure_valid_token():
            return None
            
        url = urljoin(self.BASE_URL, endpoint)
        
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Accept": "application/vnd.deere.axiom.v3+json"
        }
        
        try:
            if method == "GET":
                response = requests.get(url, headers=headers, params=params)
            elif method == "POST":
                headers["Content-Type"] = "application/vnd.deere.axiom.v3+json"
                response = requests.post(url, headers=headers, params=params, json=data)
            elif method == "PUT":
                headers["Content-Type"] = "application/vnd.deere.axiom.v3+json"
                response = requests.put(url, headers=headers, params=params, json=data)
            elif method == "DELETE":
                response = requests.delete(url, headers=headers, params=params)
            else:
                logger.error(f"Unsupported method: {method}")
                return None
                
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"API request failed: {e}")
            return None
    
    def get_organizations(self):
        """
        Get a list of organizations the user has access to.
        
        Returns:
            list or None: List of organizations or None on error
        """
        response = self._make_api_request("organizations")
        if response and "values" in response:
            return response["values"]
        return None
    
    def set_organization(self, organization_id):
        """
        Set the active organization ID.
        
        Args:
            organization_id (str): Organization ID to use
        """
        self.organization_id = organization_id
        logger.info(f"Set active organization to {organization_id}")
        self._save_tokens()
    
    def get_equipment(self):
        """
        Get a list of equipment for the active organization.
        
        Returns:
            list or None: List of equipment or None on error
        """
        if not self.organization_id:
            logger.error("No organization ID set")
            return None
            
        endpoint = f"organizations/{self.organization_id}/machines"
        response = self._make_api_request(endpoint)
        
        if response and "values" in response:
            machines = response["values"]
            
            # Store equipment data for later use
            for machine in machines:
                if "id" in machine:
                    self.equipment_data[machine["id"]] = machine
                    
            return machines
        return None
    
    def get_equipment_details(self, equipment_id):
        """
        Get detailed information about a specific piece of equipment.
        
        Args:
            equipment_id (str): Equipment ID
            
        Returns:
            dict or None: Equipment details or None on error
        """
        if not self.organization_id:
            logger.error("No organization ID set")
            return None
            
        # Check cache first
        if equipment_id in self.equipment_data:
            # If we already have detailed data, return it
            if "detailed" in self.equipment_data[equipment_id]:
                return self.equipment_data[equipment_id]
        
        endpoint = f"organizations/{self.organization_id}/machines/{equipment_id}"
        response = self._make_api_request(endpoint)
        
        if response:
            # Cache the detailed data
            self.equipment_data[equipment_id] = response
            self.equipment_data[equipment_id]["detailed"] = True
            return response
        return None
    
    def get_equipment_location(self, equipment_id):
        """
        Get the current location of a specific piece of equipment.
        
        Args:
            equipment_id (str): Equipment ID
            
        Returns:
            dict or None: Location data or None on error
        """
        if not self.organization_id:
            logger.error("No organization ID set")
            return None
            
        endpoint = f"organizations/{self.organization_id}/machines/{equipment_id}/location"
        return self._make_api_request(endpoint)
    
    def get_equipment_measurements(self, equipment_id):
        """
        Get measurements for a specific piece of equipment.
        
        Args:
            equipment_id (str): Equipment ID
            
        Returns:
            dict or None: Measurement data or None on error
        """
        if not self.organization_id:
            logger.error("No organization ID set")
            return None
            
        endpoint = f"organizations/{self.organization_id}/machines/{equipment_id}/sensors"
        return self._make_api_request(endpoint)
    
    def save_equipment_data(self, filepath):
        """
        Save equipment data to a file.
        
        Args:
            filepath (str): Path to save the data
            
        Returns:
            bool: Success status
        """
        try:
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            
            data = {
                "timestamp": datetime.now().isoformat(),
                "organization_id": self.organization_id,
                "equipment": self.equipment_data
            }
            
            with open(filepath, 'w') as f:
                json.dump(data, f, indent=2)
                
            logger.info(f"Saved equipment data to {filepath}")
            return True
        except Exception as e:
            logger.error(f"Failed to save equipment data: {e}")
            return False
