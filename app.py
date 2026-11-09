from datetime import datetime, timedelta
import json
import os
from zoneinfo import ZoneInfo
import pandas as pd
import streamlit as str_lit
from github import Github, GithubException

# --- CONFIGURATION DE LA PAGE ---
str_lit.set_page_config(
    page_title="Pronos SMC - Saison 2026-2027",
    page_icon="logo.png",
    layout="wide",
)

str_lit.markdown(
    """
    <head>
        <link rel="apple-touch-icon" href="icone.png">
        <link rel="icon" type="image/png" href="icone.png">
    </head>
""",
    unsafe_allow_html=True,
)

MOT_DE_PASSE_ADMIN = "yoan"
PARTICIPANTS_INITIAUX = ["Nathéo", "Adri", "Allan", "Jo", "Vincent", "Tony", "Yoan"]

EFFECTIF_SMC = [
    "Anthony Mandréa",
    "Yannis Clémentia",
    "Parfait Mandanda",
    "Nassim Titebah",
    "Diabé Bolumbu",
    "Sacha M'Baka",
    "Dennis Appiah",
    "Nazim Babaï",
    "Hugo Lamouliatte",
    "Josué Kimboma",
    "Freddy Bomo",
    "Gabin Tome",
    "Léo Milliner",
    "Zoumana Bagbema",
    "Mohamed El Idrissi",
    "Samuel Noireau-Dauriat",
    "Fahd El Khoumisti",
    "Ivann Botella",
    "Armand Gnanduillet",
    "Keelyan Portut",
    "Mohamed Hafid",
    "Salim Diakité",
    "Autre",
]

FICHIER_JSON = "donnees_pronos.json"

# --- CONNEXION GITHUB POUR LA PERSISTANCE ---


def get_github_repo():
    try:
        if "GITHUB_TOKEN" in str_lit.secrets:
            token = str_lit.secrets["GITHUB_TOKEN"]
            g = Github(token)
            repo_name = str_lit.secrets.get("GITHUB_REPO", "")
            if repo_name:
                return g.get_repo(repo_name)
        return None
    except Exception:
        return None


def charger_donnees_depuis_github():
    df_matchs = pd.DataFrame(
        columns=[
            "ID Match",
            "Adversaire",
            "Date",
            "Heure",
            "Résultat",
            "Score Réel",
            "Buteurs",
        ]
    )
    df_pronos = pd.DataFrame(
        columns=[
            "Participant",
            "Match",
            "Prono (1N2)",
            "Score",
            "Buteur",
            "Doublé ?",
            "Points",
        ]
    )
    df_bonus = pd.DataFrame(columns=["Participant", "Points Bonus"])
    passwords_dict = {}

    data = None
    repo = get_github_repo()
    if repo:
        try:
            file_content = repo.get_contents(FICHIER_JSON)
            data = json.loads(file_content.decoded_content.decode("utf-8"))
        except Exception:
            pass

    if data is None and os.path.exists(FICHIER_JSON):
        try:
            with open(FICHIER_JSON, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception:
            pass

    if data:
        if "matchs" in data and data["matchs"]:
            df_matchs = pd.DataFrame(data["matchs"])
        if "pronos" in data and data["pronos"]:
            df_pronos = pd.DataFrame(data["pronos"])
        if "bonus" in data and data["bonus"]:
            df_bonus = pd.DataFrame(data["bonus"])
        if "passwords" in data and data["passwords"]:
            passwords_dict = data["passwords"]

    for col in [
        "ID Match",
        "Adversaire",
        "Date",
        "Heure",
        "Résultat",
        "Score Réel",
        "Buteurs",
    ]:
        if col not in df_matchs.columns:
            df_matchs[col] = ""

    for col in [
        "Participant",
        "Match",
        "Prono (1N2)",
        "Score",
        "Buteur",
        "Doublé ?",
        "Points",
    ]:
        if col not in df_pronos.columns:
            df_pronos[col] = ""

    for col in ["Participant", "Points Bonus"]:
        if col not in df_bonus.columns:
            df_bonus[col] = ""

    return df_matchs, df_pronos, df_bonus, passwords_dict


def sauvegarder_donnees():
    data = {
        "matchs": str_lit.session_state.matchs.to_dict(orient="records"),
        "pronos": str_lit.session_state.pronos.to_dict(orient="records"),
        "bonus": str_lit.session_state.bonus.to_dict(orient="records"),
        "passwords": str_lit.session_state.passwords,
    }
    json_string = json.dumps(data, ensure_ascii=False, indent=4)

    with open(FICHIER_JSON, "w", encoding="utf-8") as f:
        f.write(json_string)

    repo = get_github_repo()
    if repo:
        try:
            file = repo.get_contents(FICHIER_JSON)
            repo.update_file(
                FICHIER_JSON,
                "Mise à jour automatique des pronos",
                json_string,
                file.sha,
            )
        except GithubException:
            try:
                repo.create_file(
                    FICHIER_JSON,
                    "Création du fichier de données des pronos",
                    json_string,
                )
            except Exception:
                pass


# --- INITIALISATION DE LA SESSION STATE SÉCURISÉE ---
if "donnees_chargees" not in str_lit.session_state or not str_lit.session_state.donnees_chargees:
    m, p, b, pw = charger_donnees_depuis_github()
    str_lit.session_state.matchs = m
    str_lit.session_state.pronos = p
    str_lit.session_state.bonus = b
    str_lit.session_state.passwords = pw
    str_lit.session
