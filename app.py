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
    "Dennis Appiah",
    "Salim Diakité",
    "Mohamed Hafid",
    "Ivann Botella",
    "Armand Gnanduillet",
    "Fahd El Khoumisti",
]

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

# --- DESIGN & UI (Correction de la visibilité du texte dans le menu) ---
st.markdown("""
    <style>
    .stApp { background-color: #f4f6f9; color: #002D62; }
    h1 { color: #002D62 !important; font-weight: 800; text-transform: uppercase; }
    h2, h3, label, p { color: #002D62 !important; font-weight: 600; }
    .stButton > button { background-color: #E30613 !important; color: white !important; font-weight: bold !important; border-radius: 8px !important; }
    
    /* Style de la barre latérale pour forcer le texte en blanc lisible */
    [data-testid="stSidebar"] { background-color: #002D62; }
    [data-testid="stSidebar"] p, [data-testid="stSidebar"] span, [data-testid="stSidebar"] label, [data-testid="stSidebar"] .stRadio div { color: white !important; font-weight: 600; }
    </style>
""", unsafe_allow_html=True)

st.title("⚽ Concours de Pronos - SMC")

menu = st.sidebar.radio(
    "🧭 Navigation",
    ["📝 Faire mon Prono", "🏆 Classement", "⚙️ Espace Admin"],
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


if menu == "📝 Faire mon Prono":
  st.header("🎯 Enregistrer ton Pronostic")
  if st.session_state.matchs.empty:
    st.info("Aucun match ouvert pour l'instant.")
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

    col1, col2 = st.columns(2)
    with col1:
      prono_1n2 = st.selectbox(
          "1N2", ["1 (Victoire Caen)", "N (Nul)", "2 (Défaite)"]
      )
      prono_score = st.text_input("Score exact (ex: 2-0)")
    with col2:
      buteurs_selectionnes = st.multiselect("Buteurs", EFFECTIF_SMC)

    annonce_double = st.selectbox(
        "Doublé ?", ["Aucun"] + buteurs_selectionnes
    )

    if st.button("Valider 🚀"):
      if nom_utilisateur and buteurs_selectionnes:
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

        st.success("Prono enregistré !")
        st.rerun()

  if not st.session_state.pronos.empty:
    st.dataframe(st.session_state.pronos, use_container_width=True)

elif menu == "🏆 Classement":
  st.header("🏆 Classement Général")
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
        classement_complet[["Participant", "Points Total"]]
        .sort_values(by="Points Total", ascending=False)
        .reset_index(drop=True)
    )
    classement_final.index += 1
    st.dataframe(classement_final, use_container_width=True)
  else:
    st.info("Classement vide.")

elif menu == "⚙️ Espace Admin":
  st.header("🔐 Espace Organisateur")
  mdp = st.text_input("Mot de passe :", type="password")
  if mdp == MOT_DE_PASSE_ADMIN:
    st.success("Connecté !")
    with st.form("f_match"):
      id_m = st.text_input("Nom du Match (ex: SMC - Bastia)")
      adv = st.text_input("Adversaire")
      res = st.selectbox("Résultat Réel", ["", "1", "N", "2"])
      sc_r = st.text_input("Score Réel (ex: 2-1)")
      but_r = st.text_input("Buteurs réels")
      if st.form_submit_button("Enregistrer Match"):
        if id_m:
          st.session_state.matchs = pd.concat(
              [
                  st.session_state.matchs,
                  pd.DataFrame({
                      "ID Match": [id_m],
                      "Adversaire": [adv],
                      "Date": ["2026-08-25"],
                      "Heure": ["20:00"],
                      "Résultat": [res],
                      "Score Réel": [sc_r],
                      "Buteurs": [but_r],
                  }),
              ],
              ignore_index=True,
          )
          st.success("Match ajouté !")
          st.rerun()
    st.dataframe(st.session_state.matchs, use_container_width=True)
  elif mdp != "":
    st.error("Mot de passe incorrect.")
