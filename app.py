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
PARTICIPANTS_INITIAUX = ["Nathéo", "Adri", "Axel", "Allan", "Jo", "Vincent", "Tony", "Yoan"]

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

  return df_matchs, df_pronos, df_bonus


def sauvegarder_donnees():
  data = {
      "matchs": str_lit.session_state.matchs.to_dict(orient="records"),
      "pronos": str_lit.session_state.pronos.to_dict(orient="records"),
      "bonus": str_lit.session_state.bonus.to_dict(orient="records"),
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


# --- INITIALISATION DE LA SESSION STATE ---
if "donnees_chargees" not in str_lit.session_state:
  m, p, b = charger_donnees_depuis_github()
  str_lit.session_state.matchs = m
  str_lit.session_state.pronos = p
  str_lit.session_state.bonus = b
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
      score_reel = (
          str(row["Score Réel"]).strip().replace(" ", "").replace("–", "-")
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
      prono_score = (
          str(p["Score"]).strip().replace(" ", "").replace("–", "-")
      )
      p_buteur = str(p["Buteur"]).strip()
      p_double = str(p["Doublé ?"]).strip()

      # 1N2 correct (+2 pts)
      if res_reel and prono_1n2 == res_reel:
        points += 2

      # Score exact correct (+10 pts)
      if score_reel and prono_score and prono_score == score_reel:
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
    "<h1 style='text-align: center;'>⚽ CONCOURS DE PRONOS - SMC"
    " 🔴🔵</h1>",
    unsafe_allow_html=True,
)
str_lit.markdown(
    "<p style='text-align: center; color: #E30613 !important; font-weight:"
    " bold;'>Saison 2026-2027</p>",
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
        fermeture_affichage = match_dt + timedelta(
            hours=2
        )  # Masque le match 2h après le début

        if ouverture_pronos <= maintenant <= fermeture_affichage:
          matchs_visibles.append(row["ID Match"])
      except Exception:
        matchs_visibles.append(row["ID Match"])

    # Fallback pour ne pas bloquer si aucun match n'est dans la fenêtre exacte
    if not matchs_visibles and not str_lit.session_state.matchs.empty:
      matchs_visibles = [str_lit.session_state.matchs.iloc[-1]["ID Match"]]

    if not matchs_visibles:
      str_lit.info(
          "⏳ Aucun match ouvert aux pronostics pour le moment (les matchs"
          " s'ouvrent 6 jours avant la rencontre)."
      )
    else:
      choix_participant = str_lit.selectbox(
          "Pseudo", obtenir_liste_participants() + ["➕ Nouveau"]
      )
      nom_utilisateur = (
          str_lit.text_input("Nouveau pseudo :")
          if choix_participant == "➕ Nouveau"
          else choix_participant
      )
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

      if match_verrouille:
        str_lit.error(
            "🔒 Ce match a déjà commencé (ou l'horaire est dépassé). Les pronos"
            " sont verrouillés pour cette rencontre !"
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

        if str_lit.button("Valider mon Prono 🚀"):
          if not nom_utilisateur:
            str_lit.error("Merci d'indiquer un pseudo.")
          else:
            choix_clean = str(prono_1n2.split()[0])
            buteurs_texte_str = str(", ".join(buteurs_selectionnes))

            existing_idx = str_lit.session_state.pronos[
                (
                    str_lit.session_state.pronos["Participant"]
                    == str(nom_utilisateur)
                )
                & (str_lit.session_state.pronos["Match"] == str(match_choisi))
            ].index

            if not existing_idx.empty:
              idx = existing_idx[0]
              str_lit.session_state.pronos.loc[idx, "Prono (1N2)"] = choix_clean
              str_lit.session_state.pronos.loc[idx, "Score"] = str(prono_score)
              str_lit.session_state.pronos.loc[idx, "Buteur"] = buteurs_texte_str
              str_lit.session_state.pronos.loc[idx, "Doublé ?"] = str(
                  annonce_double
              )
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

      # --- SECTION : SUIVI DES PRONOS POUR CE MATCH ---
      str_lit.markdown("---")
      str_lit.subheader(f"📊 Suivi des pronos pour : {match_choisi}")

      tous_les_participants = obtenir_liste_participants()
      pronos_ce_match = (
          str_lit.session_state.pronos[
              str_lit.session_state.pronos["Match"] == match_choisi
          ]
          if not str_lit.session_state.pronos.empty
          and "Match" in str_lit.session_state.pronos.columns
          else pd.DataFrame()
      )
      participants_ayant_pronostique = (
          pronos_ce_match["Participant"].tolist()
          if not pronos_ce_match.empty
          and "Participant" in pronos_ce_match.columns
          else []
      )

      suivi_data = []
      for p in tous_les_participants:
        if p in participants_ayant_pronostique:
          suivi_data.append(
              {"Participant": p, "Statut": "✅ A pronostiqué 🎯"}
          )
        else:
          suivi_data.append({"Participant": p, "Statut": "❌ En attente ⏳"})

      df_suivi = pd.DataFrame(suivi_data)
      str_lit.dataframe(df_suivi, use_container_width=True)

  # --- HISTORIQUE FILTRÉ POUR N'AFFICHER QUE LE MATCH DU MOMENT ---
  if not str_lit.session_state.pronos.empty and "match_choisi" in locals():
    str_lit.markdown("---")
    str_lit.subheader(f"📋 Pronos enregistrés pour ce match ({match_choisi})")
    pronos_du_match_actuel = str_lit.session_state.pronos[
        str_lit.session_state.pronos["Match"] == match_choisi
    ]
    if not pronos_du_match_actuel.empty:
      colonnes_visibles = [
          col for col in pronos_du_match_actuel.columns if col != "Points"
      ]
      str_lit.dataframe(
          pronos_du_match_actuel[colonnes_visibles],
          use_container_width=True,
      )
    else:
      str_lit.info("Aucun prono enregistré pour ce match pour l'instant.")

# --- 2. CLASSEMENT ---
elif menu == "🏆 Classement":
  str_lit.header("🏆 Classement Général")
  calculer_points()

  p_pronos_sum = (
      str_lit.session_state.pronos.groupby("Participant")["Points"]
      .sum()
      .reset_index()
      if not str_lit.session_state.pronos.empty
      and "Participant" in str_lit.session_state.pronos.columns
      else pd.DataFrame(columns=["Participant", "Points"])
  )

  if not p_pronos_sum.empty or not str_lit.session_state.bonus.empty:
    classement_complet = pd.merge(
        p_pronos_sum, str_lit.session_state.bonus, on="Participant", how="outer"
    ).fillna(0)
    classement_complet["Points Total"] = classement_complet[
        "Points"
    ] + classement_complet["Points Bonus"].astype(int)

    classement_final = (
        classement_complet[["Participant", "Points Total"]]
        .rename(columns={"Points Total": "Points"})
        .sort_values(by="Points", ascending=False)
        .reset_index(drop=True)
    )
    classement_final.index += 1
    str_lit.dataframe(classement_final, use_container_width=True)
  else:
    str_lit.info("Le classement est vide pour le moment.")

# --- 3. PARTICIPANTS ---
elif menu == "👥 Participants":
  str_lit.header("👥 Liste des Participants")
  str_lit.write(
      "Participants enregistrés :", ", ".join(obtenir_liste_participants())
  )

# --- 4. ESPACE ADMIN ---
elif menu == "⚙️ Espace Admin":
  str_lit.header("⚙️ Espace Organisateur")
  mdp = str_lit.text_input("Mot de passe administrateur :", type="password")

  if mdp == MOT_DE_PASSE_ADMIN:
    str_lit.success("Accès autorisé !")

    tab_m, tab_res, tab_pts, tab_suppr = str_lit.tabs([
        "➕ Ajouter un Match",
        "🎯 Saisir les Résultats",
        "➕ Ajouter des points manuellement",
        "🗑️ Supprimer un Match",
    ])

    with tab_m:
      with str_lit.form("f_match"):
        id_m = str_lit.text_input("Nom du Match (ex: SMC - Bastia)")
        adv = str_lit.text_input("Adversaire")
        date_m = str_lit.date_input("Date du match")
        heure_m = str_lit.time_input("Heure du match")
        if str_lit.form_submit_button("Créer le match"):
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
            str_lit.session_state.matchs = pd.concat(
                [str_lit.session_state.matchs, new_m], ignore_index=True
            )
            sauvegarder_donnees()
            str_lit.success("Match créé avec succès !")
            str_lit.rerun()

    with tab_res:
      if str_lit.session_state.matchs.empty:
        str_lit.info("Aucun match à renseigner.")
      else:
        match_a_maj = str_lit.selectbox(
            "Sélectionner le match terminé",
            str_lit.session_state.matchs["ID Match"].tolist(),
        )
        match_ligne = str_lit.session_state.matchs[
            str_lit.session_state.matchs["ID Match"] == match_a_maj
        ].iloc[0]

        adversaire_nom = (
            str(match_ligne["Adversaire"]).strip()
            if "Adversaire" in match_ligne and str(match_ligne["Adversaire"])
            else "Adversaire"
        )

        with str_lit.form("f_resultat"):
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
          index_initial = (
              options_keys.index(res_actuel)
              if res_actuel in options_keys
              else 0
          )

          choix_res_form = str_lit.selectbox(
              "Vainqueur Réel",
              options_keys,
              format_func=lambda x: options_dict[x],
              index=index_initial,
          )

          score_reel = str_lit.text_input(
              "Score Réel exact (ex: 2-1)", value=score_actuel
          )
          str_lit.markdown("**Saisie des buteurs réels :**")

          buteurs_deja_la = [
              b.strip() for b in buteurs_actuels_str.split(",") if b.strip()
          ]
          options_buteurs_admin = ["Aucun"] + EFFECTIF_SMC

          def safe_index(val):
            return (
                options_buteurs_admin.index(val)
                if val in options_buteurs_admin
                else 0
            )

          buteur_1 = str_lit.selectbox(
              "1er but",
              options_buteurs_admin,
              index=safe_index(
                  buteurs_deja_la[0] if len(buteurs_deja_la) > 0 else "Aucun"
              ),
          )
          buteur_2 = str_lit.selectbox(
              "2e but",
              options_buteurs_admin,
              index=safe_index(
                  buteurs_deja_la[1] if len(buteurs_deja_la) > 1 else "Aucun"
              ),
          )
          buteur_3 = str_lit.selectbox(
              "3e but",
              options_buteurs_admin,
              index=safe_index(
                  buteurs_deja_la[2] if len(buteurs_deja_la) > 2 else "Aucun"
              ),
          )
          buteur_4 = str_lit.selectbox(
              "4e but",
              options_buteurs_admin,
              index=safe_index(
                  buteurs_deja_la[3] if len(buteurs_deja_la) > 3 else "Aucun"
              ),
          )
          buteur_5 = str_lit.selectbox(
              "5e but",
              options_buteurs_admin,
              index=safe_index(
                  buteurs_deja_la[4] if len(buteurs_deja_la) > 4 else "Aucun"
              ),
          )

          autre_buteur_precisions = str_lit.text_input(
              "Si 'Autre' sélectionné, précise le ou les noms ici :"
          )

          if str_lit.form_submit_button("Enregistrer les résultats et calculer"):
            liste_buts_brute = [
                buteur_1,
                buteur_2,
                buteur_3,
                buteur_4,
                buteur_5,
            ]
            liste_finale_buteurs = [b for b in liste_buts_brute if b != "Aucun"]
            buteurs_texte_final = ", ".join(liste_finale_buteurs)
            if autre_buteur_precisions.strip():
              if buteurs_texte_final:
                buteurs_texte_final += ", " + autre_buteur_precisions.strip()
              else:
                buteurs_texte_final = autre_buteur_precisions.strip()

            idx_m = str_lit.session_state.matchs[
                str_lit.session_state.matchs["ID Match"] == match_a_maj
            ].index[0]
            str_lit.session_state.matchs.loc[idx_m, "Résultat"] = str(
                choix_res_form
            )
            str_lit.session_state.matchs.loc[idx_m, "Score Réel"] = str(
                score_reel
            )
            str_lit.session_state.matchs.loc[idx_m, "Buteurs"] = str(
                buteurs_texte_final
            )

            calculer_points()
            sauvegarder_donnees()
            str_lit.success("Résultats enregistrés et points recalculés !")
            str_lit.rerun()

    with tab_pts:
      with str_lit.form("f_ajout_pts"):
        if (
            str_lit.session_state.bonus.empty
            or "Participant" not in str_lit.session_state.bonus.columns
            or "Points Bonus" not in str_lit.session_state.bonus.columns
        ):
          str_lit.session_state.bonus = pd.DataFrame(
              columns=["Participant", "Points Bonus"]
          )

        p_choisi = str_lit.selectbox(
            "Choisir le participant", obtenir_liste_participants()
        )
        pts_a_ajouter = str_lit.number_input(
            "Nombre de points à ajouter", value=0, step=1
        )
        if str_lit.form_submit_button("Valider et ajouter les points"):
          existing_b = str_lit.session_state.bonus[
              str_lit.session_state.bonus["Participant"] == p_choisi
          ].index
          if not existing_b.empty:
            str_lit.session_state.bonus.loc[
                existing_b[0], "Points Bonus"
            ] += int(pts_a_ajouter)
          else:
            new_b = pd.DataFrame(
                {"Participant": [p_choisi], "Points Bonus": [int(pts_a_ajouter)]}
            )
            str_lit.session_state.bonus = pd.concat(
                [str_lit.session_state.bonus, new_b], ignore_index=True
            )
          sauvegarder_donnees()
          str_lit.success(f"Points ajoutés avec succès pour {p_choisi} !")
          str_lit.rerun()

    with tab_suppr:
      if str_lit.session_state.matchs.empty:
        str_lit.info("Aucun match à supprimer.")
      else:
        match_a_supprimer = str_lit.selectbox(
            "Sélectionner le match à supprimer",
            str_lit.session_state.matchs["ID Match"].tolist(),
        )
        if str_lit.button(
            "🗑️ Supprimer définitivement ce match", type="primary"
        ):
          str_lit.session_state.matchs = str_lit.session_state.matchs[
              str_lit.session_state.matchs["ID Match"] != match_a_supprimer
          ]
          if not str_lit.session_state.pronos.empty:
            str_lit.session_state.pronos = str_lit.session_state.pronos[
                str_lit.session_state.pronos["Match"] != match_a_supprimer
            ]

          sauvegarder_donnees()
          str_lit.success(
              f"Le match '{match_a_supprimer}' a été supprimé avec succès !"
          )
          str_lit.rerun()

    str_lit.markdown("---")
    str_lit.subheader("Liste des matchs actuels")
    str_lit.dataframe(str_lit.session_state.matchs, use_container_width=True)

  elif mdp != "":
    str_lit.error("Mot de passe incorrect.")
