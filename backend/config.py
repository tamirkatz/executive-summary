import os
from typing import Optional
from pathlib import Path


class Config:
    """Centralized configuration management for the application."""
    
    def __init__(self):
        # Load environment variables from .env file if it exists
        self._load_env_file()
        
        # API Keys
        self.TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")
        self.OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
        
        # Check if all API keys are set
        if not self.TAVILY_API_KEY:
            raise ValueError("TAVILY_API_KEY is not configured")
        if not self.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY is not configured")
        
        # Database Configuration
        self.MONGODB_URI = os.getenv("MONGODB_URI", "mongodb+srv://tamirkatz1234:a62CoHwmwpmHNQ5f@executive.e6ythg6.mongodb.net/?retryWrites=true&w=majority&appName=executive")
        
        # Application Configuration
        self.PORT = int(os.getenv("PORT", "8000"))
        self.ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
        self.LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
        
        # Optional External Services
        self.REDIS_URL = os.getenv("REDIS_URL", None)
        self.SENTRY_DSN = os.getenv("SENTRY_DSN", None)
    
    def _load_env_file(self):
        """Load environment variables from .env file."""
        env_path = Path(__file__).parent.parent / '.env'
        if env_path.exists():
            with open(env_path, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        os.environ[key.strip()] = value.strip()
    
    def _get_required_env(self, key: str) -> str:
        """Get a required environment variable."""
        value = os.getenv(key)
        if not value:
            raise ValueError(f"Required environment variable {key} is not set")
        return value
    
    def _get_env(self, key: str, default: Optional[str] = None) -> Optional[str]:
        """Get an optional environment variable."""
        return os.getenv(key, default)
    
    def is_development(self) -> bool:
        """Check if running in development mode."""
        return self.ENVIRONMENT.lower() == "development"
    
    def is_production(self) -> bool:
        """Check if running in production mode."""
        return self.ENVIRONMENT.lower() == "production"
    
    def get_mongodb_config(self) -> dict:
        """Get MongoDB configuration."""
        return {
            "uri": self.MONGODB_URI,
            "database": "tavily_research",
            "collections": {
                "jobs": "jobs",
                "reports": "reports",
                "companies": "companies",
                "competitors": "competitors",
                "domains": "domains"
            }
        }
    
    def get_api_keys(self) -> dict:
        """Get all API keys."""
        return {
            "tavily": self.TAVILY_API_KEY,
            "openai": self.OPENAI_API_KEY
        }
    
    def validate_config(self) -> bool:
        """Validate that all required configuration is present."""
        try:
            # Check required API keys
            assert self.TAVILY_API_KEY, "TAVILY_API_KEY is required"
            assert self.OPENAI_API_KEY, "OPENAI_API_KEY is required"
            
            # Check MongoDB URI
            assert self.MONGODB_URI, "MONGODB_URI is required"
            
            return True
        except AssertionError as e:
            print(f"Configuration validation failed: {e}")
            return False


# Global configuration instance
config = Config()


# Convenience functions for backward compatibility
def get_tavily_api_key() -> str:
    """Get Tavily API key."""
    return config.TAVILY_API_KEY


def get_openai_api_key() -> str:
    """Get OpenAI API key."""
    return config.OPENAI_API_KEY


def get_mongodb_uri() -> str:
    """Get MongoDB URI."""
    return config.MONGODB_URI


def is_mongodb_enabled() -> bool:
    """Check if MongoDB is enabled."""
    return bool(config.MONGODB_URI and config.MONGODB_URI != "mongodb://localhost:27017/tavily_research") 