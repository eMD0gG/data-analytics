import psycopg2
from faker import Faker
from datetime import datetime, timezone, timedelta
import random
import numpy as np
import time
import os

faker = Faker()

ROLE_COMPOSITION = ["tank", "damage", "damage", "support", "support"]
RANKS = ["bronze", "silver", "gold", "platinum", "diamond", "master", "grandmaster", "champion"]

RANK_MEAN = 2.5
RANK_STD = 1.5

NUM_PLAYERS = 10000

conn = psycopg2.connect(
    host="postgres",
    port=os.getenv("DB_PORT"),
    dbname=os.getenv("DB_NAME"),
    user=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD")
)
cur = conn.cursor()


def sample_rank():
    idx = int(np.clip(np.random.normal(RANK_MEAN, RANK_STD), 0, len(RANKS)-1))
    return RANKS[idx]


def generate_players():
    cur.execute("SELECT COUNT(*) FROM players;")
    if cur.fetchone()[0] > 0:
        return

    for _ in range(NUM_PLAYERS):
        nickname = faker.unique.user_name()
        email = faker.unique.email()
        phone = faker.unique.phone_number()
        rank = sample_rank()
        cur.execute(
            "INSERT INTO players (nickname, email, phone, rank) VALUES (%s,%s,%s,%s);",
            (nickname, email, phone, rank)
        )
    conn.commit()


def get_random_players_for_roles():
    players = []
    used_ids = set()
    for role in ROLE_COMPOSITION:
        cur.execute(
            "SELECT id, rank FROM players WHERE id NOT IN %s ORDER BY random() LIMIT 1;",
            (tuple(used_ids) if used_ids else (0,),)
        )
        row = cur.fetchone()
        if row:
            pid, rank = row
            used_ids.add(pid)
            players.append((pid, role, rank))
    return players


def get_random_map():
    cur.execute("SELECT name, mode FROM maps ORDER BY random() LIMIT 1;")
    return cur.fetchone()


def generate_match_stats(role):
    if role == "tank":
        kills = max(0, int(np.random.normal(15, 5)))
        assists = max(0, int(np.random.normal(10, 3)))
        deaths = max(0, int(np.random.normal(12, 4)))
        damage = max(0, int(np.random.normal(12000, 3000)))
        healing = max(0, int(np.random.normal(200, 100)))
        accuracy = float(np.clip(np.random.normal(40, 10), 0, 100))
    elif role == "damage":
        kills = max(0, int(np.random.normal(20, 5)))
        assists = max(0, int(np.random.normal(5, 3)))
        deaths = max(0, int(np.random.normal(12, 4)))
        damage = max(0, int(np.random.normal(13000, 3500)))
        healing = max(0, int(np.random.normal(100, 50)))
        accuracy = float(np.clip(np.random.normal(60, 15), 0, 100))
    elif role == "support":
        kills = max(0, int(np.random.normal(8, 3)))
        assists = max(0, int(np.random.normal(12, 4)))
        deaths = max(0, int(np.random.normal(7, 3)))
        damage = max(0, int(np.random.normal(5000, 1500)))
        healing = max(0, int(np.random.normal(10000, 2000)))
        accuracy = float(np.clip(np.random.normal(50, 10), 0, 100))
    return kills, assists, deaths, damage, healing, accuracy

def get_random_hero(role):
    cur.execute(
        "SELECT id FROM heroes WHERE role = %s ORDER BY random() LIMIT 1;",
        (role,)
    )
    row = cur.fetchone()
    return row[0] if row else None


def generate_match():
    map_name, mode = get_random_map()
    started_at = datetime.now(timezone.utc)
    ended_at = started_at + timedelta(minutes=random.randint(6, 30))
    cur.execute(
        "INSERT INTO matches (started_at, ended_at, map, mode) VALUES (%s,%s,%s,%s) RETURNING id;",
        (started_at, ended_at, map_name, mode)
    )
    match_id = cur.fetchone()[0]

    team1 = get_random_players_for_roles()
    team2 = get_random_players_for_roles()

    if random.random() < 0.01:
        results = ['draw'] * 10
        for team in [team1, team2]:
            for pid, role, rank in team:
                kills, assists, deaths, damage, healing, accuracy = generate_match_stats(role)
                hero_id = get_random_hero(role)
                cur.execute(
                    """INSERT INTO match_players 
                    (match_id, player_id, result, rank, role, hero_id, kills, assists, deaths, damage, healing, accuracy)
                    VALUES (%s,%s,'draw',%s,%s,%s,%s,%s,%s,%s,%s,%s);""",
                    (match_id, pid, rank, role, hero_id, kills, assists, deaths, damage, healing, accuracy)
                )
    else:
        winner_team = random.choice([team1, team2])
        loser_team = team1 if winner_team is team2 else team2

        for pid, role, rank in winner_team:
            kills, assists, deaths, damage, healing, accuracy = generate_match_stats(role)
            hero_id = get_random_hero(role)
            cur.execute(
                """INSERT INTO match_players 
                (match_id, player_id, result, rank, role, hero_id, kills, assists, deaths, damage, healing, accuracy)
                VALUES (%s,%s,'victory',%s,%s,%s,%s,%s,%s,%s,%s,%s);""",
                (match_id, pid, rank, role, hero_id, kills, assists, deaths, damage, healing, accuracy)
            )

        for pid, role, rank in loser_team:
            kills, assists, deaths, damage, healing, accuracy = generate_match_stats(role)
            hero_id = get_random_hero(role)
            cur.execute(
                """INSERT INTO match_players 
                (match_id, player_id, result, rank, role, hero_id, kills, assists, deaths, damage, healing, accuracy)
                VALUES (%s,%s,'defeat',%s,%s,%s,%s,%s,%s,%s,%s,%s);""",
                (match_id, pid, rank, role, hero_id, kills, assists, deaths, damage, healing, accuracy)
            )

    conn.commit()


def main():
    generate_players()
    try:
        while True:
            generate_match()
            time.sleep(1)
    except KeyboardInterrupt:
        pass

if __name__ == "__main__":
    main()
