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

RANK_MULTIPLIER = {
    "bronze": 0.9,
    "silver": 0.95,
    "gold": 1.0,
    "platinum": 1.05,
    "diamond": 1.1,
    "master": 1.15,
    "grandmaster": 1.2,
    "champion": 1.25
}

HERO_POWER = {
    1: 1.06, 2: 0.90, 3: 0.92, 4: 0.94, 5: 0.96, 6: 0.98, 7: 1.00, 8: 1.02, 9: 1.04, 10: 1.06,
    11: 0.90, 12: 0.92, 13: 0.94, 14: 0.96, 15: 0.98, 16: 1.00, 17: 1.02, 18: 1.04, 19: 1.06, 20: 1.08,
    21: 0.92, 22: 0.94, 23: 0.96, 24: 0.98, 25: 1.00, 26: 1.02, 27: 1.04, 28: 1.06, 29: 1.08, 30: 1.10,
    31: 0.94, 32: 0.96, 33: 0.98, 34: 1.00, 35: 1.02, 36: 1.04, 37: 1.06, 38: 1.08, 39: 1.12    
}

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

def get_random_players_for_roles(all_used_ids):
    players = []
    for role in ROLE_COMPOSITION:
        cur.execute(
            "SELECT id, rank FROM players WHERE id NOT IN %s ORDER BY random() LIMIT 1;",
            (tuple(all_used_ids) if all_used_ids else (0,),)
        )
        row = cur.fetchone()
        if row:
            pid, rank = row
            all_used_ids.add(pid)
            players.append((pid, role, rank))
    return players

def get_random_hero_for_team(role, used_hero_ids):
    cur.execute(
        "SELECT id FROM heroes WHERE role = %s AND id NOT IN %s ORDER BY random() LIMIT 1;",
        (role, tuple(used_hero_ids) if used_hero_ids else (0,))
    )
    row = cur.fetchone()
    if row:
        used_hero_ids.add(row[0])
        return row[0]
    return None

def get_random_map():
    cur.execute("SELECT name, mode FROM maps ORDER BY random() LIMIT 1;")
    return cur.fetchone()

def generate_match_stats(role, hero_power=1.0, rank_mult=1.0):
    if role == "tank":
        base_kills = 15
        base_assists = 10
        base_deaths = 12
        base_damage = 12000
        base_healing = 200
        base_accuracy = 40
    elif role == "damage":
        base_kills = 20
        base_assists = 5
        base_deaths = 12
        base_damage = 13000
        base_healing = 100
        base_accuracy = 60
    elif role == "support":
        base_kills = 8
        base_assists = 12
        base_deaths = 7
        base_damage = 5000
        base_healing = 10000
        base_accuracy = 50

    kills = max(0, int(np.random.normal(base_kills * hero_power * rank_mult, 3)))
    assists = max(0, int(np.random.normal(base_assists * hero_power * rank_mult, 2)))
    deaths = max(0, int(np.random.normal(base_deaths / (hero_power * rank_mult), 3)))
    damage = max(0, int(np.random.normal(base_damage * hero_power * rank_mult, base_damage * 0.1)))
    healing = max(0, int(np.random.normal(base_healing * hero_power * rank_mult, base_healing * 0.1)))
    accuracy = float(np.clip(np.random.normal(base_accuracy * hero_power * rank_mult, 10), 0, 100))

    return kills, assists, deaths, damage, healing, accuracy

def calculate_team_power_with_rank(team, heroes_by_role):
    power = 0
    hero_index = {role: 0 for role in heroes_by_role}
    for pid, role, rank in team:
        hero_id = heroes_by_role[role][hero_index[role]]
        hero_index[role] += 1
        hero_power_value = HERO_POWER.get(hero_id, 1.0)
        rank_mult = RANK_MULTIPLIER.get(rank, 1.0)
        power += hero_power_value * 100 + rank_mult * 10
    return power

def choose_winner(team1_power, team2_power):
    diff = team1_power - team2_power
    return random.random() < (1 / (1 + np.exp(-diff / 50)))

def generate_match():
    map_name, mode = get_random_map()
    started_at = datetime.now(timezone.utc)
    ended_at = started_at + timedelta(minutes=random.randint(6, 30))
    cur.execute(
        "INSERT INTO matches (started_at, ended_at, map, mode) VALUES (%s,%s,%s,%s) RETURNING id;",
        (started_at, ended_at, map_name, mode)
    )
    match_id = cur.fetchone()[0]

    used_player_ids = set()
    team1 = get_random_players_for_roles(used_player_ids)
    team2 = get_random_players_for_roles(used_player_ids)

    heroes_by_role_team1 = {role: [] for role in ROLE_COMPOSITION}
    heroes_by_role_team2 = {role: [] for role in ROLE_COMPOSITION}

    for role in ROLE_COMPOSITION:
        heroes_by_role_team1[role].append(get_random_hero_for_team(role, set()))
        heroes_by_role_team2[role].append(get_random_hero_for_team(role, set()))

    team1_power = calculate_team_power_with_rank(team1, heroes_by_role_team1)
    team2_power = calculate_team_power_with_rank(team2, heroes_by_role_team2)

    if choose_winner(team1_power, team2_power):
        winner_team, loser_team = team1, team2
        winner_heroes, loser_heroes = heroes_by_role_team1, heroes_by_role_team2
        result_winner, result_loser = 'victory', 'defeat'
    else:
        winner_team, loser_team = team2, team1
        winner_heroes, loser_heroes = heroes_by_role_team2, heroes_by_role_team1
        result_winner, result_loser = 'victory', 'defeat'

    for team, heroes_by_role, result in [(winner_team, winner_heroes, result_winner),
                                         (loser_team, loser_heroes, result_loser)]:
        hero_index = {role: 0 for role in heroes_by_role}
        for pid, role, rank in team:
            hero_id = heroes_by_role[role][hero_index[role]]
            hero_index[role] += 1
            hero_power_value = HERO_POWER.get(hero_id, 1.0)
            rank_mult = RANK_MULTIPLIER.get(rank, 1.0)
            kills, assists, deaths, damage, healing, accuracy = generate_match_stats(
                role, hero_power=hero_power_value, rank_mult=rank_mult
            )
            cur.execute(
                """INSERT INTO match_players 
                (match_id, player_id, result, rank, role, hero_id, kills, assists, deaths, damage, healing, accuracy)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s);""",
                (match_id, pid, result, rank, role, hero_id, kills, assists, deaths, damage, healing, accuracy)
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
