from datetime import datetime
import pandas as pd
import gspread
import streamlit as str_lit
from zoneinfo import ZoneInfo

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

# ⚠️ Vérifie bien que ton URL est entre ces guillemets
GOOGLE_SHEET_URL = (
    "https://docs.google.com/spreadsheets/d/1LMP1ELnq3e-gaM1QQHQq6SDZRhQkRUs52SM8T3OfmGI/edit?usp=sharing"
)

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


# --- CONNEXION DIRECTE GSPREAD AVEC PARTAGE PUBLIC ---
def charger_donnees_gsheets():
  try:
    gc = gspread.no_authorization()
    sh = gc.open_by_url(GOOGLE_SHEET_URL)

    # Chargement Matchs
    ws_matchs = sh.worksheet("matchs")
    data_matchs = ws_matchs.get_all_records()
    df_matchs = (
        pd.DataFrame(data_matchs)
        if data_matchs
        else pd.DataFrame(
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
    )

    # Chargement Pronos
    ws_pronos = sh.worksheet("pronos")
    data_pronos = ws_pronos.get_all_records()
    df_pronos = (
        pd.DataFrame(data_pronos)
        if data_pronos
        else pd.DataFrame(
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
    )

    # Chargement Bonus
    ws_bonus = sh.worksheet("bonus")
    data_bonus = ws_bonus.get_all_records()
    df_bonus = (
        pd.DataFrame(data_bonus)
        if data_bonus
        else pd.DataFrame(columns=["Participant", "Points Bonus"])
    )

    return df_matchs, df_pronos, df_bonus
  except Exception as e:
    str_lit.error(f"Erreur de lecture Google Sheets : {e}")
    df_m = pd.DataFrame(
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
    df_p = pd.DataFrame(
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
    df_b = pd.DataFrame(columns=["Participant", "Points Bonus"])
    return df_m, df_p, df_b


def sauvegarder_donnees_gsheets():
  try:
    gc = gspread.no_authorization()
    sh = gc.open_by_url(GOOGLE_SHEET_URL)

    if "matchs" in str_lit.session_state:
      ws = sh.worksheet("matchs")
      ws.clear()
      df = str_lit.session_state.matchs
      if not df.empty:
        ws.update([df.columns.values.tolist()] + df.values.tolist())

    if "pronos" in str_lit.session_state:
      ws = sh.worksheet("pronos")
      ws.clear()
      df = str_lit.session_state.pronos
      if not df.empty:
        ws.update([df.columns.values.tolist()] + df.values.tolist())

    if "bonus" in str_lit.session_state:
      ws = sh.worksheet("bonus")
      ws.clear()
      df = str_lit.session_state.bonus
      if not df.empty:
        ws.update([df.columns.values.tolist()] + df.values.tolist())
  except Exception as e:
    str_lit.error(f"Erreur de sauvegarde Google Sheets : {e}")


def calculer_points():
  if (
      "pronos" not in str_lit.session_state
      or str_lit.session_state.pronos.empty
      or "matchs" not in str_lit.session_state
      or str_lit.session_state.matchs.empty
  ):
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

      if res_reel and prono_1n2 == res_reel:
        points += 2
      if score_reel and prono_score == score_reel:
        points += 10

      buteurs_choisis = [
          b.strip() for b in p_buteur.split(",") if b.strip() and b != "nan"
      ]
      for b in buteurs_choisis:
        b_lower = b.lower()
        if b_lower in compteur_buts_reels and compteur_buts_reels[b_lower] > 0:
          points += 3

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

  sauvegarder_donnees_gsheets()


# Chargement initial
if "donnees_chargees" not in str_lit.session_state:
  m_load, p_load, b_load = charger_donnees_gsheets()
  str_lit.session_state.matchs = m_load
  str_lit.session_state.pronos = p_load
  str_lit.session_state.bonus = b_load
  str_lit.session_state.donnees_chargees = True

calculer_points()

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


if menu == "📝 Faire mon Prono":
  str_lit.header("✍️ Enregistrer ton Pronostic")

  if str_lit.session_state.matchs.empty:
    str_lit.warning(
        "⚠️ Aucun match trouvé. Va dans l'Espace Admin pour vérifier ou force"
        " la synchronisation !"
    )
  else:
    with str_lit.expander("📅 Voir les détails des matchs enregistrés"):
      str_lit.dataframe(
          str_lit.session_state.matchs, use_container_width=True
      )

    matchs_disponibles = str_lit.session_state.matchs["ID Match"].tolist()
    choix_participant = str_lit.selectbox(
        "Pseudo", obtenir_liste_participants() + ["➕ Nouveau"]
    )
    nom_utilisateur = (
        str_lit.text_input("Nouveau pseudo :")
        if choix_participant == "➕ Nouveau"
        else choix_participant
    )
    match_choisi = str_lit.selectbox("Sélectionne le match", matchs_disponibles)

    match_ligne = str_lit.session_state.matchs[
        str_lit.session_state.matchs["ID Match"] == match_choisi
    ].iloc[0]
    date_str = str(match_ligne["Date"]).strip()
    heure_str = str(match_ligne["Heure"]).strip()

    match_verrouille = False
    try:
      tz_paris = ZoneInfo("Europe/Paris")
      maintenant = datetime.now(tz_paris)
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
        verification_actuelle = False
        try:
          tz_paris = ZoneInfo("Europe/Paris")
          maintenant = datetime.now(tz_paris)
          match_datetime = datetime.strptime(
              f"{date_str} {heure_str}", "%Y-%m-%d %H:%M"
          ).replace(tzinfo=tz_paris)
          if maintenant >= match_datetime:
            verification_actuelle = True
        except Exception:
          if datetime.now() >= datetime.strptime(
              f"{date_str} {heure_str}", "%Y-%m-%d %H:%M"
          ):
            verification_actuelle = True

        if verification_actuelle:
          str_lit.error(
              "❌ Impossible de valider : le match a déjà commencé ou l'heure"
              " est dépassée !"
          )
        elif not nom_utilisateur:
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
          sauvegarder_donnees_gsheets()
          str_lit.success("Prono enregistré avec succès !")
          str_lit.rerun()

  if not str_lit.session_state.pronos.empty:
    str_lit.subheader("📋 Tous les pronos enregistrés")
    colonnes_visibles = [
        col for col in str_lit.session_state.pronos.columns if col != "Points"
    ]
    str_lit.dataframe(
        str_lit.session_state.pronos[colonnes_visibles],
        use_container_width=True,
    )

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

elif menu == "👥 Participants":
  str_lit.header("👥 Liste des Participants")
  str_lit.write(
      "Participants enregistrés :", ", ".join(obtenir_liste_participants())
  )

elif menu == "⚙️ Espace Admin":
  str_lit.header("⚙️ Espace Organisateur")
  mdp = str_lit.text_input("Mot de passe administrateur :", type="password")

  if mdp == MOT_DE_PASSE_ADMIN:
    str_lit.success("Accès autorisé !")

    # Bouton magique pour forcer la synchronisation avec le Google Sheet
    if str_lit.button("🔄 Recharger les données depuis Google Sheets"):
      m_load, p_load, b_load = charger_donnees_gsheets()
      str_lit.session_state.matchs = m_load
      str_lit.session_state.pronos = p_load
      str_lit.session_state.bonus = b_load
      str_lit.success("Données rechargées avec succès depuis Google Sheets !")
      str_lit.rerun()

    tab_m, tab_res, tab_pts = str_lit.tabs([
        "➕ Ajouter un Match",
        "🎯 Saisir les Résultats",
        "➕ Ajouter des points manuellement",
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
            sauvegarder_donnees_gsheets()
            str_lit.success("Match créé et sauvegardé dans Google Sheets !")
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

          index_initial = 0
          if res_actuel in options_keys:
            index_initial = options_keys.index(res_actuel)

          choix_res_form = str_lit.selectbox(
              "Vainqueur Réel",
              options_keys,
              format_func=lambda x: options_dict[x],
              index=index_initial,
          )

          score_reel = str_lit.text_input(
              "Score Réel exact (ex: 2-1)", value=score_actuel
          )

          str_lit.markdown(
              "**Saisie des buteurs réels (jusqu'à 5 buts via listes"
              " déroulantes) :**"
          )

          buteurs_deja_la = [
              b.strip() for b in buteurs_actuels_str.split(",") if b.strip()
          ]
          b1_def = buteurs_deja_la[0] if len(buteurs_deja_la) > 0 else "Aucun"
          b2_def = buteurs_deja_la[1] if len(buteurs_deja_la) > 1 else "Aucun"
          b3_def = buteurs_deja_la[2] if len(buteurs_deja_la) > 2 else "Aucun"
          b4_def = buteurs_deja_la[3] if len(buteurs_deja_la) > 3 else "Aucun"
          b5_def = buteurs_deja_la[4] if len(buteurs_deja_la) > 4 else "Aucun"

          options_buteurs_admin = ["Aucun"] + EFFECTIF_SMC

          def safe_index(val, opts):
            return opts.index(val) if val in opts else 0

          buteur_1 = str_lit.selectbox(
              "1er but",
              options_buteurs_admin,
              index=safe_index(b1_def, options_buteurs_admin),
          )
          buteur_2 = str_lit.selectbox(
              "2e but",
              options_buteurs_admin,
              index=safe_index(b2_def, options_buteurs_admin),
          )
          buteur_3 = str_lit.selectbox(
              "3e but",
              options_buteurs_admin,
              index=safe_index(b3_def, options_buteurs_admin),
          )
          buteur_4 = str_lit.selectbox(
              "4e but",
              options_buteurs_admin,
              index=safe_index(b4_def, options_buteurs_admin),
          )
          buteur_5 = str_lit.selectbox(
              "5e but",
              options_buteurs_admin,
              index=safe_index(b5_def, options_buteurs_admin),
          )

          autre_buteur_precisions = str_lit.text_input(
              "Si 'Autre' sélectionné ci-dessus, précise le ou les noms ici"
              " (séparés par des virgules) :"
          )

          if str_lit.form_submit_button("Enregistrer les résultats et calculer"):
            liste_buts_brute = [
                buteur_1,
                buteur_2,
                buteur_3,
                buteur_4,
                buteur_5,
            ]
            liste_finale_buteurs = []

            for b in liste_buts_brute:
              if b and b != "Aucun":
                liste_finale_buteurs.append(b)

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
            sauvegarder_donnees_gsheets()
            str_lit.success(
                "Résultats enregistrés, points recalculés et sauvegardés dans"
                " le Cloud !"
            )
            str_lit.rerun()

    with tab_pts:
      str_lit.write(
          "Ici, tu peux ajouter des points aux participants (par exemple, pour"
          " les matchs d'avant l'application)."
      )
      with str_lit.form("f_ajout_pts"):
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
          sauvegarder_donnees_gsheets()
          str_lit.success(f"Points ajoutés avec succès pour {p_choisi} !")
          str_lit.rerun()

    str_lit.markdown("---")
    str_lit.subheader("Liste des matchs actuels")
    str_lit.dataframe(str_lit.session_state.matchs, use_container_width=True)

    if not str_lit.session_state.matchs.empty:
      str_lit.markdown("---")
      str_lit.subheader("🗑️ Supprimer un Match")
      match_a_supprimer = str_lit.selectbox(
          "Choisir le match à supprimer",
          str_lit.session_state.matchs["ID Match"].tolist(),
          key="select_suppr_match",
      )
      if str_lit.button("Supprimer ce match définitivement ?"):
        str_lit.session_state.matchs = str_lit.session_state.matchs[
            str_lit.session_state.matchs["ID Match"] != match_a_supprimer
        ].reset_index(drop=True)

        if not str_lit.session_state.pronos.empty:
          str_lit.session_state.pronos = str_lit.session_state.pronos[
              str_lit.session_state.pronos["Match"] != match_a_supprimer
          ].reset_index(drop=True)

        calculer_points()
        sauvegarder_donnees_gsheets()
        str_lit.success(
            f"Le match '{match_a_supprimer}' et ses pronos associés ont bien"
            " été supprimés !"
        )
        str_lit.rerun()

  elif mdp != "":
    str_lit.error("Mot de passe incorrect.")
