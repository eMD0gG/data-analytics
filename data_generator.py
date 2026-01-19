import time
import random
import psycopg2
import os
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

DB_CONFIG = {
    "host": "postgres",
    "port": os.getenv("DB_PORT", 5432),
    "dbname": os.getenv("DB_NAME", "overwatch"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
}

if not DB_CONFIG["user"] or not DB_CONFIG["password"]:
    raise RuntimeError("DB_USER or DB_PASSWORD not set in environment")

ROLE_COMPOSITION = ["damage", "damage", "support", "support", "tank"]

RANKS = ["bronze", "silver", "gold", "platinum", "diamond", "master", "grandmaster", "champion"]

MAPS_MODES = {
    "Ilios": "Control",
    "King's Row": "Hybrid",
    "Havana": "Escort",
    "Busan": "Control",
    "Colosseo": "Push"
}

def random_stats(role):
    if role == "damage":
        return {
            "kills": random.randint(15, 40),
            "assists": random.randint(5, 15),
            "deaths": random.randint(5, 15),
            "damage": random.randint(8000, 20000),
            "healing": random.randint(0, 500),
            "accuracy": round(random.uniform(25, 55), 2),
        }
    if role == "tank":
        return {
            "kills": random.randint(5, 20),
            "assists": random.randint(10, 30),
            "deaths": random.randint(5, 15),
            "damage": random.randint(10000, 25000),
            "healing": random.randint(0, 1000),
            "accuracy": round(random.uniform(15, 40), 2),
        }

    return {
        "kills": random.randint(3, 15),
        "assists": random.randint(20, 45),
        "deaths": random.randint(3, 12),
        "damage": random.randint(2000, 8000),
        "healing": random.randint(8000, 20000),
        "accuracy": round(random.uniform(20, 45), 2),
    }

def connect():
    return psycopg2.connect(**DB_CONFIG)

def get_random_player(cur, used_players):
    cur.execute(
        "SELECT id FROM players WHERE id NOT IN %s ORDER BY random() LIMIT 1;",
        (tuple(used_players) if used_players else (0,),)
    )
    row = cur.fetchone()
    if row:
        return row[0]
    nickname = f"Player{random.randint(1000,9999)}"
    cur.execute("INSERT INTO players (nickname) VALUES (%s) RETURNING id;", (nickname,))
    return cur.fetchone()[0]

def get_random_hero(cur):
    cur.execute("SELECT id FROM heroes ORDER BY random() LIMIT 1;")
    return cur.fetchone()[0]

def create_match(cur):
    map_name, mode = random.choice(list(MAPS_MODES.items()))
    cur.execute(
        "INSERT INTO matches (started_at, map, mode) VALUES (%s, %s, %s) RETURNING id;",
        (datetime.utcnow(), map_name, mode)
    )
    return cur.fetchone()[0]

def insert_match_player(cur, match_id, player_id, role):
    hero_id = get_random_hero(cur)
    stats = random_stats(role)
    cur.execute(
        """
        INSERT INTO match_players (
            match_id, player_id,
            result, rank,
            role, hero_id,
            kills, assists, deaths,
            damage, healing, accuracy
        )
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        ON CONFLICT (match_id, player_id) DO NOTHING;
        """,
        (
            match_id,
            player_id,
            random.choice(["win", "loss"]),
            random.choice(RANKS),
            role,
            hero_id,
            stats["kills"],
            stats["assists"],
            stats["deaths"],
            stats["damage"],
            stats["healing"],
            stats["accuracy"]
        )
    )

def main():
    conn = connect()
    conn.autocommit = True
    cur = conn.cursor()

    while True:
        match_id = create_match(cur)
        used_players = []

        for role in ROLE_COMPOSITION:
            player_id = get_random_player(cur, used_players)
            used_players.append(player_id)
            insert_match_player(cur, match_id, player_id, role)

        time.sleep(1)

if __name__ == "__main__":
    main()
