from datetime import datetime, timedelta
import json
import os
from zoneinfo import ZoneInfo
import pandas as pd
import streamlit as st
from github import Github, GithubException

st.set_page_config(
    page_title="Pronos SMC - Saison 2026-2027",
    page_icon="logo.png",
    layout="wide",
)

MOT_DE_PASSE_ADMIN = "yoan"
PARTICIPANTS_INITIAUX = ["Nathéo", "Adri", "Allan", "Jo", "Vincent", "Tony", "Yoan"]
EFFECTIF_SMC = [
    "Anthony Mandréa", "Yannis Clémentia", "Parfait Mandanda", "Nassim Titebah",
    "Diabé Bolumbu", "Sacha M'Baka", "Dennis Appiah", "Nazim Babaï",
    "Hugo Lamouliatte", "Josué Kimboma", "Freddy Bomo", "Gabin Tome",
    "Léo Milliner", "Zoumana Bagbema", "Mohamed El Idrissi", "Samuel Noireau-Dauriat",
    "Fahd El Khoumisti", "Ivann Botella", "Armand Gnanduillet", "Keelyan Portut",
    "Mohamed Hafid", "Salim Diakité", "Autre"
]
FICHIER_JSON = "donnees_pronos.json"

def get_github_repo():
    try:
        if "GITHUB_TOKEN" in st.secrets:
            g = Github(st.secrets["GITHUB_TOKEN"])
            repo_name = st.secrets.get("GITHUB_REPO", "")
            if repo_name:
                return g.get_repo(repo_name)
    except Exception:
        pass
    return None

def charger_donnees():
    df_matchs = pd.DataFrame(columns=["ID Match", "Adversaire", "Date", "Heure", "Résultat", "Score Réel", "Buteurs"])
    df_pronos = pd.DataFrame(columns=["Participant", "Match", "Prono (1N2)", "Score", "Buteur", "Doublé ?", "Points"])
    df_bonus = pd.DataFrame(columns=["Participant", "Points Bonus"])
    passwords = {}
    
    data = None
    repo = get_github_repo()
    if repo:
        try:
            content = repo.get_contents(FICHIER_JSON)
            data = json.loads(content.decoded_content.decode("utf-8"))
        except Exception:
            pass
            
    if data is None and os.path.exists(FICHIER_JSON):
        try:
            with open(FICHIER_JSON, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception:
            pass
            
    if data:
        if "matchs" in data and data["matchs"]: df_matchs = pd.DataFrame(data["matchs"])
        if "pronos" in data and data["pronos"]: df_pronos = pd.DataFrame(data["pronos"])
        if "bonus" in data and data["bonus"]: df_bonus = pd.DataFrame(data["bonus"])
        if "passwords" in data and data["passwords"]: passwords = data["passwords"]
        
    return df_matchs, df_pronos, df_bonus, passwords

def sauvegarder_donnees():
    data = {
        "matchs": st.session_state.matchs.to_dict(orient="records"),
        "pronos": st.session_state.pronos.to_dict(orient="records"),
        "bonus": st.session_state.bonus.to_dict(orient="records"),
        "passwords": st.session_state.passwords,
    }
    json_str = json.dumps(data, ensure_ascii=False, indent=4)
    with open(FICHIER_JSON, "w", encoding="utf-8") as f:
        f.write(json_str)
        
    repo = get_github_repo()
    if repo:
        try:
            file = repo.get_contents(FICHIER_JSON)
            repo.update_file(FICHIER_JSON, "Mise à jour pronos", json_str, file.sha)
        except GithubException:
            try:
                repo.create_file(FICHIER_JSON, "Création pronos", json_str)
            except Exception:
                pass

if "init" not in st.session_state:
    m, p, b, pw = charger_donnees()
    st.session_state.matchs = m
    st.session_state.pronos = p
    st.session_state.bonus = b
    st.session_state.passwords = pw
    st.session_state.init = True

def calculer_points():
    if st.session_state.pronos.empty or st.session_state.matchs.empty:
        return
    for idx, row_p in st.session_state.pronos.iterrows():
        m_id = str(row_p["Match"]).strip()
        match_info = st.session_state.matchs[st.session_state.matchs["ID Match"].str.strip() == m_id]
        if not match_info.empty:
            m_row = match_info.iloc[0]
            res_reel = str(m_row["Résultat"]).strip()
            score_reel = str(m_row["Score Réel"]).strip().replace(" ", "").replace("–", "-").replace("/", "-")
            buteurs_reels = [b.strip().lower() for b in str(m_row["Buteurs"]).split(",") if b.strip()]
            compteur_buts = {b: buteurs_reels.count(b) for b in set(buteurs_reels)}
            
            pts = 0
            p_1n2 = str(row_p["Prono (1N2)"]).strip().split()[0] if str(row_p["Prono (1N2)"]).strip() else ""
            p_score = str(row_p["Score"]).strip().replace(" ", "").replace("–", "-").replace("/", "-")
            p_buteur = str(row_p["Buteur"]).strip()
            p_double = str(row_p["Doublé ?"]).strip()
            
            if res_reel and p_1n2 == res_reel: pts += 2
            if score_reel and p_score == score_reel: pts +=
