"""
ZippyCoin Marketplace for Development Assets

This module implements a marketplace system for trading spec templates,
A/B test results, and other development assets using ZippyCoin.
"""

import asyncio
import json
import uuid
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

@dataclass
class MarketplaceListing:
    """Marketplace listing for development assets."""
    listing_id: str
    title: str
    description: str
    content: Dict[str, Any]
    tags: List[str]
    author: str
    author_wallet: str
    pricing: Dict[str, Any]
    trust_score: float
    category: str  # 'spec_template', 'ab_test_result', 'milestone_template'
    created_at: str
    updated_at: str
    purchase_count: int
    rating: float
    reviews: List[Dict[str, Any]]

@dataclass
class PurchaseTransaction:
    """Purchase transaction record."""
    transaction_id: str
    listing_id: str
    buyer_wallet: str
    seller_wallet: str
    amount: float
    currency: str
    status: str  # 'pending', 'completed', 'failed'
    created_at: str
    completed_at: Optional[str]

class ZippyCoinMarketplace:
    """
    ZippyCoin marketplace for development assets.
    """
    
    def __init__(self):
        self.listings: Dict[str, MarketplaceListing] = {}
        self.transactions: Dict[str, PurchaseTransaction] = {}
        self.categories = {
            'spec_template': 'Specification Templates',
            'ab_test_result': 'A/B Test Results',
            'milestone_template': 'Milestone Templates',
            'prompt_template': 'Prompt Templates',
            'workflow_template': 'Workflow Templates'
        }
    
    async def create_listing(self, listing_data: Dict[str, Any]) -> str:
        """
        Create a new marketplace listing.
        
        Args:
            listing_data: Listing data including title, description, content, etc.
            
        Returns:
            Listing ID
        """
        try:
            listing_id = str(uuid.uuid4())
            
            # Validate required fields
            required_fields = ['title', 'description', 'content', 'tags', 'author', 'pricing']
            for field in required_fields:
                if field not in listing_data:
                    raise ValueError(f"Missing required field: {field}")
            
            # Create listing
            listing = MarketplaceListing(
                listing_id=listing_id,
                title=listing_data['title'],
                description=listing_data['description'],
                content=listing_data['content'],
                tags=listing_data['tags'],
                author=listing_data['author'],
                author_wallet=listing_data.get('author_wallet', 'unknown'),
                pricing=listing_data['pricing'],
                trust_score=listing_data.get('trust_score', 0.5),
                category=listing_data.get('category', 'spec_template'),
                created_at=datetime.now().isoformat(),
                updated_at=datetime.now().isoformat(),
                purchase_count=0,
                rating=0.0,
                reviews=[]
            )
            
            # Store listing
            self.listings[listing_id] = listing
            
            logger.info(f"Created marketplace listing: {listing_id} - {listing.title}")
            
            return listing_id
            
        except Exception as e:
            logger.error(f"Failed to create listing: {e}")
            raise
    
    async def get_listing(self, listing_id: str) -> Optional[MarketplaceListing]:
        """Get a marketplace listing by ID."""
        return self.listings.get(listing_id)
    
    async def search_listings(self, query: str = None, category: str = None,
                            tags: List[str] = None, min_trust_score: float = 0.0,
                            max_price: float = None) -> List[MarketplaceListing]:
        """
        Search marketplace listings.
        
        Args:
            query: Search query
            category: Filter by category
            tags: Filter by tags
            min_trust_score: Minimum trust score
            max_price: Maximum price
            
        Returns:
            List of matching listings
        """
        results = []
        
        for listing in self.listings.values():
            # Apply filters
            if category and listing.category != category:
                continue
                
            if min_trust_score and listing.trust_score < min_trust_score:
                continue
                
            if max_price and listing.pricing.get('amount', 0) > max_price:
                continue
                
            if tags and not any(tag in listing.tags for tag in tags):
                continue
                
            if query:
                # Simple text search
                search_text = f"{listing.title} {listing.description} {' '.join(listing.tags)}".lower()
                if query.lower() not in search_text:
                    continue
            
            results.append(listing)
        
        # Sort by trust score and rating
        results.sort(key=lambda x: (x.trust_score, x.rating), reverse=True)
        
        return results
    
    async def purchase_listing(self, listing_id: str, buyer_wallet: str) -> Dict[str, Any]:
        """
        Purchase a marketplace listing.
        
        Args:
            listing_id: ID of the listing to purchase
            buyer_wallet: Buyer's wallet address
            
        Returns:
            Purchase result
        """
        try:
            listing = self.listings.get(listing_id)
            if not listing:
                return {
                    'success': False,
                    'error': 'Listing not found'
                }
            
            # Create transaction
            transaction_id = str(uuid.uuid4())
            transaction = PurchaseTransaction(
                transaction_id=transaction_id,
                listing_id=listing_id,
                buyer_wallet=buyer_wallet,
                seller_wallet=listing.author_wallet,
                amount=listing.pricing['amount'],
                currency=listing.pricing['currency'],
                status='pending',
                created_at=datetime.now().isoformat(),
                completed_at=None
            )
            
            # Simulate payment processing
            await asyncio.sleep(0.1)  # Simulate processing time
            
            # Complete transaction
            transaction.status = 'completed'
            transaction.completed_at = datetime.now().isoformat()
            
            # Update listing
            listing.purchase_count += 1
            listing.updated_at = datetime.now().isoformat()
            
            # Store transaction
            self.transactions[transaction_id] = transaction
            
            logger.info(f"Completed purchase: {transaction_id} - {listing.title}")
            
            return {
                'success': True,
                'transaction_id': transaction_id,
                'listing': asdict(listing),
                'transaction': asdict(transaction)
            }
            
        except Exception as e:
            logger.error(f"Failed to purchase listing: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def add_review(self, listing_id: str, reviewer_wallet: str, 
                        rating: float, review_text: str) -> Dict[str, Any]:
        """
        Add a review to a marketplace listing.
        
        Args:
            listing_id: ID of the listing
            reviewer_wallet: Reviewer's wallet address
            rating: Rating (1-5)
            review_text: Review text
            
        Returns:
            Review result
        """
        try:
            listing = self.listings.get(listing_id)
            if not listing:
                return {
                    'success': False,
                    'error': 'Listing not found'
                }
            
            # Validate rating
            if not 1 <= rating <= 5:
                return {
                    'success': False,
                    'error': 'Rating must be between 1 and 5'
                }
            
            # Check if user has purchased the listing
            has_purchased = any(
                t.buyer_wallet == reviewer_wallet and t.status == 'completed'
                for t in self.transactions.values()
                if t.listing_id == listing_id
            )
            
            if not has_purchased:
                return {
                    'success': False,
                    'error': 'Must purchase listing before reviewing'
                }
            
            # Add review
            review = {
                'reviewer_wallet': reviewer_wallet,
                'rating': rating,
                'review_text': review_text,
                'created_at': datetime.now().isoformat()
            }
            
            listing.reviews.append(review)
            
            # Update average rating
            total_rating = sum(r['rating'] for r in listing.reviews)
            listing.rating = total_rating / len(listing.reviews)
            listing.updated_at = datetime.now().isoformat()
            
            logger.info(f"Added review to listing {listing_id}: {rating}/5")
            
            return {
                'success': True,
                'review': review,
                'new_average_rating': listing.rating
            }
            
        except Exception as e:
            logger.error(f"Failed to add review: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def update_listing(self, listing_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update a marketplace listing.
        
        Args:
            listing_id: ID of the listing to update
            updates: Fields to update
            
        Returns:
            Update result
        """
        try:
            listing = self.listings.get(listing_id)
            if not listing:
                return {
                    'success': False,
                    'error': 'Listing not found'
                }
            
            # Update allowed fields
            allowed_fields = ['title', 'description', 'content', 'tags', 'pricing']
            for field, value in updates.items():
                if field in allowed_fields:
                    setattr(listing, field, value)
            
            listing.updated_at = datetime.now().isoformat()
            
            logger.info(f"Updated listing: {listing_id}")
            
            return {
                'success': True,
                'listing': asdict(listing)
            }
            
        except Exception as e:
            logger.error(f"Failed to update listing: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def delete_listing(self, listing_id: str, author_wallet: str) -> Dict[str, Any]:
        """
        Delete a marketplace listing.
        
        Args:
            listing_id: ID of the listing to delete
            author_wallet: Author's wallet address for verification
            
        Returns:
            Delete result
        """
        try:
            listing = self.listings.get(listing_id)
            if not listing:
                return {
                    'success': False,
                    'error': 'Listing not found'
                }
            
            if listing.author_wallet != author_wallet:
                return {
                    'success': False,
                    'error': 'Unauthorized to delete this listing'
                }
            
            # Remove listing
            del self.listings[listing_id]
            
            logger.info(f"Deleted listing: {listing_id}")
            
            return {
                'success': True,
                'deleted_listing_id': listing_id
            }
            
        except Exception as e:
            logger.error(f"Failed to delete listing: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def get_marketplace_stats(self) -> Dict[str, Any]:
        """Get marketplace statistics."""
        total_listings = len(self.listings)
        total_transactions = len([t for t in self.transactions.values() if t.status == 'completed'])
        total_volume = sum(t.amount for t in self.transactions.values() if t.status == 'completed')
        
        # Category breakdown
        category_stats = {}
        for listing in self.listings.values():
            if listing.category not in category_stats:
                category_stats[listing.category] = {
                    'count': 0,
                    'total_purchases': 0,
                    'avg_rating': 0.0
                }
            category_stats[listing.category]['count'] += 1
            category_stats[listing.category]['total_purchases'] += listing.purchase_count
        
        # Calculate average ratings
        for category in category_stats:
            category_listings = [l for l in self.listings.values() if l.category == category]
            if category_listings:
                avg_rating = sum(l.rating for l in category_listings) / len(category_listings)
                category_stats[category]['avg_rating'] = round(avg_rating, 2)
        
        return {
            'total_listings': total_listings,
            'total_transactions': total_transactions,
            'total_volume': total_volume,
            'category_stats': category_stats,
            'top_categories': sorted(category_stats.items(), key=lambda x: x[1]['count'], reverse=True)[:5]
        }
    
    async def get_user_listings(self, wallet_address: str) -> List[MarketplaceListing]:
        """Get listings by a specific user."""
        return [
            listing for listing in self.listings.values()
            if listing.author_wallet == wallet_address
        ]
    
    async def get_user_purchases(self, wallet_address: str) -> List[PurchaseTransaction]:
        """Get purchase history for a specific user."""
        return [
            transaction for transaction in self.transactions.values()
            if transaction.buyer_wallet == wallet_address and transaction.status == 'completed'
        ]
    
    async def export_marketplace_data(self, format: str = 'json') -> str:
        """Export marketplace data in specified format."""
        if format == 'json':
            data = {
                'listings': [asdict(listing) for listing in self.listings.values()],
                'transactions': [asdict(transaction) for transaction in self.transactions.values()],
                'exported_at': datetime.now().isoformat()
            }
            return json.dumps(data, indent=2)
        else:
            raise ValueError(f"Unsupported export format: {format}")
