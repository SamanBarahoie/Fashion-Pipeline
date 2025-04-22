CREATE TABLE fashion_comments (
    id SERIAL PRIMARY KEY,
    comment TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE sentiment_analysis (
    id SERIAL PRIMARY KEY,
    comment_id INTEGER REFERENCES fashion_comments(id),
    sentiment VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);