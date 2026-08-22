import base64
from datetime import datetime
import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="Pronos SMC - Saison 2026-2027", page_icon="⚽", layout="wide"
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

# --- INITIALISATION DE LA MÉMOIRE (SESSION STATE) ---
if "matchs" not in st.session_state:
  st.session_state.matchs = pd.DataFrame(
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

if "pronos" not in st.session_state:
  st.session_state.pronos = pd.DataFrame(
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

if "bonus" not in st.session_state:
  st.session_state.bonus = pd.DataFrame(columns=["Participant", "Points Bonus"])


# --- FONCTION DE CALCUL DES POINTS ---
def calculer_points():
  if st.session_state.pronos.empty or st.session_state.matchs.empty:
    return

  for idx, p in st.session_state.pronos.iterrows():
    match_id = p["Match"]
    match_info = st.session_state.matchs[
        st.session_state.matchs["ID Match"] == match_id
    ]

    if not match_info.empty:
      res_reel = str(match_info.iloc[0]["Résultat"]).strip()
      score_reel = str(match_info.iloc[0]["Score Réel"]).strip()
      buteurs_reels = str(match_info.iloc[0]["Buteurs"]).lower()

      points = 0
      prono_1n2 = str(p["Prono (1N2)"]).strip()
      prono_score = str(p["Score"]).strip()
      p_buteur = str(p["Buteur"]).strip()
      p_double = str(p["Doublé ?"]).strip()

      # 1. Bon 1N2 (3 points)
      if res_reel and prono_1n2 == res_reel:
        points += 3

      # 2. Bon score exact (5 points bonus)
      if score_reel and prono_score == score_reel:
        points += 5

      # 3. Buteur trouvé (2 points par buteur)
      if buteurs_reels and p_buteur:
        buteurs_choisis = [b.strip() for b in p_buteur.split(",")]
        for b in buteurs_choisis:
          if b != "Autre" and b.lower() in buteurs_reels:
            points += 2

      # 4. Doublé trouvé (3 points bonus)
      if (
          p_double != "Aucun"
          and p_double != "Autre"
          and p_double.lower() in buteurs_reels
      ):
        points += 3

      st.session_state.pronos.loc[idx, "Points"] = points


# --- DESIGN & UI ---
st.markdown("""
    <style>
    .stApp { background-color: #f4f6f9; color: #002D62; }
    h1 { color: #002D62 !important; font-weight: 800; text-transform: uppercase; }
    h2, h3, label, p { color: #002D62 !important; font-weight: 600; }
    .stButton > button { background-color: #E30613 !important; color: white !important; font-weight: bold !important; border-radius: 8px !important; }
    
    [data-testid="stSidebar"] { background-color: #002D62; }
    [data-testid="stSidebar"] p, [data-testid="stSidebar"] span, [data-testid="stSidebar"] label, [data-testid="stSidebar"] .stRadio div { color: white !important; font-weight: 600; }
    </style>
""", unsafe_allow_html=True)

# En-tête avec Logo SMC et Titre
col_logo, col_titre = st.columns([1, 5])
with col_logo:
  st.image(
      "https://upload.wikimedia.org/wikipedia/fr/thumb/e/e1/Stade_Malherbe_Caen_logo_2024.svg/langfr-120px-Stade_Malherbe_Caen_logo_2024.svg.png",
      width=90,
  )
with col_titre:
  st.title("Concours de Pronos - SMC")

menu = st.sidebar.radio(
    "🧭 Navigation",
    [
        "📝 Faire mon Prono",
        "🏆 Classement",
        "👥 Participants & Bonus",
        "⚙️ Espace Admin",
    ],
)


def obtenir_liste_participants():
  p_pronos = (
      st.session_state.pronos["Participant"].unique().tolist()
      if not st.session_state.pronos.empty
      and "Participant" in st.session_state.pronos.columns
      else []
  )
  p_bonus = (
      st.session_state.bonus["Participant"].unique().tolist()
      if not st.session_state.bonus.empty
      and "Participant" in st.session_state.bonus.columns
      else []
  )
  tous = set(PARTICIPANTS_INITIAUX + p_pronos + p_bonus)
  if "" in tous:
    tous.remove("")
  return sorted(list(tous))


# --- ONGLET 1 : FAIRE MON PRONO ---
if menu == "📝 Faire mon Prono":
  st.header("🎯 Enregistrer ton Pronostic")
  if st.session_state.matchs.empty:
    st.info(
        "Aucun match ouvert pour l'instant. Demande à l'admin d'en ajouter un !"
    )
  else:
    matchs_disponibles = st.session_state.matchs["ID Match"].tolist()
    choix_participant = st.selectbox(
        "Pseudo", obtenir_liste_participants() + ["➕ Nouveau"]
    )
    nom_utilisateur = (
        st.text_input("Nouveau pseudo :")
        if choix_participant == "➕ Nouveau"
        else choix_participant
    )
    match_choisi = st.selectbox("Match", matchs_disponibles)

    # Vérification du verrouillage selon la date et l'heure du match
    match_ligne = st.session_state.matchs[
        st.session_state.matchs["ID Match"] == match_choisi
    ].iloc[0]
    date_str = str(match_ligne["Date"])
    heure_str = str(match_ligne["Heure"])

    match_verrouille = False
    try:
      match_datetime = datetime.strptime(
          f"{date_str} {heure_str}", "%Y-%m-%d %H:%M"
      )
      if datetime.now() >= match_datetime:
        match_verrouille = True
    except Exception:
      pass

    if match_verrouille:
      st.error(
          "⏳ Ce match a déjà commencé (ou l'horaire est dépassé). Les pronos"
          " sont verrouillés pour cette rencontre !"
      )
    else:
      col1, col2 = st.columns(2)
      with col1:
        prono_1n2 = st.selectbox(
            "1N2", ["1 (Victoire Caen)", "N (Nul)", "2 (Défaite)"]
        )
        prono_score = st.text_input("Score exact (ex: 2-0)")
      with col2:
        buteurs_selectionnes = st.multiselect("Buteurs", EFFECTIF_SMC)

      if "Autre" in buteurs_selectionnes:
        autre_buteur_saisi = st.text_input(
            "Préciser le nom du joueur (si 'Autre' sélectionné) :"
        )
        if autre_buteur_saisi:
          buteurs_selectionnes = [
              b if b != "Autre" else autre_buteur_saisi
              for b in buteurs_selectionnes
          ]

      options_double = ["Aucun"] + buteurs_selectionnes
      annonce_double = st.selectbox(
          "Doublé ?", options_double if options_double else ["Aucun"]
      )

      if st.button("Valider 🚀"):
        if nom_utilisateur:
          choix_clean = prono_1n2.split()[0]
          buteurs_texte_str = ", ".join(buteurs_selectionnes)

          existing_idx = st.session_state.pronos[
              (st.session_state.pronos["Participant"] == nom_utilisateur)
              & (st.session_state.pronos["Match"] == match_choisi)
          ].index
          if not existing_idx.empty:
            idx = existing_idx[0]
            st.session_state.pronos.loc[idx, "Prono (1N2)"] = choix_clean
            st.session_state.pronos.loc[idx, "Score"] = prono_score
            st.session_state.pronos.loc[idx, "Buteur"] = buteurs_texte_str
            st.session_state.pronos.loc[idx, "Doublé ?"] = annonce_double
          else:
            new_row = pd.DataFrame({
                "Participant": [nom_utilisateur],
                "Match": [match_choisi],
                "Prono (1N2)": [choix_clean],
                "Score": [prono_score],
                "Buteur": [buteurs_texte_str],
                "Doublé ?": [annonce_double],
                "Points": [0],
            })
            st.session_state.pronos = pd.concat(
                [st.session_state.pronos, new_row], ignore_index=True
            )

          calculer_points()
          st.success("Prono enregistré avec succès !")
          st.rerun()
        else:
          st.error("Merci d'indiquer un pseudo.")

  if not st.session_state.pronos.empty:
    st.subheader("📋 Tous les pronos enregistrés")
    st.dataframe(st.session_state.pronos, use_container_width=True)

# --- ONGLET 2 : CLASSEMENT ---
elif menu == "🏆 Classement":
  st.header("🏆 Classement Général")
  calculer_points()

  p_pronos_sum = (
      st.session_state.pronos.groupby("Participant")["Points"]
      .sum()
      .reset_index()
      if not st.session_state.pronos.empty
      else pd.DataFrame(columns=["Participant", "Points"])
  )

  if not p_pronos_sum.empty or not st.session_state.bonus.empty:
    classement_complet = pd.merge(
        p_pronos_sum, st.session_state.bonus, on="Participant", how="outer"
    ).fillna(0)
    classement_complet["Points Total"] = (
        classement_complet["Points"]
        + classement_complet["Points Bonus"].astype(float)
    )
    classement_final = (
        classement_complet[["Participant", "Points Total", "Points Bonus"]]
        .sort_values(by="Points Total", ascending=False)
        .reset_index(drop=True)
    )
    classement_final.index += 1
    st.dataframe(classement_final, use_container_width=True)
  else:
    st.info("Le classement est vide pour le moment.")

# --- ONGLET 3 : PARTICIPANTS & BONUS ---
elif menu == "👥 Participants & Bonus":
  st.header("👥 Gestion des Participants & Bonus")
  st.write("Participants initiaux :", ", ".join(PARTICIPANTS_INITIAUX))

  st.subheader("Attribution de points bonus (Admin / Spécial)")
  with st.form("f_bonus"):
    p_choisi = st.selectbox("Participant", obtenir_liste_participants())
    pts_bonus = st.number_input("Points Bonus à ajouter", value=0, step=1)
    if st.form_submit_button("Valider le bonus"):
      existing_b = st.session_state.bonus[
          st.session_state.bonus["Participant"] == p_choisi
      ].index
      if not existing_b.empty:
        st.session_state.bonus.loc[existing_b[0], "Points Bonus"] += pts_bonus
      else:
        new_b = pd.DataFrame(
            {"Participant": [p_choisi], "Points Bonus": [pts_bonus]}
        )
        st.session_state.bonus = pd.concat(
            [st.session_state.bonus, new_b], ignore_index=True
        )
      st.success("Bonus mis à jour !")
      st.rerun()

  if not st.session_state.bonus.empty:
    st.dataframe(st.session_state.bonus, use_container_width=True)

# --- ONGLET 4 : ESPACE ADMIN ---
elif menu == "⚙️ Espace Admin":
  st.header("🔐 Espace Organisateur")
  mdp = st.text_input("Mot de passe administrateur :", type="password")

  if mdp == MOT_DE_PASSE_ADMIN:
    st.success("Accès autorisé !")

    tab_m, tab_res = st.tabs(["➕ Ajouter un Match", "⚽ Saisir les Résultats"])

    with tab_m:
      with st.form("f_match"):
        id_m = st.text_input("Nom du Match (ex: SMC - Bastia)")
        adv = st.text_input("Adversaire")
        date_m = st.date_input("Date du match")
        heure_m = st.time_input("Heure du match")
        if st.form_submit_button("Créer le match"):
          if id_m:
            st.session_state.matchs = pd.concat(
                [
                    st.session_state.matchs,
                    pd.DataFrame({
                        "ID Match": [id_m],
                        "Adversaire": [adv],
                        "Date": [str(date_m)],
                        "Heure": [heure_m.strftime("%H:%M")],
                        "Résultat": [""],
                        "Score Réel": [""],
                        "Buteurs": [""],
                    }),
                ],
                ignore_index=True,
            )
            st.success("Match créé avec succès et verrouillage programmé !")
            st.rerun()

    with tab_res:
      if st.session_state.matchs.empty:
        st.info("Aucun match à renseigner.")
      else:
        match_a_maj = st.selectbox(
            "Sélectionner le match terminé",
            st.session_state.matchs["ID Match"].tolist(),
        )
        match_ligne = st.session_state.matchs[
            st.session_state.matchs["ID Match"] == match_a_maj
        ].iloc[0]

        with st.form("f_resultat"):
          res_reel = st.selectbox(
              "Vainqueur Réel",
              ["", "1", "N", "2"],
              index=(
                  ["", "1", "N", "2"].index(match_ligne["Résultat"])
                  if match_ligne["Résultat"] in ["", "1", "N", "2"]
                  else 0
              ),
          )
          score_reel = st.text_input(
              "Score Réel exact (ex: 2-1)", value=match_ligne["Score Réel"]
          )
          buteurs_reels = st.text_input(
              "Buteurs réels (séparés par des virgules)",
              value=match_ligne["Buteurs"],
          )

          if st.form_submit_button("Enregistrer les résultats et calculer"):
            idx_m = st.session_state.matchs[
                st.session_state.matchs["ID Match"] == match_a_maj
            ].index[0]
            st.session_state.matchs.loc[idx_m, "Résultat"] = res_reel
            st.session_state.matchs.loc[idx_m, "Score Réel"] = score_reel
            st.session_state.matchs.loc[idx_m, "Buteurs"] = buteurs_reels

            calculer_points()
            st.success(
                "Résultats enregistrés et points recalculés automatiquement"
                " pour tout le monde !"
            )
            st.rerun()

    st.subheader("Liste des matchs actuels")
    st.dataframe(st.session_state.matchs, use_container_width=True)

  elif mdp != "":
    st.error("Mot de passe incorrect.")
