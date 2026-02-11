use async_trait::async_trait;

/// Base trait for all storage backends (Dependency Inversion Principle).
///
/// Mirrors Python's BaseStorage ABC from app/storage/base.py.
/// Generic over the item type T. Each storage implementation must provide
/// CRUD + list operations.
#[async_trait]
pub trait Storage<T>: Send + Sync
where
    T: Send + Sync,
{
    /// Retrieve an item by its UUID.
    async fn get(&self, uuid: &str) -> Result<Option<T>, StorageError>;

    /// Create a new item and return its UUID.
    async fn create(&self, item: &mut T) -> Result<String, StorageError>;

    /// Delete an item by its UUID.
    async fn delete(&self, uuid: &str) -> Result<bool, StorageError>;

    /// Update an existing item.
    async fn update(&self, item: &T) -> Result<bool, StorageError>;

    /// List all items in storage.
    async fn list_all(&self) -> Result<Vec<T>, StorageError>;

    /// List items with cursor-based pagination, ordered by uuid.
    ///
    /// Returns (items, next_cursor). next_cursor is None if no more items.
    async fn list_paginated(
        &self,
        limit: i64,
        cursor: Option<&str>,
    ) -> Result<(Vec<T>, Option<String>), StorageError>;
}

/// Storage error type.
#[derive(Debug, thiserror::Error)]
pub enum StorageError {
    #[error("Database error: {0}")]
    Database(String),

    #[error("Serialization error: {0}")]
    Serialization(String),

    #[error("Not found: {0}")]
    NotFound(String),
}

impl From<sqlx::Error> for StorageError {
    fn from(err: sqlx::Error) -> Self {
        StorageError::Database(err.to_string())
    }
}

impl From<serde_json::Error> for StorageError {
    fn from(err: serde_json::Error) -> Self {
        StorageError::Serialization(err.to_string())
    }
}
