CREATE TYPE game_result AS ENUM ('victory', 'defeat', 'draw');

CREATE TYPE player_rank AS ENUM (
    'bronze',
    'silver',
    'gold',
    'platinum',
    'diamond',
    'master',
    'grandmaster',
    'champion'
);

CREATE TYPE player_role AS ENUM ('damage', 'support', 'tank');

CREATE TABLE players (
    id BIGSERIAL PRIMARY KEY,
    nickname TEXT NOT NULL UNIQUE,
    email TEXT UNIQUE,
    phone TEXT UNIQUE,
    rank player_rank NOT NULL,
    created_at TIMESTAMP DEFAULT now()
);

CREATE TABLE matches (
    id BIGSERIAL PRIMARY KEY,
    started_at TIMESTAMP NOT NULL,
    ended_at TIMESTAMP,
    map TEXT,
    mode TEXT
);

CREATE TABLE heroes (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    role player_role NOT NULL
);

INSERT INTO heroes (name, role) VALUES
-- Tanks
('D.Va', 'tank'), ('Doomfist', 'tank'), ('Junker Queen', 'tank'), ('Mauga', 'tank'),
('Orisa', 'tank'), ('Ramattra', 'tank'), ('Reinhardt', 'tank'), ('Roadhog', 'tank'),
('Sigma', 'tank'), ('Winston', 'tank'), ('Wrecking Ball', 'tank'), ('Zarya', 'tank'),

-- Damage
('Ashe', 'damage'), ('Bastion', 'damage'), ('Cassidy', 'damage'), ('Echo', 'damage'),
('Genji', 'damage'), ('Hanzo', 'damage'), ('Junkrat', 'damage'), ('Mei', 'damage'),
('Pharah', 'damage'), ('Reaper', 'damage'), ('Sojourn', 'damage'), ('Soldier: 76', 'damage'),
('Sombra', 'damage'), ('Symmetra', 'damage'), ('Torbjörn', 'damage'),
('Tracer', 'damage'), ('Widowmaker', 'damage'),

-- Support
('Ana', 'support'), ('Baptiste', 'support'), ('Brigitte', 'support'), ('Illari', 'support'),
('Kiriko', 'support'), ('Lifeweaver', 'support'), ('Lúcio', 'support'),
('Mercy', 'support'), ('Moira', 'support'), ('Zenyatta', 'support');

CREATE TABLE maps (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    mode TEXT NOT NULL
);

INSERT INTO maps (name, mode) VALUES
('Ilios', 'Control'),
('Lijiang Tower', 'Control'),
('Nepal', 'Control'),
('Busan', 'Control'),
('Havana', 'Escort'),
('Dorado', 'Escort'),
('Route 66', 'Escort'),
('Watchpoint: Gibraltar', 'Escort'),
('King''s Row', 'Hybrid'),
('Numbani', 'Hybrid'),
('Eichenwalde', 'Hybrid'),
('Blizzard World', 'Hybrid'),
('Colosseo', 'Push'),
('New Queen Street', 'Push'),
('Esperança', 'Push');

CREATE TABLE match_players (
    id BIGSERIAL PRIMARY KEY,

    match_id BIGINT NOT NULL
        REFERENCES matches(id) ON DELETE CASCADE,

    player_id BIGINT NOT NULL
        REFERENCES players(id) ON DELETE CASCADE,

    result game_result NOT NULL,
    rank player_rank NOT NULL,

    role player_role NOT NULL,
    hero_id INT NOT NULL
        REFERENCES heroes(id),

    kills INT NOT NULL CHECK (kills >= 0),
    assists INT NOT NULL CHECK (assists >= 0),
    deaths INT NOT NULL CHECK (deaths >= 0),

    damage INT NOT NULL CHECK (damage >= 0),
    healing INT NOT NULL CHECK (healing >= 0),

    accuracy NUMERIC(5,2) CHECK (accuracy BETWEEN 0 AND 100),

    UNIQUE (match_id, player_id)
);

CREATE INDEX idx_match_players_player
    ON match_players(player_id);

CREATE INDEX idx_match_players_match
    ON match_players(match_id);

CREATE INDEX idx_match_players_hero
    ON match_players(hero_id);

CREATE INDEX idx_match_players_rank
    ON match_players(rank);
