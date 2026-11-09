from datetime import datetime, timedelta
import json
import os
from zoneinfo import ZoneInfo
import pandas as pd
import streamlit as st
from github import Github, GithubException

# --- CONFIGURATION DE LA PAGE ---
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

# --- GITHUB / DONNÉES ---
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
            prono_1n2_str = str(row_p["Prono (1N2)"]).strip()
            p_1n2 = prono_1n2_str.split()[0] if prono_1n2_str else ""
            p_score = str(row_p["Score"]).strip().replace(" ", "").replace("–", "-").replace("/", "-")
            p_buteur = str(row_p["Buteur"]).strip()
            p_double = str(row_p["Doublé ?"]).strip()
            
            if res_reel and p_1n2 == res_reel: pts += 2
            if score_reel and p_score == score_reel: pts += 10
            
            choix_buteurs = [b.strip() for b in p_buteur.split(",") if b.strip() and b != "nan"]
            for b in choix_buteurs:
                if b.lower() in compteur_buts and compteur_buts[b.lower()] > 0:
                    pts += 3
                    
            if p_double and p_double != "Aucun" and p_double != "nan":
                if compteur_buts.get(p_double.lower(), 0) >= 2: pts += 5
                else: pts -= 3
                
            st.session_state.pronos.loc[idx, "Points"] = int(pts)
        else:
            st.session_state.pronos.loc[idx, "Points"] = 0
    sauvegarder_donnees()

try:
    calculer_points()
except Exception:
    pass

st.markdown("<style>.stApp { background-color: #f4f6f9; color: #002D62; } h1 { color: #002D62 !important; font-weight: 800; }</style>", unsafe_allow_html=True)

col1, col2, col3 = st.columns([1, 1, 1])
with col2:
    try: st.image("logo.png", width=150)
    except Exception: pass

st.markdown("<h1 style='text-align: center;'>⚽ CONCOURS DE PRONOS - SMC 🔴🔵</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: #E30613; font-weight: bold;'>Saison 2026-2027</p>", unsafe_allow_html=True)

menu = st.sidebar.radio("📌 Navigation", ["📝 Faire mon Prono", "🏆 Classement", "👥 Participants", "⚙️ Espace Admin"])

def get_participants():
    p_pronos = st.session_state.pronos["Participant"].unique().tolist() if not st.session_state.pronos.empty and "Participant" in st.session_state.pronos.columns else []
    p_bonus = st.session_state.bonus["Participant"].unique().tolist() if not st.session_state.bonus.empty and "Participant" in st.session_state.bonus.columns else []
    tous = set(PARTICIPANTS_INITIAUX + p_pronos + p_bonus)
    if "" in tous: tous.remove("")
    return sorted(list(tous))

# --- 1. FAIRE MON PRONO ---
if menu == "📝 Faire mon Prono":
    st.header("✍️ Enregistrer ton Pronostic")
    if st.session_state.matchs.empty:
        st.warning("⚠️ Aucun match trouvé. Va dans l'Espace Admin pour créer un match !")
    else:
        matchs_visibles = st.session_state.matchs["ID Match"].tolist()
        choix_p = st.selectbox("Pseudo", get_participants() + ["➕ Nouveau"])
        
        nom_u, acces = "", False
        if choix_p == "➕ Nouveau":
            nom_u = st.text_input("Nouveau pseudo :").strip()
            if nom_u:
                mdp_n = st.text_input("Crée ton mot de passe :", type="password")
                if st.button("Valider la création"):
                    if nom_u in get_participants(): st.error("Existe déjà !")
                    elif not mdp_n: st.error("Mot de passe vide.")
                    else:
                        st.session_state.passwords[nom_u] = mdp_n
                        sauvegarder_donnees()
                        st.success("Profil créé !")
                        st.rerun()
        else:
            nom_u = choix_p
            if nom_u not in st.session_state.passwords:
                st.info(f"🔒 Première connexion pour {nom_u}. Crée ton mot de passe :")
                mdp_c = st.text_input("Mot de passe :", type="password")
                if st.button("Enregistrer"):
                    if mdp_c:
                        st.session_state.passwords[nom_u] = mdp_c
                        sauvegarder_donnees()
                        st.success("Enregistré !")
                        st.rerun()
            else:
                mdp_s = st.text_input(f"Mot de passe pour {nom_u} :", type="password")
                if mdp_s == st.session_state.passwords[nom_u]: acces = True
                elif mdp_s: st.error("Incorrect.")
                
        if acces and nom_u:
            match_c = st.selectbox("Sélectionne le match", matchs_visibles)
            existing = st.session_state.pronos[(st.session_state.pronos["Participant"] == nom_u) & (st.session_state.pronos["Match"] == match_c)]
            
            if not existing.empty:
                r = existing.iloc[0]
                st.info(f"📌 Prono actuel — 1N2 : **{r['Prono (1N2)']}** | Score : **{r['Score']}** | Buteur : **{r['Buteur']}**")
                
            p_1n2 = st.selectbox("1N2", ["1 (Victoire Caen)", "N (Nul)", "2 (Défaite)"])
            p_score = st.text_input("Score exact (ex: 2-0)")
            buteurs_sel = st.multiselect("Buteurs", EFFECTIF_SMC)
            double_sel = st.selectbox("Doublé ?", ["Aucun"] + buteurs_sel)
            
            if st.button("Valider mon Prono 🚀"):
                c_clean = p_1n2.split()[0]
                b_str = ", ".join(buteurs_sel)
                if not existing.empty:
                    idx = existing.index[0]
                    st.session_state.pronos.loc[idx, ["Prono (1N2)", "Score", "Buteur", "Doublé ?"]] = [c_clean, p_score, b_str, double_sel]
                else:
                    new_r = pd.DataFrame({"Participant": [nom_u], "Match": [match_c], "Prono (1N2)": [c_clean], "Score": [p_score], "Buteur": [b_str], "Doublé ?": [double_sel], "Points": [0]})
                    st.session_state.pronos = pd.concat([st.session_state.pronos, new_r], ignore_index=True)
                calculer_points()
                sauvegarder_donnees()
                st.success("Prono enregistré !")
                st.rerun()

# --- 2. CLASSEMENT ---
elif menu == "🏆 Classement":
    st.header("🏆 Classement Général")
    try: calculer_points()
    except Exception: pass
    
    df_p = st.session_state.pronos.groupby("Participant")["Points"].sum().reset_index() if not st.session_state.pronos.empty and "Participant" in st.session_state.pronos.columns else pd.DataFrame(columns=["Participant", "Points"])
    df_b = st.session_state.bonus if not st.session_state.bonus.empty else pd.DataFrame(columns=["Participant", "Points Bonus"])
    
    if not df_p.empty or not df_b.empty:
        comp = pd.merge(df_p, df_b, on="Participant", how="outer").fillna(0)
        comp["Points Pronos"] = comp["Points"].astype(int)
        comp["Points Bonus"] = comp["Points Bonus"].astype(int)
        comp["Points Total"] = comp["Points Pronos"] + comp["Points Bonus"]
        final = comp[["Participant", "Points Pronos", "Points Bonus", "Points Total"]].sort_values(by="Points Total", ascending=False).reset_index(drop=True)
        final.index += 1
        st.dataframe(final, use_container_width=True)
    else:
        st.info("Classement vide.")

# --- 3. PARTICIPANTS ---
elif menu == "👥 Participants":
    st.header("👥 Participants")
    st.write(", ".join(get_participants()))

# --- 4. ESPACE ADMIN ---
elif menu == "⚙️ Espace Admin":
    st.header("⚙️ Espace Organisateur")
    mdp_adm = st.text_input("Mot de passe admin :", type="password")
    
    if mdp_adm == MOT_DE_PASSE_ADMIN:
        st.success("Autorisé !")
        t1, t2, t3 = st.tabs(["➕ Ajouter Match", "🎯 Résultats", "➕ Bonus"])
        with t1:
            with st.form("f_m"):
                id_m = st.text_input("Nom du Match")
                adv = st.text_input("Adversaire")
                d_m = st.date_input("Date")
                h_m = st.time_input("Heure")
                if st.form_submit_button("Créer"):
                    if id_m:
                        new_m = pd.DataFrame({"ID Match": [id_m], "Adversaire": [adv], "Date": [str(d_m)], "Heure": [h_m.strftime("%H:%M")], "Résultat": [""], "Score Réel": [""], "Buteurs": [""]})
                        st.session_state.matchs = pd.concat([st.session_state.matchs, new_m], ignore_index=True)
                        sauvegarder_donnees()
                        st.success("Créé !")
                        st.rerun()
        with t2:
            if not st.session_state.matchs.empty:
                m_sel = st.selectbox("Match", st.session_state.matchs["ID Match"].tolist())
                with st.form("f_res"):
                    r_form = st.selectbox("V
