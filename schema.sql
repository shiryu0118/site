CREATE TABLE IF NOT EXISTS invalid_articles (
    url TEXT PRIMARY KEY,
    tool_name TEXT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
); 