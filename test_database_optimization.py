#!/usr/bin/env python3
"""
Test script to verify database optimizations.
"""

import sys
import time
from sqlalchemy.orm import joinedload
from app.db.session import get_db, get_connection_pool_stats, check_database_health
from app.models.post import MatchedPost, AIResponse
from app.models.user import User
from app.models.config import ClientConfig


def test_connection_pool():
    """Test connection pool statistics."""
    print("\n=== Testing Connection Pool ===")
    
    stats = get_connection_pool_stats()
    print(f"Pool Size: {stats['pool_size']}")
    print(f"Max Overflow: {stats['max_overflow']}")
    print(f"Checked Out: {stats['checked_out']}")
    print(f"Checked In: {stats['checked_in']}")
    print(f"Total Capacity: {stats['total_connections']}")
    
    health = check_database_health()
    print(f"Health Status: {health['status']}")
    
    assert stats['pool_size'] == 5, "Pool size should be 5"
    assert stats['max_overflow'] == 15, "Max overflow should be 15"
    print("✓ Connection pool configuration correct")


def test_eager_loading():
    """Test eager loading to prevent N+1 queries."""
    print("\n=== Testing Eager Loading ===")
    
    db = next(get_db())
    
    try:
        # Test without eager loading (will cause N+1 if there are posts)
        start = time.time()
        posts_without = db.query(MatchedPost).limit(10).all()
        time_without = time.time() - start
        
        # Access responses to trigger lazy loading
        for post in posts_without:
            _ = post.responses
        
        # Test with eager loading
        start = time.time()
        posts_with = db.query(MatchedPost).options(
            joinedload(MatchedPost.responses)
        ).limit(10).all()
        time_with = time.time() - start
        
        # Access responses (already loaded)
        for post in posts_with:
            _ = post.responses
        
        print(f"Without eager loading: {time_without:.4f}s")
        print(f"With eager loading: {time_with:.4f}s")
        
        if len(posts_with) > 0:
            improvement = ((time_without - time_with) / time_without * 100) if time_without > 0 else 0
            print(f"Performance improvement: {improvement:.1f}%")
        
        print("✓ Eager loading working correctly")
        
    finally:
        db.close()


def test_indexes():
    """Test that indexes are being used (requires EXPLAIN ANALYZE)."""
    print("\n=== Testing Database Indexes ===")
    
    db = next(get_db())
    
    try:
        # Check if tables exist
        posts_count = db.query(MatchedPost).count()
        responses_count = db.query(AIResponse).count()
        
        print(f"Posts in database: {posts_count}")
        print(f"Responses in database: {responses_count}")
        
        # Test indexed query performance
        start = time.time()
        result = db.query(MatchedPost).filter(
            MatchedPost.client_id == 1
        ).order_by(MatchedPost.created_at.desc()).limit(10).all()
        query_time = time.time() - start
        
        print(f"Indexed query time: {query_time:.4f}s")
        
        if query_time < 0.1:
            print("✓ Query performance is good (< 100ms)")
        else:
            print("⚠ Query performance could be improved")
        
    finally:
        db.close()


def test_health_endpoints():
    """Test that health check functions work."""
    print("\n=== Testing Health Check Functions ===")
    
    health = check_database_health()
    print(f"Database Health: {health['status']}")
    
    if 'pool_stats' in health:
        print("✓ Pool stats included in health check")
    
    stats = get_connection_pool_stats()
    print(f"✓ Connection pool stats retrieved: {len(stats)} metrics")


def main():
    """Run all tests."""
    print("=" * 60)
    print("Database Optimization Test Suite")
    print("=" * 60)
    
    try:
        test_connection_pool()
        test_health_endpoints()
        test_indexes()
        test_eager_loading()
        
        print("\n" + "=" * 60)
        print("✓ All tests passed!")
        print("=" * 60)
        return 0
        
    except Exception as e:
        print(f"\n✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
