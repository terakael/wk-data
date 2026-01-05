-- WaniKani Database Schema
-- PostgreSQL implementation

-- Radicals table
CREATE TABLE radicals (
    id SERIAL PRIMARY KEY,
    character VARCHAR(100), -- Can be NULL for image-only radicals
    character_image VARCHAR(512), -- For radicals that are images instead of characters
    meaning VARCHAR(255) NOT NULL UNIQUE,
    mnemonic TEXT,
    mnemonic_image VARCHAR(512),
    url VARCHAR(512),
    level INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Kanji table
CREATE TABLE kanji (
    id SERIAL PRIMARY KEY,
    character VARCHAR(20) NOT NULL UNIQUE,
    meaning VARCHAR(255) NOT NULL,
    url VARCHAR(512),
    level INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Kanji readings table
CREATE TABLE kanji_readings (
    id SERIAL PRIMARY KEY,
    kanji_id INTEGER REFERENCES kanji(id) ON DELETE CASCADE,
    reading_type VARCHAR(20) NOT NULL CHECK (reading_type IN ('on', 'kun', 'nanori')),
    reading_text VARCHAR(100) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Kanji mnemonics table
CREATE TABLE kanji_mnemonics (
    id SERIAL PRIMARY KEY,
    kanji_id INTEGER REFERENCES kanji(id) ON DELETE CASCADE,
    mnemonic_type VARCHAR(20) NOT NULL CHECK (mnemonic_type IN ('meaning', 'reading')),
    content TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Junction table for kanji-radicals relationship
CREATE TABLE kanji_radicals (
    kanji_id INTEGER REFERENCES kanji(id) ON DELETE CASCADE,
    radical_id INTEGER REFERENCES radicals(id) ON DELETE CASCADE,
    PRIMARY KEY (kanji_id, radical_id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Vocabulary table
CREATE TABLE vocabulary (
    id SERIAL PRIMARY KEY,
    character VARCHAR(50) NOT NULL UNIQUE,
    primary_meaning VARCHAR(255) NOT NULL,
    reading VARCHAR(255) NOT NULL,
    url VARCHAR(512),
    level INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Vocabulary alternative meanings table
CREATE TABLE vocabulary_alternative_meanings (
    id SERIAL PRIMARY KEY,
    vocab_id INTEGER REFERENCES vocabulary(id) ON DELETE CASCADE,
    meaning_text VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Vocabulary explanations table
CREATE TABLE vocab_explanations (
    id SERIAL PRIMARY KEY,
    vocab_id INTEGER REFERENCES vocabulary(id) ON DELETE CASCADE,
    explanation_type VARCHAR(20) NOT NULL CHECK (explanation_type IN ('meaning', 'reading')),
    content TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Junction table for vocabulary-kanji composition
CREATE TABLE vocab_kanji_composition (
    vocab_id INTEGER REFERENCES vocabulary(id) ON DELETE CASCADE,
    kanji_id INTEGER REFERENCES kanji(id) ON DELETE CASCADE,
    PRIMARY KEY (vocab_id, kanji_id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Basic indexes for common lookups
CREATE INDEX idx_kanji_character ON kanji(character);
CREATE INDEX idx_radicals_character ON radicals(character);
CREATE INDEX idx_radicals_meaning ON radicals(meaning);
CREATE INDEX idx_vocabulary_character ON vocabulary(character);
CREATE INDEX idx_kanji_level ON kanji(level);
CREATE INDEX idx_radicals_level ON radicals(level);
CREATE INDEX idx_vocabulary_level ON vocabulary(level);