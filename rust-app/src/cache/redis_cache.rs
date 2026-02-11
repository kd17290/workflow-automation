//! Centralized Redis cache service for workflow automation.
//!
//! Provides async Redis operations with TTL-based caching
//! for frequently-read data like workflow definitions.

use redis::AsyncCommands;
use tracing::warn;

/// Redis cache client wrapper.
pub struct RedisCache {
    client: redis::Client,
}

impl RedisCache {
    /// Create a new RedisCache from a Redis URL (e.g., "redis://redis:6379").
    pub fn new(redis_url: &str) -> Result<Self, redis::RedisError> {
        let client = redis::Client::open(redis_url)?;
        Ok(Self { client })
    }

    /// Get a value from the cache.
    ///
    /// Returns None if the key doesn't exist or on error (fail-open).
    pub async fn get(&self, key: &str) -> Option<String> {
        match self.client.get_multiplexed_async_connection().await {
            Ok(mut conn) => match conn.get::<_, Option<String>>(key).await {
                Ok(val) => val,
                Err(e) => {
                    warn!("Redis cache_get error for key={}: {}", key, e);
                    None
                }
            },
            Err(e) => {
                warn!("Redis connection error in cache_get: {}", e);
                None
            }
        }
    }

    /// Set a value in the cache with a TTL in seconds.
    pub async fn set(&self, key: &str, value: &str, ttl_seconds: u64) {
        match self.client.get_multiplexed_async_connection().await {
            Ok(mut conn) => {
                let result: Result<(), _> = conn.set_ex(key, value, ttl_seconds).await;
                if let Err(e) = result {
                    warn!("Redis cache_set error for key={}: {}", key, e);
                }
            }
            Err(e) => {
                warn!("Redis connection error in cache_set: {}", e);
            }
        }
    }

    /// Delete a key from the cache.
    pub async fn delete(&self, key: &str) {
        match self.client.get_multiplexed_async_connection().await {
            Ok(mut conn) => {
                let result: Result<(), _> = conn.del(key).await;
                if let Err(e) = result {
                    warn!("Redis cache_delete error for key={}: {}", key, e);
                }
            }
            Err(e) => {
                warn!("Redis connection error in cache_delete: {}", e);
            }
        }
    }
}
