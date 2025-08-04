"""
Example configuration file for the MCP PostgreSQL Natural Language Query Server.
Copy this file to config.py and modify the settings as needed.
"""

import os

# LLM Client Configuration
# These settings can be used by LLM clients for SQL generation
LLM_MODEL = "claude-3-sonnet"  # or your preferred model
LLM_TEMPERATURE = 0.1  # Lower temperature for more consistent SQL generation
LLM_MAX_TOKENS = 500

# Database Configuration
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': os.getenv('DB_PORT', '5432'),
    'database': os.getenv('DB_NAME', 'postgres'),
    'user': os.getenv('DB_USER', 'postgres'),
    'password': os.getenv('DB_PASSWORD', ''),
    'sslmode': os.getenv('DB_SSLMODE', 'prefer'),  # prefer, require, disable
}

# Server Configuration
SERVER_NAME = "postgres-nl-query-server"
LOG_LEVEL = "INFO"  # DEBUG, INFO, WARNING, ERROR

# Query Configuration
MAX_RESULTS = 1000  # Maximum number of rows to return
QUERY_TIMEOUT = 240  # Query timeout in seconds

# Schema Configuration
SCHEMA_CACHE_TTL = 300  # Schema cache time-to-live in seconds
AUTO_REFRESH_SCHEMA = True  # Automatically refresh schema information 
