CREATE TYPE game_result AS ENUM ('win', 'loss');

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
    created_at TIMESTAMP DEFAULT now()
);

CREATE TABLE matches (
    id BIGSERIAL PRIMARY KEY,
    started_at TIMESTAMP NOT NULL,
    map TEXT,
    mode TEXT
);

CREATE TABLE heroes (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL UNIQUE
);

INSERT INTO heroes (name) VALUES
-- Tanks
('D.Va'), ('Doomfist'), ('Junker Queen'), ('Mauga'),
('Orisa'), ('Ramattra'), ('Reinhardt'), ('Roadhog'),
('Sigma'), ('Winston'), ('Wrecking Ball'), ('Zarya'),

-- Damage
('Ashe'), ('Bastion'), ('Cassidy'), ('Echo'),
('Genji'), ('Hanzo'), ('Junkrat'), ('Mei'),
('Pharah'), ('Reaper'), ('Sojourn'), ('Soldier: 76'),
('Sombra'), ('Symmetra'), ('Torbjörn'),
('Tracer'), ('Widowmaker'),

-- Support
('Ana'), ('Baptiste'), ('Brigitte'), ('Illari'),
('Kiriko'), ('Lifeweaver'), ('Lúcio'),
('Mercy'), ('Moira'), ('Zenyatta');

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
