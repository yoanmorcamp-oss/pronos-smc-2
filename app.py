from datetime import datetime
import os
import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="Pronos SMC - Saison 2026-2027", page_icon="⚽", layout="wide"
)

MOT_DE_PASSE_ADMIN = "yoan"
FICHIER_DONNEES = "donnees_pronos.csv"

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


# --- GESTION DE LA PERSISTANCE (SAUVEGARDE FICHIER SÉCURISÉE) ---
def charger_donnees():
  if os.path.exists(FICHIER_DONNEES):
    try:
      df = pd.read_csv(FICHIER_DONNEES)
      if "Type" not in df.columns:
        os.remove(FICHIER_DONNEES)
        return pd.DataFrame()
      return df
    except Exception:
      if os.path.exists(FICHIER_DONNEES):
        os.remove(FICHIER_DONNEES)
  return pd.DataFrame()


def sauvegarder_donnees():
  dfs = []
  if not st.session_state.matchs.empty:
    m = st.session_state.matchs.copy()
    m["Type"] = "MATCH"
    dfs.append(m)
  if not st.session_state.pronos.empty:
    p = st.session_state.pronos.copy()
    p["Type"] = "PRONO"
    dfs.append(p)
  if not st.session_state.bonus.empty:
    b = st.session_state.bonus.copy()
    b["Type"] = "BONUS"
    dfs.append(b)

  if dfs:
    df_global = pd.concat(dfs, ignore_index=True)
    df_global.to_csv(FICHIER_DONNEES, index=False)


# --- INITIALISATION DE LA MÉMOIRE (SESSION STATE) ---
if "donnees_chargees" not in st.session_state:
  df_load = charger_donnees()

  if not df_load.empty and "Type" in df_load.columns:
    st.session_state.matchs = (
        df_load[df_load["Type"] == "MATCH"]
        .drop(columns=["Type"], errors="ignore")
        .dropna(how="all", axis=1)
        .reset_index(drop=True)
    )
    st.session_state.pronos = (
        df_load[df_load["Type"] == "PRONO"]
        .drop(columns=["Type"], errors="ignore")
        .dropna(how="all", axis=1)
        .reset_index(drop=True)
    )
    st.session_state.bonus = (
        df_load[df_load["Type"] == "BONUS"]
        .drop(columns=["Type"], errors="ignore")
        .dropna(how="all", axis=1)
        .reset_index(drop=True)
    )
  else:
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
    st.session_state.bonus = pd.DataFrame(
        columns=["Participant", "Points Bonus"]
    )

  st.session_state.donnees_chargees = True

# Forçage des types de colonnes
for col in [
    "ID Match",
    "Adversaire",
    "Date",
    "Heure",
    "Résultat",
    "Score Réel",
    "Buteurs",
]:
  if col not in st.session_state.matchs.columns:
    st.session_state.matchs[col] = ""
  st.session_state.matchs[col] = st.session_state.matchs[col].astype(str)

for col in [
    "Participant",
    "Match",
    "Prono (1N2)",
    "Score",
    "Buteur",
    "Doublé ?",
]:
  if col not in st.session_state.pronos.columns:
    st.session_state.pronos[col] = ""
  st.session_state.pronos[col] = st.session_state.pronos[col].astype(str)

if "Points" not in st.session_state.pronos.columns:
  st.session_state.pronos["Points"] = 0
st.session_state.pronos["Points"] = (
    pd.to_numeric(st.session_state.pronos["Points"], errors="coerce")
    .fillna(0)
    .astype(int)
)

for col in ["Participant"]:
  if col not in st.session_state.bonus.columns:
    st.session_state.bonus[col] = ""
  st.session_state.bonus[col] = st.session_state.bonus[col].astype(str)
if "Points Bonus" not in st.session_state.bonus.columns:
  st.session_state.bonus["Points Bonus"] = 0
st.session_state.bonus["Points Bonus"] = (
    pd.to_numeric(st.session_state.bonus["Points Bonus"], errors="coerce")
    .fillna(0)
    .astype(int)
)


# --- FONCTION DE CALCUL DES POINTS SÉCURISÉE ---
def calculer_points():
  if st.session_state.pronos.empty or st.session_state.matchs.empty:
    return

  for idx, p in st.session_state.pronos.iterrows():
    match_id = str(p["Match"])
    match_info = st.session_state.matchs[
        st.session_state.matchs["ID Match"] == match_id
    ]

    if not match_info.empty:
      row = match_info.iloc[0]
      res_reel = str(row["Résultat"]).strip()
      score_reel = str(row["Score Réel"]).strip()
      buteurs_reels = str(row["Buteurs"]).lower()

      points = 0
      prono_1n2 = str(p["Prono (1N2)"]).strip()
      prono_score = str(p["Score"]).strip()
      p_buteur = str(p["Buteur"]).strip()
      p_double = str(p["Doublé ?"]).strip()

      if res_reel and prono_1n2 == res_reel:
        points += 3
      if score_reel and prono_score == score_reel:
        points += 5
      if buteurs_reels and p_buteur:
        buteurs_choisis = [b.strip() for b in p_buteur.split(",")]
        for b in buteurs_choisis:
          if b != "Autre" and b.lower() in buteurs_reels:
            points += 2
      if (
          p_double != "Aucun"
          and p_double != "Autre"
          and p_double.lower() in buteurs_reels
      ):
        points += 3

      st.session_state.pronos.loc[idx, "Points"] = int(points)
  sauvegarder_donnees()


# --- DESIGN & UI ---
st.markdown("""
    <style>
    .stApp { background-color: #f4f6f9; color: #002D62; }
    h1 { color: #002D62 !important; font-weight: 800; text-transform: uppercase; font-size: 1.5rem !important; }
    h2, h3, label, p { color: #002D62 !important; font-weight: 600; }
    .stButton > button { background-color: #E30613 !important; color: white !important; font-weight: bold !important; border-radius: 8px !important; width: 100%; }
    [data-testid="stSidebar"] { background-color: #002D62; }
    [data-testid="stSidebar"] p, [data-testid="stSidebar"] span, [data-testid="stSidebar"] label, [data-testid="stSidebar"] .stRadio div { color: white !important; font-weight: 600; }
    </style>
""", unsafe_allow_html=True)

st.markdown(
    "<h1 style='text-align: center;'>🔴🔵 CONCOURS DE PRONOS - SMC"
    " 🔵🔴</h1>",
    unsafe_allow_html=True,
)
st.markdown(
    "<p style='text-align: center; color: #E30613 !important; font-weight:"
    " bold;'>Saison 2026-2027</p>",
    unsafe_allow_html=True,
)

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
    st.warning(
        "⚠️ Aucun match créé pour l'instant. Va dans l'Espace Admin pour en"
        " ajouter un !"
    )
  else:
    with st.expander("📅 Voir les détails des matchs enregistrés"):
      st.dataframe(st.session_state.matchs, use_container_width=True)

    matchs_disponibles = st.session_state.matchs["ID Match"].tolist()
    choix_participant = st.selectbox(
        "Pseudo", obtenir_liste_participants() + ["➕ Nouveau"]
    )
    nom_utilisateur = (
        st.text_input("Nouveau pseudo :")
        if choix_participant == "➕ Nouveau"
        else choix_participant
    )
    match_choisi = st.selectbox("Sélectionne le match", matchs_disponibles)

    match_ligne = st.session_state.matchs[
        st.session_state.matchs["ID Match"] == match_choisi
    ].iloc[0]
    date_str = str(match_ligne["Date"]).strip()
    heure_str = str(match_ligne["Heure"]).strip()

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
          "⏳ Ce match a déjà commencé. Les pronos sont verrouillés pour cette"
          " rencontre !"
      )
    else:
      prono_1n2 = st.selectbox(
          "1N2", ["1 (Victoire Caen)", "N (Nul)", "2 (Défaite)"]
      )
      prono_score = st.text_input("Score exact (ex: 2-0)")
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

      if st.button("Valider mon Prono 🚀"):
        if match_verrouille:
          st.error("Impossible de valider : le match a commencé !")
        elif nom_utilisateur:
          choix_clean = str(prono_1n2.split()[0])
          buteurs_texte_str = str(", ".join(buteurs_selectionnes))

          existing_idx = st.session_state.pronos[
              (st.session_state.pronos["Participant"] == str(nom_utilisateur))
              & (st.session_state.pronos["Match"] == str(match_choisi))
          ].index

          if not existing_idx.empty:
            idx = existing_idx[0]
            st.session_state.pronos.loc[idx, "Prono (1N2)"] = choix_clean
            st.session_state.pronos.loc[idx, "Score"] = str(prono_score)
            st.session_state.pronos.loc[idx, "Buteur"] = buteurs_texte_str
            st.session_state.pronos.loc[idx, "Doublé ?"] = str(annonce_double)
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
            st.session_state.pronos = pd.concat(
                [st.session_state.pronos, new_row], ignore_index=True
            )

          calculer_points()
          sauvegarder_donnees()
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
      and "Participant" in st.session_state.pronos.columns
      else pd.DataFrame(columns=["Participant", "Points"])
  )

  if not p_pronos_sum.empty or not st.session_state.bonus.empty:
    classement_complet = pd.merge(
        p_pronos_sum, st.session_state.bonus, on="Participant", how="outer"
    ).fillna(0)
    classement_complet["Points Total"] = classement_complet[
        "Points"
    ] + classement_complet["Points Bonus"].astype(int)
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
        st.session_state.bonus.loc[
            existing_b[0], "Points Bonus"
        ] += int(pts_bonus)
      else:
        new_b = pd.DataFrame(
            {"Participant": [p_choisi], "Points Bonus": [int(pts_bonus)]}
        )
        st.session_state.bonus = pd.concat(
            [st.session_state.bonus, new_b], ignore_index=True
        )
      sauvegarder_donnees()
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
            new_m = pd.DataFrame({
                "ID Match": [str(id_m)],
                "Adversaire": [str(adv)],
                "Date": [str(date_m)],
                "Heure": [heure_m.strftime("%H:%M")],
                "Résultat": [""],
                "Score Réel": [""],
                "Buteurs": [""],
            })
            st.session_state.matchs = pd.concat(
                [st.session_state.matchs, new_m], ignore_index=True
            )
            sauvegarder_donnees()
            st.success("Match créé et sauvegardé durablement !")
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

        adversaire_nom = (
            str(match_ligne["Adversaire"]).strip()
            if "Adversaire" in match_ligne and str(match_ligne["Adversaire"])
            else "Adversaire"
        )

        with st.form("f_resultat"):
          res_actuel = str(match_ligne["Résultat"])
          score_actuel = str(match_ligne["Score Réel"])
          buteurs_actuels_str = str(match_ligne["Buteurs"])

          options_dict = {
              "": "",
              "1": f"Victoire de Caen (1)",
              "N": f"Match Nul (N)",
              "2": f"Victoire de {adversaire_nom} (2)",
          }
          options_keys = list(options_dict.keys())

          index_initial = 0
          if res_actuel in options_keys:
            index_initial = options_keys.index(res_actuel)

          choix_res_form = st.selectbox(
              "Vainqueur Réel",
              options_keys,
              format_func=lambda x: options_dict[x],
              index=index_initial,
          )

          score_reel = st.text_input(
              "Score Réel exact (ex: 2-1)", value=score_actuel
          )

          buteurs_deja_enregistres = [
              b.strip() for b in buteurs_actuels_str.split(",") if b.strip()
          ]
          buteurs_reels_choisis = st.multiselect(
              "Buteurs réels",
              EFFECTIF_SMC,
              default=[
                  b
                  for b in buteurs_deja_enregistres
                  if b in EFFECTIF_SMC
              ],
          )

          autre_buteur_reel_saisi = ""
          if "Autre" in buteurs_reels_choisis:
            autre_buteur_reel_saisi = st.text_input(
                "Préciser le nom du joueur (si 'Autre' sélectionné pour les"
                " buts réels) :"
            )

          if st.form_submit_button("Enregistrer les résultats et calculer"):
            liste_finale_buteurs = []
            for b in buteurs_reels_choisis:
              if b == "Autre" and autre_buteur_reel_saisi:
                liste_finale_buteurs.append(autre_buteur_reel_saisi)
              elif b != "Autre":
                liste_finale_buteurs.append(b)

            buteurs_texte_final = ", ".join(liste_finale_buteurs)

            idx_m = st.session_state.matchs[
                st.session_state.matchs["ID Match"] == match_a_maj
            ].index[0]
            st.session_state.matchs.loc[idx_m, "Résultat"] = str(choix_res_form)
            st.session_state.matchs.loc[idx_m, "Score Réel"] = str(score_reel)
            st.session_state.matchs.loc[idx_m, "Buteurs"] = str(
                buteurs_texte_final
            )

            calculer_points()
            sauvegarder_donnees()
            st.success(
                "Résultats enregistrés, points recalculés et sauvegardés !"
            )
            st.rerun()

    st.subheader("Liste des matchs actuels")
    st.dataframe(st.session_state.matchs, use_container_width=True)

    # --- SECTION SUPPRESSION DE MATCH ---
    if not st.session_state.matchs.empty:
      st.markdown("---")
      st.subheader("🗑️ Supprimer un Match")
      match_a_supprimer = st.selectbox(
          "Choisir le match à supprimer",
          st.session_state.matchs["ID Match"].tolist(),
          key="select_suppr_match",
      )
      if st.button("Supprimer ce match définitivement ❌"):
        # Supprime le match de la liste
        st.session_state.matchs = st.session_state.matchs[
            st.session_state.matchs["ID Match"] != match_a_supprimer
        ].reset_index(drop=True)

        # Nettoie aussi les pronos liés à ce match pour éviter les bugs
        if not st.session_state.pronos.empty:
          st.session_state.pronos = st.session_state.pronos[
              st.session_state.pronos["Match"] != match_a_supprimer
          ].reset_index(drop=True)

        sauvegarder_donnees()
        st.success(
            f"Le match '{match_a_supprimer}' et ses pronos associés ont bien"
            " été supprimés !"
        )
        st.rerun()

  elif mdp != "":
    st.error("Mot de passe incorrect.")
