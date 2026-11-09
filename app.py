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
    str_lit.session_state.donnees_chargees = True


def calculer_points():
    if str_lit.session_state.pronos.empty or str_lit.session_state.matchs.empty:
        return

    for idx, p in str_lit.session_state.pronos.iterrows():
        match_id = str(p["Match"]).strip()
        match_info = str_lit.session_state.matchs[
            str_lit.session_state.matchs["ID Match"].str.strip() == match_id
        ]

        if not match_info.empty:
            row = match_info.iloc[0]
            res_reel = str(row["Résultat"]).strip()

            score_reel_brut = str(row["Score Réel"]).strip()
            score_reel = (
                score_reel_brut.replace(" ", "")
                .replace("–", "-")
                .replace("/", "-")
            )

            buteurs_reels_brut = str(row["Buteurs"]).strip()
            buteurs_reels_liste = [
                b.strip().lower()
                for b in buteurs_reels_brut.split(",")
                if b.strip()
            ]
            compteur_buts_reels = {}
            for b in buteurs_reels_liste:
                compteur_buts_reels[b] = compteur_buts_reels.get(b, 0) + 1

            points = 0
            prono_1n2_brut = str(p["Prono (1N2)"]).strip()
            prono_1n2 = prono_1n2_brut.split()[0] if prono_1n2_brut else ""

            prono_score_brut = str(p["Score"]).strip()
            prono_score = (
                prono_score_brut.replace(" ", "")
                .replace("–", "-")
                .replace("/", "-")
            )

            p_buteur = str(p["Buteur"]).strip()
            p_double = str(p["Doublé ?"]).strip()

            # 1N2 correct (+2 pts)
            if res_reel and prono_1n2 == res_reel:
                points += 2

            # Score exact (+10 pts) uniquement si le score réel est valide et contient un tiret
            if score_reel and score_reel_brut and score_reel != "nan" and "-" in score_reel:
                if prono_score and prono_score == score_reel:
                    points += 10

            # Buteurs corrects (+3 pts par buteur)
            buteurs_choisis = [
                b.strip() for b in p_buteur.split(",") if b.strip() and b != "nan"
            ]
            for b in buteurs_choisis:
                b_lower = b.lower()
                if b_lower in compteur_buts_reels and compteur_buts_reels[b_lower] > 0:
                    points += 3

            # Doublé (+5 pts ou -3 pts)
            if p_double and p_double != "Aucun" and p_double != "nan":
                joueur_double_annonce = p_double.lower()
                buts_du_joueur = compteur_buts_reels.get(joueur_double_annonce, 0)
                if buts_du_joueur >= 2:
                    points += 5
                else:
                    points -= 3

            str_lit.session_state.pronos.loc[idx, "Points"] = int(points)
        else:
            str_lit.session_state.pronos.loc[idx, "Points"] = 0

    sauvegarder_donnees()

calculer_points()

# --- DESIGN ET STYLE ---
str_lit.markdown("""
    <style>
    .stApp { background-color: #f4f6f9; color: #002D62; }
    h1 { color: #002D62 !important; font-weight: 800; text-transform: uppercase; font-size: 1.5rem !important; }
    h2, h3, label, p { color: #002D62 !important; font-weight: 600; }
    .stButton > button { background-color: #E30613 !important; color: white !important; font-weight: bold !important; border-radius: 8px !important; width: 100%; }
    [data-testid="stSidebar"] { background-color: #002D62; }
    [data-testid="stSidebar"] p, [data-testid="stSidebar"] span, [data-testid="stSidebar"] label, [data-testid="stSidebar"] .stRadio div { color: white !important; font-weight: 600; }
    </style>
""", unsafe_allow_html=True)

# En-tête avec Logo centré
col1, col2, col3 = str_lit.columns([1, 1, 1])
with col2:
    try:
        str_lit.image("logo.png", width=150)
    except Exception:
        pass

str_lit.markdown(
    "<h1 style='text-align: center;'>⚽ CONCOURS DE PRONOS - SMC 🔴🔵</h1>",
    unsafe_allow_html=True,
)
str_lit.markdown(
    "<p style='text-align: center; color: #E30613 !important; font-weight: bold;'>Saison 2026-2027</p>",
    unsafe_allow_html=True,
)

# Menu Navigation Latéral
menu = str_lit.sidebar.radio(
    "📌 Navigation",
    [
        "📝 Faire mon Prono",
        "🏆 Classement",
        "👥 Participants",
        "⚙️ Espace Admin",
    ],
)


def obtenir_liste_participants():
    p_pronos = (
        str_lit.session_state.pronos["Participant"].unique().tolist()
        if not str_lit.session_state.pronos.empty
        and "Participant" in str_lit.session_state.pronos.columns
        else []
    )
    p_bonus = (
        str_lit.session_state.bonus["Participant"].unique().tolist()
        if not str_lit.session_state.bonus.empty
        and "Participant" in str_lit.session_state.bonus.columns
        else []
    )
    tous = set(PARTICIPANTS_INITIAUX + p_pronos + p_bonus)
    if "" in tous:
        tous.remove("")
    return sorted(list(tous))


# --- 1. FAIRE MON PRONO ---
if menu == "📝 Faire mon Prono":
    str_lit.header("✍️ Enregistrer ton Pronostic")

    if str_lit.session_state.matchs.empty:
        str_lit.warning(
            "⚠️ Aucun match trouvé. Va dans l'Espace Admin pour créer un match !"
        )
    else:
        matchs_visibles = []
        tz_paris = ZoneInfo("Europe/Paris")
        maintenant = datetime.now(tz_paris)

        for _, row in str_lit.session_state.matchs.iterrows():
            try:
                d_str = str(row["Date"]).strip()
                h_str = str(row["Heure"]).strip()
                match_dt = datetime.strptime(f"{d_str} {h_str}", "%Y-%m-%d %H:%M").replace(
                    tzinfo=tz_paris
                )
                ouverture_pronos = match_dt - timedelta(days=6)
                fermeture_affichage = match_dt + timedelta(hours=2)

                if ouverture_pronos <= maintenant <= fermeture_affichage:
                    matchs_visibles.append(row["ID Match"])
            except Exception:
                matchs_visibles.append(row["ID Match"])

        if not matchs_visibles and not str_lit.session_state.matchs.empty:
            matchs_visibles = [str_lit.session_state.matchs.iloc[-1]["ID Match"]]

        if not matchs_visibles:
            str_lit.info(
                "⏳ Aucun match ouvert aux pronostics pour le moment (les matchs s'ouvrent 6 jours avant la rencontre)."
            )
        else:
            choix_participant = str_lit.selectbox(
                "Pseudo", obtenir_liste_participants() + ["➕ Nouveau"]
            )

            nom_utilisateur = ""
            acces_autorise = False

            if choix_participant == "➕ Nouveau":
                nom_utilisateur = str_lit.text_input("Nouveau pseudo :").strip()
                if nom_utilisateur:
                    mdp_nouveau = str_lit.text_input(
                        "Crée ton mot de passe personnel :", type="password"
                    )
                    if str_lit.button("Valider la création du profil"):
                        if nom_utilisateur in obtenir_liste_participants():
                            str_lit.error("Ce pseudo existe déjà !")
                        elif not mdp_nouveau:
                            str_lit.error("Veuillez entrer un mot de passe.")
                        else:
                            str_lit.session_state.passwords[nom_utilisateur] = mdp_nouveau
                            sauvegarder_donnees()
                            str_lit.success("Profil créé ! Tu peux maintenant faire tes pronos.")
                            str_lit.rerun()
            else:
                nom_utilisateur = choix_participant
                if nom_utilisateur not in str_lit.session_state.passwords:
                    str_lit.info(
                        f"🔒 C'est ta première connexion avec ce pseudo ({nom_utilisateur}). Crée ton mot de passe personnel :"
                    )
                    mdp_creation = str_lit.text_input(
                        "Nouveau mot de passe :", type="password", key="pwd_create"
                    )
                    if str_lit.button("Enregistrer mon mot de passe"):
                        if mdp_creation:
                            str_lit.session_state.passwords[nom_utilisateur] = mdp_creation
                            sauvegarder_donnees()
                            str_lit.success("Mot de passe enregistré ! Rafraîchissement...")
                            str_lit.rerun()
                        else:
                            str_lit.error("Le mot de passe ne peut pas être vide.")
                else:
                    mdp_saisi = str_lit.text_input(
                        f"Mot de passe pour {nom_utilisateur} :",
                        type="password",
                        key="pwd_login",
                    )
                    if mdp_saisi == str_lit.session_state.passwords[nom_utilisateur]:
                        acces_autorise = True
                    elif mdp_saisi != "":
                        str_lit.error("Mot de passe incorrect.")

            if acces_autorise and nom_utilisateur:
                match_choisi = str_lit.selectbox("Sélectionne le match", matchs_visibles)

                match_ligne = str_lit.session_state.matchs[
                    str_lit.session_state.matchs["ID Match"] == match_choisi
                ].iloc[0]
                date_str = str(match_ligne["Date"]).strip()
                heure_str = str(match_ligne["Heure"]).strip()

                match_verrouille = False
                try:
                    match_datetime = datetime.strptime(
                        f"{date_str} {heure_str}", "%Y-%m-%d %H:%M"
                    ).replace(tzinfo=tz_paris)
                    if maintenant >= match_datetime:
                        match_verrouille = True
                except Exception:
                    match_datetime = datetime.strptime(
                        f"{date_str} {heure_str}", "%Y-%m-%d %H:%M"
                    )
                    if datetime.now() >= match_datetime:
                        match_verrouille = True

                existing_prono_row = str_lit.session_state.pronos[
                    (str_lit.session_state.pronos["Participant"] == nom_utilisateur)
                    & (str_lit.session_state.pronos["Match"] == match_choisi)
                ]

                if not existing_prono_row.empty:
                    r = existing_prono_row.iloc[0]
                    str_lit.info(
                        f"📌 **Ton prono actuel pour ce match** — 1N2 : **{r['Prono (1N2)']}**"
                        f" | Score : **{r['Score']}** | Buteur(s) : **{r['Buteur']}** |"
                        f" Doublé : **{r['Doublé ?']}**"
                    )
                else:
                    str_lit.warning(
                        "⚠️ Tu n'as pas encore enregistré de pronostic pour ce match."
                    )

                if match_verrouille:
                    str_lit.error(
                        "🔒 Ce match a déjà commencé (ou l'horaire est dépassé). Les pronos sont verrouillés pour cette rencontre !"
                    )
                else:
                    prono_1n2 = str_lit.selectbox(
                        "1N2", ["1 (Victoire Caen)", "N (Nul)", "2 (Défaite)"]
                    )
                    prono_score = str_lit.text_input("Score exact (ex: 2-0)")
                    buteurs_selectionnes = str_lit.multiselect("Buteurs", EFFECTIF_SMC)

                    if "Autre" in buteurs_selectionnes:
                        autre_buteur_saisi = str_lit.text_input(
                            "Préciser le nom du joueur (si 'Autre' sélectionné) :"
                        )
                        if autre_buteur_saisi:
                            buteurs_selectionnes = [
                                b if b != "Autre" else autre_buteur_saisi
                                for b in buteurs_selectionnes
                            ]

                    options_double = ["Aucun"] + buteurs_selectionnes
                    annonce_double = str_lit.selectbox(
                        "Doublé ?", options_double if options_double else ["Aucun"]
                    )

                    if str_lit.button("Valider / Modifier mon Prono 🚀"):
                        choix_clean = str(prono_1n2.split()[0])
                        buteurs_texte_str = str(", ".join(buteurs_selectionnes))

                        if not existing_prono_row.empty:
                            idx = existing_prono_row.index[0]
                            str_lit.session_state.pronos.loc[idx, "Prono (1N2)"] = choix_clean
                            str_lit.session_state.pronos.loc[idx, "Score"] = str(prono_score)
                            str_lit.session_state.pronos.loc[idx, "Buteur"] = buteurs_texte_str
                            str_lit.session_state.pronos.loc[idx, "Doublé ?"] = str(annonce_double)
                        else:
                            new_row = pd.DataFrame({
                                "Participant": [str(nom_utilisateur)],
                                "Match": [str(match_choisi)],
                                "Prono (1N2)": [choix_clean],
                                "Score": [str(prono_score)],
                                "Buteur": [buteurs_texte_str],
                                "Doublé ?": [str(annonce_double)],
                                "Points": [0],
                            })
                            str_lit.session_state.pronos = pd.concat(
                                [str_lit.session_state.pronos, new_row], ignore_index=True
                            )

                        calculer_points()
                        sauvegarder_donnees()
                        str_lit.success("Prono enregistré avec succès !")
                        str_lit.rerun()

                str_lit.markdown("---")
                str_lit.subheader(f"📊 Suivi des validations pour le match : {match_choisi}")
                str_lit.info(
                    "💡 Seul le statut (qui a pronostiqué ou non) est affiché ici. Les choix des joueurs restent secrets jusqu'au coup d'envoi !"
                )

                tous_les_participants = obtenir_liste_participants()
                pronos_ce_match = (
                    str_lit.session_state.pronos[
                        str_lit
