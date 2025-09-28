"""
Tests for the plugin system including plugin manager, trust manager, and marketplace
"""

import pytest
import asyncio
from unittest.mock import patch, MagicMock, AsyncMock
import sys
import os

# Add the project root to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'agentic-workflow'))

from plugins.plugin_manager import register_tool, load_plugins, get_tool_by_name, TOOLS_REGISTRY
from plugins.trust_manager import ZippyTrustManager, TrustScore, PluginMetadata
from plugins.marketplace import ZippyCoinMarketplace, MarketplaceListing

class TestPluginManager:
    """Test suite for plugin management system."""

    def setup_method(self):
        """Clear the tools registry before each test."""
        TOOLS_REGISTRY.clear()

    def test_register_tool(self):
        """Test tool registration."""
        class TestTool:
            name = "test_tool"
            description = "A test tool"
            
            def run(self, *args, **kwargs):
                return "test_result"
        
        register_tool(TestTool())
        assert "test_tool" in TOOLS_REGISTRY
        assert TOOLS_REGISTRY["test_tool"].name == "test_tool"

    def test_register_duplicate_tool(self):
        """Test that duplicate tool names raise an error."""
        class TestTool:
            name = "duplicate_tool"
            description = "A test tool"
            
            def run(self, *args, **kwargs):
                return "test_result"
        
        register_tool(TestTool())
        
        with pytest.raises(ValueError, match="Tool 'duplicate_tool' is already registered"):
            register_tool(TestTool())

    def test_get_tool_by_name(self):
        """Test retrieving tools by name."""
        class TestTool:
            name = "retrievable_tool"
            description = "A retrievable tool"
            
            def run(self, *args, **kwargs):
                return "retrieved_result"
        
        register_tool(TestTool())
        
        tool = get_tool_by_name("retrievable_tool")
        assert tool is not None
        assert tool.name == "retrievable_tool"
        assert tool.run() == "retrieved_result"

    def test_get_nonexistent_tool(self):
        """Test retrieving non-existent tools."""
        tool = get_tool_by_name("nonexistent_tool")
        assert tool is None

    @patch('plugins.plugin_manager.importlib.import_module')
    def test_load_plugins(self, mock_import_module):
        """Test dynamic plugin loading."""
        # Mock module with tools
        mock_module = MagicMock()
        mock_module.test_tool = MagicMock()
        mock_module.test_tool.name = "test_tool"
        mock_module.test_tool.description = "Test tool"
        mock_module.test_tool.run = MagicMock(return_value="test_result")
        
        mock_import_module.return_value = mock_module
        
        # Mock os.listdir to return plugin files
        with patch('plugins.plugin_manager.os.listdir') as mock_listdir:
            mock_listdir.return_value = ['test_plugin.py', '__init__.py']

            # Use the correct parameter name for load_plugins
            plugins_directory = 'plugins'
            load_plugins(plugins_directory)

            assert "test_tool" in TOOLS_REGISTRY

    def test_tool_protocol_compliance(self):
        """Test that tools must implement the required protocol."""
        class InvalidTool:
            # Missing name and description
            def run(self, *args, **kwargs):
                return "result"
        
        # Should not be able to register invalid tools
        with pytest.raises(AttributeError):
            register_tool(InvalidTool())

class TestTrustManager:
    """Test suite for trust management system."""

    def setup_method(self):
        """Set up test fixtures."""
        self.trust_manager = ZippyTrustManager()
        self.sample_plugin_code = "def test_function(): return 'test'"
        self.sample_metadata = PluginMetadata(
            name="test_plugin",
            description="A test plugin",
            author="test_author",
            version="1.0.0",
            dependencies=[],
            tags=["test"],
            license="MIT"
        )

    async def test_verify_plugin(self):
        """Test plugin verification process."""
        with patch('plugins.trust_manager.hashlib.sha256') as mock_sha256:
            mock_sha256.return_value.hexdigest.return_value = "test_hash"
            
            trust_score = await self.trust_manager.verify_plugin(
                self.sample_plugin_code,
                self.sample_metadata
            )
            
            assert isinstance(trust_score, TrustScore)
            assert trust_score.plugin_id == "test_plugin"
            assert trust_score.verification_status in ["verified", "pending", "flagged"]

    async def test_get_trust_score(self):
        """Test retrieving trust scores."""
        # First verify a plugin to create a trust score
        with patch('plugins.trust_manager.hashlib.sha256') as mock_sha256:
            mock_sha256.return_value.hexdigest.return_value = "test_hash"
            
            await self.trust_manager.verify_plugin(
                self.sample_plugin_code,
                self.sample_metadata
            )
            
            # Now retrieve the trust score
            trust_score = await self.trust_manager.get_trust_score("test_plugin")
            assert trust_score is not None
            assert trust_score.plugin_id == "test_plugin"

    async def test_update_trust_score(self):
        """Test updating trust scores."""
        plugin_id = "test_plugin_id"
        new_score = 0.9

        await self.trust_manager.update_trust_score(plugin_id, new_score, "test update")
        
        # Verify the score was updated
        trust_score = await self.trust_manager.get_trust_score(plugin_id)
        assert trust_score.zippy_trust_score == new_score

    def test_load_verification_rules(self):
        """Test that verification rules are properly loaded."""
        rules = self.trust_manager._load_verification_rules()
        
        assert "code_quality" in rules
        assert "security" in rules
        assert "reputation" in rules
        
        # Check specific rule values
        assert rules["code_quality"]["require_docstrings"] is True
        assert rules["security"]["check_exec"] is True

    async def test_cache_operations(self):
        """Test trust score caching functionality."""
        plugin_id = "cached_plugin"
        initial_score = 0.8
        
        # Set initial score
        await self.trust_manager.update_trust_score(plugin_id, initial_score, "initial score")
        
        # Verify it's cached
        cached_score = await self.trust_manager.get_trust_score(plugin_id)
        assert cached_score.zippy_trust_score == initial_score
        
        # Update score
        new_score = 0.9
        await self.trust_manager.update_trust_score(plugin_id, new_score, "updated score")
        
        # Verify cache was updated
        updated_score = await self.trust_manager.get_trust_score(plugin_id)
        assert updated_score.zippy_trust_score == new_score

class TestMarketplace:
    """Test suite for marketplace functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.marketplace = ZippyCoinMarketplace()
        self.sample_listing_data = {
            "title": "Test Listing",
            "description": "A test listing",
            "content": {"type": "spec_template", "data": "template content"},
            "tags": ["test", "template"],
            "author": "test_author",
            "pricing": {"amount": 100, "currency": "ZIPPY"}
        }

    async def test_create_listing(self):
        """Test creating marketplace listings."""
        listing_id = await self.marketplace.create_listing(self.sample_listing_data)
        
        assert listing_id is not None
        assert listing_id in self.marketplace.listings
        
        listing = self.marketplace.listings[listing_id]
        assert listing.title == "Test Listing"
        assert listing.author == "test_author"
        assert listing.pricing["amount"] == 100

    async def test_get_listing(self):
        """Test retrieving marketplace listings."""
        # Create a listing first
        listing_id = await self.marketplace.create_listing(self.sample_listing_data)
        
        # Retrieve the listing
        listing = await self.marketplace.get_listing(listing_id)
        assert listing is not None
        assert listing.title == "Test Listing"

    async def test_purchase_listing(self):
        """Test purchasing marketplace listings."""
        # Create a listing
        listing_id = await self.marketplace.create_listing(self.sample_listing_data)
        
        # Purchase the listing
        buyer_wallet = "buyer_wallet_123"
        result = await self.marketplace.purchase_listing(
            listing_id, buyer_wallet
        )

        assert result['success'] is True
        transaction_id = result['transaction_id']
        assert transaction_id is not None
        assert transaction_id in self.marketplace.transactions
        
        # Verify transaction details
        transaction = self.marketplace.transactions[transaction_id]
        assert transaction.listing_id == listing_id
        assert transaction.buyer_wallet == buyer_wallet
        assert transaction.status == "completed"

    async def test_listing_validation(self):
        """Test that listing validation works correctly."""
        # Test missing required fields
        invalid_data = {"title": "Test"}  # Missing description, content, etc.
        
        with pytest.raises(ValueError, match="Missing required field"):
            await self.marketplace.create_listing(invalid_data)

    async def test_category_management(self):
        """Test marketplace category functionality."""
        categories = self.marketplace.categories
        
        assert "spec_template" in categories
        assert "ab_test_result" in categories
        assert "milestone_template" in categories
        
        # Test category descriptions
        assert categories["spec_template"] == "Specification Templates"

    async def test_search_listings(self):
        """Test listing search functionality."""
        # Create multiple listings
        await self.marketplace.create_listing({
            **self.sample_listing_data,
            "title": "Python Template",
            "tags": ["python", "template"]
        })
        
        await self.marketplace.create_listing({
            **self.sample_listing_data,
            "title": "JavaScript Template",
            "tags": ["javascript", "template"]
        })
        
        # Search by tag
        python_listings = await self.marketplace.search_listings(tags=["python"])
        assert len(python_listings) == 1
        assert python_listings[0].title == "Python Template"

    async def test_rating_system(self):
        """Test marketplace rating system."""
        # Create a listing
        listing_id = await self.marketplace.create_listing(self.sample_listing_data)
        
        # Add a review
        reviewer_wallet = "reviewer_wallet_123"
        rating = 5.0
        review_text = "Great template!"

        await self.marketplace.add_review(listing_id, reviewer_wallet, rating, review_text)
        
        # Verify rating was updated
        listing = await self.marketplace.get_listing(listing_id)
        assert listing.rating == 5.0
        assert len(listing.reviews) == 1

    async def test_transaction_history(self):
        """Test transaction history tracking."""
        # Create and purchase a listing
        listing_id = await self.marketplace.create_listing(self.sample_listing_data)
        transaction_id = await self.marketplace.purchase_listing(
            listing_id, "buyer_123"
        )
        
        # Get transaction history (using get_user_purchases method)
        history = await self.marketplace.get_user_purchases("buyer_123")
        assert len(history) == 1
        assert history[0].transaction_id == transaction_id

    async def test_marketplace_statistics(self):
        """Test marketplace statistics and analytics."""
        # Create some listings and transactions
        listing_id = await self.marketplace.create_listing(self.sample_listing_data)
        result = await self.marketplace.purchase_listing(listing_id, "buyer_123")
        transaction_id = result['transaction_id']
        
        # Get marketplace stats
        stats = await self.marketplace.get_marketplace_stats()
        
        assert "total_listings" in stats
        assert "total_transactions" in stats
        assert "total_volume" in stats
        assert stats["total_listings"] == 1
        assert stats["total_transactions"] == 1
