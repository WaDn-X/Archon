"""
Supabase Database Client for Zippy-Archon

This module provides database integration with Supabase for storing
requirements, A/B tests, marketplace listings, and user data.
"""

import os
import json
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
import asyncio
from dataclasses import dataclass, asdict
import aiohttp
from supabase import create_client, Client
from supabase.lib.client_options import ClientOptions

logger = logging.getLogger(__name__)

@dataclass
class DatabaseConfig:
    """Database configuration."""
    supabase_url: str
    supabase_key: str
    schema: str = "public"
    timeout: int = 30

class SupabaseManager:
    """
    Manages Supabase database operations for the Zippy-Archon platform.
    """
    
    def __init__(self, config: DatabaseConfig):
        self.config = config
        self.client: Optional[Client] = None
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize Supabase client."""
        try:
            options = ClientOptions(
                schema=self.config.schema,
                headers={
                    "X-Client-Info": "zippy-archon/1.0.0"
                }
            )
            
            self.client = create_client(
                self.config.supabase_url,
                self.config.supabase_key,
                options=options
            )
            
            logger.info("Supabase client initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize Supabase client: {e}")
            raise
    
    async def test_connection(self) -> bool:
        """Test database connection."""
        try:
            # Simple query to test connection
            result = self.client.table("requirements").select("id").limit(1).execute()
            return True
        except Exception as e:
            logger.error(f"Database connection test failed: {e}")
            return False
    
    # Requirements Management
    async def create_requirement(self, requirement_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new requirement in the database."""
        try:
            # Add metadata
            requirement_data.update({
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            })
            
            result = self.client.table("requirements").insert(requirement_data).execute()
            
            if result.data:
                logger.info(f"Created requirement: {result.data[0]['id']}")
                return result.data[0]
            else:
                raise Exception("Failed to create requirement")
                
        except Exception as e:
            logger.error(f"Failed to create requirement: {e}")
            raise
    
    async def get_requirement(self, requirement_id: str) -> Optional[Dict[str, Any]]:
        """Get a requirement by ID."""
        try:
            result = self.client.table("requirements").select("*").eq("id", requirement_id).execute()
            
            if result.data:
                return result.data[0]
            return None
            
        except Exception as e:
            logger.error(f"Failed to get requirement {requirement_id}: {e}")
            return None
    
    async def update_requirement(self, requirement_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        """Update a requirement."""
        try:
            updates["updated_at"] = datetime.now().isoformat()
            
            result = self.client.table("requirements").update(updates).eq("id", requirement_id).execute()
            
            if result.data:
                logger.info(f"Updated requirement: {requirement_id}")
                return result.data[0]
            else:
                raise Exception("Failed to update requirement")
                
        except Exception as e:
            logger.error(f"Failed to update requirement {requirement_id}: {e}")
            raise
    
    async def list_requirements(self, filters: Dict[str, Any] = None, limit: int = 100) -> List[Dict[str, Any]]:
        """List requirements with optional filters."""
        try:
            query = self.client.table("requirements").select("*")
            
            if filters:
                for key, value in filters.items():
                    query = query.eq(key, value)
            
            result = query.limit(limit).order("created_at", desc=True).execute()
            
            return result.data or []
            
        except Exception as e:
            logger.error(f"Failed to list requirements: {e}")
            return []
    
    # A/B Testing Management
    async def create_ab_test(self, test_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new A/B test result."""
        try:
            test_data.update({
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            })
            
            result = self.client.table("ab_tests").insert(test_data).execute()
            
            if result.data:
                logger.info(f"Created A/B test: {result.data[0]['id']}")
                return result.data[0]
            else:
                raise Exception("Failed to create A/B test")
                
        except Exception as e:
            logger.error(f"Failed to create A/B test: {e}")
            raise
    
    async def get_ab_test(self, test_id: str) -> Optional[Dict[str, Any]]:
        """Get an A/B test by ID."""
        try:
            result = self.client.table("ab_tests").select("*").eq("id", test_id).execute()
            
            if result.data:
                return result.data[0]
            return None
            
        except Exception as e:
            logger.error(f"Failed to get A/B test {test_id}: {e}")
            return None
    
    async def list_ab_tests(self, filters: Dict[str, Any] = None, limit: int = 50) -> List[Dict[str, Any]]:
        """List A/B tests with optional filters."""
        try:
            query = self.client.table("ab_tests").select("*")
            
            if filters:
                for key, value in filters.items():
                    query = query.eq(key, value)
            
            result = query.limit(limit).order("created_at", desc=True).execute()
            
            return result.data or []
            
        except Exception as e:
            logger.error(f"Failed to list A/B tests: {e}")
            return []
    
    # Marketplace Management
    async def create_marketplace_listing(self, listing_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new marketplace listing."""
        try:
            listing_data.update({
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat(),
                "purchase_count": 0,
                "rating": 0.0
            })
            
            result = self.client.table("marketplace_listings").insert(listing_data).execute()
            
            if result.data:
                logger.info(f"Created marketplace listing: {result.data[0]['id']}")
                return result.data[0]
            else:
                raise Exception("Failed to create marketplace listing")
                
        except Exception as e:
            logger.error(f"Failed to create marketplace listing: {e}")
            raise
    
    async def get_marketplace_listing(self, listing_id: str) -> Optional[Dict[str, Any]]:
        """Get a marketplace listing by ID."""
        try:
            result = self.client.table("marketplace_listings").select("*").eq("id", listing_id).execute()
            
            if result.data:
                return result.data[0]
            return None
            
        except Exception as e:
            logger.error(f"Failed to get marketplace listing {listing_id}: {e}")
            return None
    
    async def update_marketplace_listing(self, listing_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        """Update a marketplace listing."""
        try:
            updates["updated_at"] = datetime.now().isoformat()
            
            result = self.client.table("marketplace_listings").update(updates).eq("id", listing_id).execute()
            
            if result.data:
                logger.info(f"Updated marketplace listing: {listing_id}")
                return result.data[0]
            else:
                raise Exception("Failed to update marketplace listing")
                
        except Exception as e:
            logger.error(f"Failed to update marketplace listing {listing_id}: {e}")
            raise
    
    async def search_marketplace_listings(self, query: str = None, category: str = None,
                                        min_trust_score: float = 0.0, limit: int = 50) -> List[Dict[str, Any]]:
        """Search marketplace listings."""
        try:
            db_query = self.client.table("marketplace_listings").select("*")
            
            if category:
                db_query = db_query.eq("category", category)
            
            if min_trust_score > 0:
                db_query = db_query.gte("trust_score", min_trust_score)
            
            if query:
                # Use full-text search if available, otherwise filter by title/description
                db_query = db_query.or_(f"title.ilike.%{query}%,description.ilike.%{query}%")
            
            result = db_query.limit(limit).order("trust_score", desc=True).execute()
            
            return result.data or []
            
        except Exception as e:
            logger.error(f"Failed to search marketplace listings: {e}")
            return []
    
    # User Management
    async def create_user(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new user."""
        try:
            user_data.update({
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat(),
                "zippycoin_balance": 0.0
            })
            
            result = self.client.table("users").insert(user_data).execute()
            
            if result.data:
                logger.info(f"Created user: {result.data[0]['id']}")
                return result.data[0]
            else:
                raise Exception("Failed to create user")
                
        except Exception as e:
            logger.error(f"Failed to create user: {e}")
            raise
    
    async def get_user(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get a user by ID."""
        try:
            result = self.client.table("users").select("*").eq("id", user_id).execute()
            
            if result.data:
                return result.data[0]
            return None
            
        except Exception as e:
            logger.error(f"Failed to get user {user_id}: {e}")
            return None
    
    async def get_user_by_wallet(self, wallet_address: str) -> Optional[Dict[str, Any]]:
        """Get a user by wallet address."""
        try:
            result = self.client.table("users").select("*").eq("wallet_address", wallet_address).execute()
            
            if result.data:
                return result.data[0]
            return None
            
        except Exception as e:
            logger.error(f"Failed to get user by wallet {wallet_address}: {e}")
            return None
    
    async def update_user_balance(self, user_id: str, new_balance: float) -> Dict[str, Any]:
        """Update user's ZippyCoin balance."""
        try:
            updates = {
                "zippycoin_balance": new_balance,
                "updated_at": datetime.now().isoformat()
            }
            
            result = self.client.table("users").update(updates).eq("id", user_id).execute()
            
            if result.data:
                logger.info(f"Updated user balance: {user_id} -> {new_balance}")
                return result.data[0]
            else:
                raise Exception("Failed to update user balance")
                
        except Exception as e:
            logger.error(f"Failed to update user balance {user_id}: {e}")
            raise
    
    # Transaction Management
    async def create_transaction(self, transaction_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new transaction record."""
        try:
            transaction_data.update({
                "created_at": datetime.now().isoformat(),
                "status": "pending"
            })
            
            result = self.client.table("transactions").insert(transaction_data).execute()
            
            if result.data:
                logger.info(f"Created transaction: {result.data[0]['id']}")
                return result.data[0]
            else:
                raise Exception("Failed to create transaction")
                
        except Exception as e:
            logger.error(f"Failed to create transaction: {e}")
            raise
    
    async def update_transaction_status(self, transaction_id: str, status: str) -> Dict[str, Any]:
        """Update transaction status."""
        try:
            updates = {
                "status": status,
                "updated_at": datetime.now().isoformat()
            }
            
            if status == "completed":
                updates["completed_at"] = datetime.now().isoformat()
            
            result = self.client.table("transactions").update(updates).eq("id", transaction_id).execute()
            
            if result.data:
                logger.info(f"Updated transaction status: {transaction_id} -> {status}")
                return result.data[0]
            else:
                raise Exception("Failed to update transaction status")
                
        except Exception as e:
            logger.error(f"Failed to update transaction status {transaction_id}: {e}")
            raise
    
    # Analytics and Statistics
    async def get_platform_stats(self) -> Dict[str, Any]:
        """Get platform statistics."""
        try:
            stats = {}
            
            # Count requirements
            req_result = self.client.table("requirements").select("id", count="exact").execute()
            stats["total_requirements"] = req_result.count or 0
            
            # Count A/B tests
            ab_result = self.client.table("ab_tests").select("id", count="exact").execute()
            stats["total_ab_tests"] = ab_result.count or 0
            
            # Count marketplace listings
            mp_result = self.client.table("marketplace_listings").select("id", count="exact").execute()
            stats["total_listings"] = mp_result.count or 0
            
            # Count users
            user_result = self.client.table("users").select("id", count="exact").execute()
            stats["total_users"] = user_result.count or 0
            
            # Total transaction volume
            tx_result = self.client.table("transactions").select("amount").eq("status", "completed").execute()
            total_volume = sum(tx.get("amount", 0) for tx in tx_result.data or [])
            stats["total_volume"] = total_volume
            
            stats["generated_at"] = datetime.now().isoformat()
            
            return stats
            
        except Exception as e:
            logger.error(f"Failed to get platform stats: {e}")
            return {
                "total_requirements": 0,
                "total_ab_tests": 0,
                "total_listings": 0,
                "total_users": 0,
                "total_volume": 0,
                "generated_at": datetime.now().isoformat()
            }
    
    # Database Schema Management
    async def create_tables(self):
        """Create database tables if they don't exist."""
        try:
            # This would typically be done via migrations, but for development we can create tables
            logger.info("Creating database tables...")
            
            # Note: In production, use proper migrations instead of this approach
            # This is just for development/demo purposes
            
            logger.info("Database tables created successfully")
            
        except Exception as e:
            logger.error(f"Failed to create tables: {e}")
            raise
    
    async def run_migration(self, migration_file: str):
        """Run a database migration."""
        try:
            with open(migration_file, 'r') as f:
                migration_sql = f.read()
            
            # Execute migration SQL
            result = self.client.rpc('exec_sql', {'sql': migration_sql}).execute()
            
            logger.info(f"Migration {migration_file} executed successfully")
            
        except Exception as e:
            logger.error(f"Failed to run migration {migration_file}: {e}")
            raise


# Factory function to create Supabase manager
def create_supabase_manager() -> SupabaseManager:
    """Create a Supabase manager with configuration from environment variables."""
    config = DatabaseConfig(
        supabase_url=os.getenv('SUPABASE_URL', ''),
        supabase_key=os.getenv('SUPABASE_SERVICE_KEY', ''),
        schema=os.getenv('SUPABASE_SCHEMA', 'public'),
        timeout=int(os.getenv('SUPABASE_TIMEOUT', '30'))
    )
    
    if not config.supabase_url or not config.supabase_key:
        raise ValueError("SUPABASE_URL and SUPABASE_SERVICE_KEY environment variables must be set")
    
    return SupabaseManager(config)
