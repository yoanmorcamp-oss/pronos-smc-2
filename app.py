import gspread
import pandas as pd
import streamlit as str_lit

# --- CONFIGURATION DE LA PAGE ---
str_lit.set_page_config(
    page_title="Pronos SMC 2026-2027", page_icon="⚽", layout="wide"
)

# URL de ton Google Sheet
GOOGLE_SHEET_URL = (
    "https://docs.google.com/spreadsheets/d/1LMP1ELnq3e-gaM1QQHQq6SDZRhQkRUs52SM8T3OfmGI/edit?usp=sharing"  # Remplace par ton URL exacte si besoin
)


# --- CONNEXION SIMPLIFIÉE GSPREAD ---
def obtenir_feuille():
  gc = gspread.no_authorization()
  return gc.open_by_url(GOOGLE_SHEET_URL)


def charger_donnees_gsheets():
  try:
    sh = obtenir_feuille()
    df_matchs = pd.DataFrame(sh.worksheet("matchs").get_all_records())
    df_pronos = pd.DataFrame(sh.worksheet("pronos").get_all_records())
    df_bonus = pd.DataFrame(sh.worksheet("bonus").get_all_records())

    # Sécurité si les onglets sont vides (garde les en-têtes)
    if df_matchs.empty:
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
    if df_pronos.empty:
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
    if df_bonus.empty:
      df_bonus = pd.DataFrame(columns=["Participant", "Points Bonus"])

    return df_matchs, df_pronos, df_bonus
  except Exception as e:
    str_lit.error(f"Erreur de lecture : {e}")
    return (
        pd.DataFrame(
            columns=[
                "ID Match",
                "Adversaire",
                "Date",
                "Heure",
                "Résultat",
                "Score Réel",
                "Buteurs",
            ]
        ),
        pd.DataFrame(
            columns=[
                "Participant",
                "Match",
                "Prono (1N2)",
                "Score",
                "Buteur",
                "Doublé ?",
                "Points",
            ]
        ),
        pd.DataFrame(columns=["Participant", "Points Bonus"]),
    )


def sauvegarder_donnees_gsheets():
  try:
    sh = obtenir_feuille()

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
    str_lit.error(f"Erreur de sauvegarde : {e}")


# --- INITIALISATION DE LA SESSION ---
if "matchs" not in str_lit.session_state or "pronos" not in str_lit.session_state:
  df_m, df_p, df_b = charger_donnees_gsheets()
  str_lit.session_state.matchs = df_m
  str_lit.session_state.pronos = df_p
  str_lit.session_state.bonus = df_b

# --- BARRE LATÉRALE (NAVIGATION) ---
str_lit.sidebar.title("⚽ Pronos SMC")
menu = str_lit.sidebar.selectbox(
    "Navigation",
    ["Classement Général", "Calendrier & Pronos", "Règlement", "⚙️ Espace Admin"],
)

# --- 1. CLASSEMENT GÉNÉRAL ---
if menu == "Classement Général":
  str_lit.title("🏆 Classement Général des Pronostiqueurs")
  str_lit.write("Voici le classement mistez en temps réel :")

  # Calcul des points totaux par participant
  df_pronos = str_lit.session_state.pronos
  df_bonus = str_lit.session_state.bonus

  if not df_pronos.empty and "Points" in df_pronos.columns:
    classement_pronos = df_pronos.groupby("Participant")["Points"].sum().reset_index()
  else:
    classement_pronos = pd.DataFrame(columns=["Participant", "Points"])

  if not df_bonus.empty and "Points Bonus" in df_bonus.columns:
    classement_bonus = df_bonus.groupby("Participant")["Points Bonus"].sum().reset_index()
    classement_general = pd.merge(classement_pronos, classement_bonus, on="Participant", how="outer").fillna(0)
    classement_general["Total"] = classement_general["Points"] + classement_general["Points Bonus"]
  else:
    classement_general = classement_pronos
    if not classement_general.empty:
      classement_general["Total"] = classement_general["Points"]

  if not classement_general.empty:
    classement_general = classement_general.sort_values(by="Total", ascending=False).reset_index(drop=True)
    str_lit.dataframe(classement_general, use_container_width=True)
  else:
    str_lit.info("Aucun point enregistré pour le moment.")

# --- 2. CALENDRIER & PRONOS ---
elif menu == "Calendrier & Pronos":
  str_lit.title("📅 Calendrier des Matchs & Saisie des Pronos")
  
  df_matchs = str_lit.session_state.matchs
  if not df_matchs.empty:
    str_lit.subheader("Liste des matchs de la saison")
    str_lit.dataframe(df_matchs, use_container_width=True)

    str_lit.markdown("---")
    str_lit.subheader("Faire un pronostic")
    with str_lit.form("form_prono"):
      participant = str_lit.text_input("Ton Nom / Pseudo")
      match_choisi = str_lit.selectbox("Sélectionne le match", df_matchs["ID Match"].tolist())
      prono_1n2 = str_lit.selectbox("Pronostic (1N2)", ["1", "N", "2"])
      score_exact = str_lit.text_input("Score exact (ex: 2-1)")
      buteur = str_lit.text_input("Buteur pressenti")
      double = str_lit.checkbox("Doublé de ce buteur ?")

      submit_prono = str_lit.form_submit_button("Valider mon Prono")

      if submit_prono:
        if participant:
          nouveau_prono = pd.DataFrame({
              "Participant": [participant],
              "Match": [match_choisi],
              "Prono (1N2)": [prono_1n2],
              "Score": [score_exact],
              "Buteur": [buteur],
              "Doublé ?": ["Oui" if double else "Non"],
              "Points": [0]
          })
          str_lit.session_state.pronos = pd.concat([str_lit.session_state.pronos, nouveau_prono], ignore_index=True)
          sauvegarder_donnees_gsheets()
          str_lit.success(f"Prono enregistré avec succès pour {participant} !")
        else:
          str_lit.error("Veuillez renseigner votre nom.")
  else:
    str_lit.warning("Aucun match disponible pour le moment. Contactez l'administrateur.")

# --- 3. RÈGLEMENT ---
elif menu == "Règlement":
  str_lit.title("📜 Règlement du Concours de Pronos")
  str_lit.markdown("""
  Bienvenue dans le concours de pronostics officiel ! Voici les règles d'attribution des points :
  * **1N2 (Résultat du match)** : X points
  * **Score exact** : X points
  * **Buteur trouvé** : X points
  * **Doublé du buteur** : Points bonus
  """)

# --- 4. ESPACE ADMIN ---
elif menu == "⚙️ Espace Admin":
  str_lit.title("🔐 Espace Administration")

  # Mot de passe simple
  mdp = str_lit.text_input("Mot de passe admin", type="password")
  if mdp == "smc2026":  # Tu pourras changer ce mot de passe
    str_lit.success("Accès autorisé !")

    # Bouton de rechargement manuel
    if str_lit.button("🔄 Recharger les données depuis Google Sheets", type="primary"):
      df_m, df_p, df_b = charger_donnees_gsheets()
      str_lit.session_state.matchs = df_m
      str_lit.session_state.pronos = df_p
      str_lit.session_state.bonus = df_b
      str_lit.rerun()

    tab1, tab2, tab3 = str_lit.tabs(["➕ Ajouter un Match", "🎯 Saisir les Résultats", "➕ Ajouter des points manuellement"])

    with tab1:
      str_lit.subheader("Créer un nouveau match")
      with str_lit.form("form_match"):
        id_match = str_lit.text_input("Nom du Match (ex: SMC - Bastia)")
        adversaire = str_lit.text_input("Adversaire")
        date_match = str_lit.date_input("Date du match")
        heure_match = str_lit.time_input("Heure du match")

        submit_match = str_lit.form_submit_button("Créer le match")
        if submit_match and id_match:
          nouveau_match = pd.DataFrame({
              "ID Match": [id_match],
              "Adversaire": [adversaire],
              "Date": [str(date_match)],
              "Heure": [str(heure_match)],
              "Résultat": [""],
              "Score Réel": [""],
              "Buteurs": [""]
          })
          str_lit.session_state.matchs = pd.concat([str_lit.session_state.matchs, nouveau_match], ignore_index=True)
          sauvegarder_donnees_gsheets()
          str_lit.success(f"Match '{id_match}' créé et enregistré !")

    with tab2:
      str_lit.subheader("Saisir le résultat d'un match joué")
      df_matchs = str_lit.session_state.matchs
      if not df_matchs.empty:
        match_selectionne = str_lit.selectbox("Choisir le match terminé", df_matchs["ID Match"].tolist())
        score_reel = str_lit.text_input("Score Réel (ex: 2-0)")
        resultat_1n2 = str_lit.selectbox("Résultat 1N2", ["1", "N", "2"])
        buteurs_reels = str_lit.text_input("Buteurs du match")

        if str_lit.button("Enregistrer le résultat"):
          # Mise à jour du match dans le dataframe
          idx = str_lit.session_state.matchs[str_lit.session_state.matchs["ID Match"] == match_selectionne].index
          if not idx.empty:
            str_lit.session_state.matchs.loc[idx, "Score Réel"] = score_reel
            str_lit.session_state.matchs.loc[idx, "Résultat"] = resultat_1n2
            str_lit.session_state.matchs.loc[idx, "Buteurs"] = buteurs_reels
            sauvegarder_donnees_gsheets()
            str_lit.success("Résultat enregistré avec succès !")

    with tab3:
      str_lit.subheader("Ajout de points bonus")
      with str_lit.form("form_bonus"):
        participant_bonus = str_lit.text_input("Nom du participant")
        points_bonus = str_lit.number_input("Points Bonus", value=0, step=1)
        submit_bonus = str_lit.form_submit_button("Ajouter le bonus")

        if submit_bonus and participant_bonus:
          nouveau_b = pd.DataFrame({
              "Participant": [participant_bonus],
              "Points Bonus": [points_bonus]
          })
          str_lit.session_state.bonus = pd.concat([str_lit.session_state.bonus, nouveau_b], ignore_index=True)
          sauvegarder_donnees_gsheets()
          str_lit.success("Bonus ajouté avec succès !")

    str_lit.markdown("---")
    str_lit.subheader("Liste des matchs actuels")
    str_lit.dataframe(str_lit.session_state.matchs, use_container_width=True)

  elif mdp != "":
    str_lit.error("Mot de passe incorrect.")
