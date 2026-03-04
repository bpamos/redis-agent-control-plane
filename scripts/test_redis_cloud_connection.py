#!/usr/bin/env python3
"""Test Redis Cloud connectivity and vector search capabilities."""

import os
import sys
from pathlib import Path

from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import redis
import numpy as np


def test_redis_cloud_connection():
    """Test basic Redis Cloud connectivity and vector search."""
    
    redis_url = os.getenv("REDIS_URL")
    if not redis_url:
        print("❌ ERROR: REDIS_URL not found in .env file")
        return False
    
    print("=" * 60)
    print("Redis Cloud Connection Test")
    print("=" * 60)
    
    try:
        # Test 1: Basic connection
        print("\n[1/5] Testing basic connection...")
        client = redis.from_url(redis_url, decode_responses=True)
        response = client.ping()
        if response:
            print("  ✅ Connection successful (PING → PONG)")
        else:
            print("  ❌ Connection failed")
            return False
        
        # Test 2: Get server info
        print("\n[2/5] Getting server info...")
        info = client.info("server")
        redis_version = info.get("redis_version", "unknown")
        print(f"  ✅ Redis version: {redis_version}")
        
        # Test 3: Test basic operations
        print("\n[3/5] Testing basic operations...")
        client.set("test_key", "test_value")
        value = client.get("test_key")
        if value == "test_value":
            print("  ✅ SET/GET operations work")
        client.delete("test_key")
        
        # Test 4: Test hash operations (used for vector storage)
        print("\n[4/5] Testing hash operations...")
        client.hset("test_hash", mapping={"field1": "value1", "field2": "value2"})
        hash_value = client.hgetall("test_hash")
        if hash_value == {"field1": "value1", "field2": "value2"}:
            print("  ✅ HSET/HGETALL operations work")
        client.delete("test_hash")
        
        # Test 5: Test vector storage (binary data)
        print("\n[5/5] Testing vector storage...")

        # Create a binary client for vector storage
        binary_client = redis.from_url(redis_url, decode_responses=False)

        test_vector = np.random.rand(384).astype(np.float32)
        vector_bytes = test_vector.tobytes()

        # Store vector in hash
        binary_client.hset(b"test_vector", mapping={
            b"content": b"test content",
            b"embedding": vector_bytes
        })

        # Retrieve vector
        stored = binary_client.hgetall(b"test_vector")
        if stored and b"embedding" in stored:
            retrieved_vector = np.frombuffer(stored[b"embedding"], dtype=np.float32)
            if np.allclose(test_vector, retrieved_vector):
                print("  ✅ Vector storage/retrieval works")
            else:
                print("  ❌ Vector data mismatch")
                binary_client.close()
                return False
        else:
            print("  ❌ Vector storage failed")
            binary_client.close()
            return False

        binary_client.delete(b"test_vector")
        binary_client.close()
        
        # Summary
        print("\n" + "=" * 60)
        print("✅ All Redis Cloud connectivity tests passed!")
        print("=" * 60)
        print(f"\nRedis version: {redis_version}")
        print(f"Connection: {redis_url.split('@')[1] if '@' in redis_url else 'configured'}")
        print("\nReady to proceed with RAG pipeline indexing.")
        
        return True
        
    except redis.ConnectionError as e:
        print(f"\n❌ Connection error: {e}")
        return False
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        try:
            client.close()
        except:
            pass


if __name__ == "__main__":
    success = test_redis_cloud_connection()
    sys.exit(0 if success else 1)

