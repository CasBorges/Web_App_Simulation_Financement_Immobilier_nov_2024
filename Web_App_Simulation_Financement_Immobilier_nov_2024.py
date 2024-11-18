import streamlit as st
import pandas as pd
import numpy_financial as npf
import plotly.graph_objects as go
from PIL import Image
import base64
from io import BytesIO
from fpdf import FPDF
import locale

# Définir le format local pour l'affichage des nombres
try:
    locale.setlocale(locale.LC_NUMERIC, 'French_France')
except locale.Error:
    print("Impossible de définir la locale française, la locale par défaut du système sera utilisée.")

def format_number_fr(number):
    """
    Formate un nombre en utilisant une virgule comme séparateur décimal
    et un espace comme séparateur des milliers, sans dépendre de locale.
    """
    # Formater avec deux décimales et un séparateur des milliers
    return f"{number:,.2f}".replace(',', ' ').replace('.', ',')

# Fonction pour convertir l'image en base64
def get_image_base64(image_path):
    """
    Cette fonction lit une image et la convertit en format base64 pour
    pouvoir l'afficher dans un contexte HTML.
    """
    with open(image_path, "rb") as img_file:
        return base64.b64encode(img_file.read()).decode()

# Charger l'image du logo
logo_path = "1_Logo.png"  # Assurez-vous que le logo est dans le même dossier que ce script
logo_image = Image.open(logo_path)
logo_base64 = get_image_base64(logo_path)

# Appliquer le fond d'écran à toute la page
st.markdown(
    """
    <style>
    .stApp {
        background-color: #F4F1E8;
    }
    body, h1, h2, h3, h4, h5, h6, p, label {
        color: #9B4819;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# En-tête avec logo, titre, description, et ligne de séparation
st.markdown(
    f"""
    <style>
    .header {{
        text-align: center;
        padding: 10px;
        background-color: #F4F1E8;
        border-bottom: 2px solid gray;
        margin-bottom: 20px;
    }}
    .header h1 {{
        color: #9B4819;
        margin-bottom: 0;
    }}
    .description {{
        color: #0C141A;
        margin-top: 5px;
    }}
    .header img {{
        margin-bottom: 10px;
    }}
    </style>
    <div class='header'>
        <img src='data:image/png;base64,{logo_base64}' alt='Logo' width='150'>
        <h1>Simulation de financement immobilier</h1>
        <p class='description'>Cette application vous permet de simuler votre financement immobilier en fonction de divers paramètres financiers.</p>
    </div>
    """,
    unsafe_allow_html=True
)

# Fonction pour afficher la barre de progression
def afficher_barre_progression(step, total_steps):
    """
    Cette fonction affiche une barre de progression en fonction de l'étape actuelle et du nombre total d'étapes.
    """
    progress = (step - 1) / total_steps
    if step >= total_steps:  # Lorsque l'utilisateur arrive au PEL, la barre est complètement pleine
        progress = 1.0
    st.progress(progress)

# Fonction pour réinitialiser les calculs
def reset_calculs():
    """
    Réinitialise tous les calculs en supprimant les valeurs enregistrées dans la session.
    """
    for key in st.session_state.keys():
        if key.startswith("step_") or key in ['recap', 'revenu_annuel', 'valeur_bien', 'apport_personnel', 'taux_interet', 'duree_pret', 'assurance_emprunteur_annuelle', 'frais_de_notaire', 'frais_de_garantie', 'frais_de_dossier', 'frais_de_courtage', 'frais_agence_immobiliere', 'ptz', 'pel']:
            del st.session_state[key]
    st.session_state.step = 1

# Fonction pour afficher l'entrée et valider l'étape
def afficher_et_valider_etape(texte, valeur_par_defaut, etape, min_value=None, max_value=None):
    """
    Affiche un champ de saisie pour l'utilisateur et permet de valider cette étape.
    Utilise la validation pour vérifier que l'entrée est correcte.
    """

    # Convertir min_value et max_value pour correspondre au type de valeur_par_defaut
    if isinstance(valeur_par_defaut, float):
        if min_value is not None:
            min_value = float(min_value)
        if max_value is not None:
            max_value = float(max_value)
    elif isinstance(valeur_par_defaut, int):
        if min_value is not None:
            min_value = int(min_value)
        if max_value is not None:
            max_value = int(max_value)

    # Définir le pas en fonction du type de valeur_par_defaut
    step = 0.01 if isinstance(valeur_par_defaut, float) else 1

    # S'assurer que value, min_value, max_value, et step sont du même type
    valeur = st.number_input(
        texte,
        value=valeur_par_defaut,
        min_value=min_value,
        max_value=max_value,
        step=step,
        key=f"{etape}_input"
    )

    # Vérifier si l'étape a été validée
    if st.session_state.get(f"step_{etape}_valid", False):
        return valeur, True
    if st.button("Valider", key=f"{etape}_valider"):
        st.session_state[f"step_{etape}_valid"] = True
        return valeur, True
    return valeur, False

# Fonction principale pour la simulation de financement
def simuler_financement_avec_calculs_et_recommandations():
    """
    Simule le financement immobilier en calculant les différents coûts et en renvoyant un DataFrame avec les résultats.
    Utilisation de la mise en cache pour améliorer les performances.
    """
    revenu_annuel = st.session_state.revenu_annuel
    valeur_bien = st.session_state.valeur_bien
    apport = st.session_state.apport_personnel
    taux_interet = st.session_state.taux_interet / 100
    duree_pret_annees = st.session_state.duree_pret
    assurance_annuelle = st.session_state.assurance_emprunteur_annuelle
    frais_notaire = st.session_state.frais_de_notaire
    frais_garantie = st.session_state.frais_de_garantie
    frais_dossier = st.session_state.frais_de_dossier
    frais_courtage = st.session_state.frais_de_courtage
    frais_agence = st.session_state.frais_agence_immobiliere
    ptz = st.session_state.ptz
    pel = st.session_state.pel

    montant_pret = valeur_bien - apport
    cout_total_frais = round(frais_notaire + frais_garantie + frais_dossier + frais_courtage + frais_agence + assurance_annuelle * duree_pret_annees, 2)
    montant_total_finance = round(montant_pret + cout_total_frais - ptz - pel, 2)

    taux_interet_mensuel = taux_interet / 12
    duree_pret_mois = duree_pret_annees * 12
    assurance_mensuelle = round(assurance_annuelle / 12, 2)

    mensualite = round(npf.pmt(taux_interet_mensuel, duree_pret_mois, -montant_total_finance), 2) if taux_interet_mensuel > 0 else round(montant_total_finance / duree_pret_mois, 2)
    
    mensualite_totale = round(mensualite + assurance_mensuelle, 2)
    paiement_total = round((mensualite * duree_pret_mois) + assurance_annuelle * duree_pret_annees, 2)
    interet_total = round(paiement_total - montant_pret, 2)
    revenu_mensuel = round(revenu_annuel / 12, 2)
    taux_endettement = round((mensualite_totale / revenu_mensuel) * 100, 2)
    
    df_resultats = pd.DataFrame({
        "Description": [
            "Revenu annuel avant impôt", "Valeur du bien/ prix d'achat", "Apport personnel", 
            "Frais de notaire", "Frais de garantie", "Frais de dossier", 
            "Frais de courtage", "Frais d'agence immobilière", 
            "Assurance emprunteur annuelle", "Assurance emprunteur totale", 
            "PTZ", "PEL", "Taux d'intérêt", 
            "Durée du prêt (années)", "Paiement total", 
            "Intérêts totaux", "Mensualité hors assurance", 
            "Mensualité avec assurance", "Montant total financé", 
            "Taux d'endettement (mensualité avec assurance)"
        ],
        "Valeur": [
            f"{format_number_fr(revenu_annuel)} €", 
            f"{format_number_fr(valeur_bien)} €", 
            f"{format_number_fr(apport)} €", 
            f"{format_number_fr(frais_notaire)} €", 
            f"{format_number_fr(frais_garantie)} €", 
            f"{format_number_fr(frais_dossier)} €", 
            f"{format_number_fr(frais_courtage)} €", 
            f"{format_number_fr(frais_agence)} €", 
            f"{format_number_fr(assurance_annuelle)} €", 
            f"{format_number_fr(assurance_annuelle * duree_pret_annees)} €", 
            f"{format_number_fr(ptz)} €", 
            f"{format_number_fr(pel)} €", 
            f"{format_number_fr(taux_interet * 100)} %", 
            f"{duree_pret_annees} ans", 
            f"{format_number_fr(paiement_total)} €", 
            f"{format_number_fr(interet_total)} €", 
            f"{format_number_fr(mensualite)} €", 
            f"{format_number_fr(mensualite_totale)} €", 
            f"{format_number_fr(montant_total_finance)} €", 
            f"Prédiction du taux estimé à {format_number_fr(taux_endettement)} %"
        ]
    })
    
    return df_resultats

# Fonction pour actualiser le financement avec la nouvelle mensualité souhaitée
def actualiser_financement(df_resultats, nouvelle_mensualite):
    # Obtenir les valeurs nécessaires depuis les résultats actuels
    valeur_bien_str = df_resultats.loc[df_resultats["Description"] == "Valeur du bien/ prix d'achat", "Valeur"].values[0].replace(' €', '').replace('\xa0', '').replace(',', '.')
    valeur_bien = float(valeur_bien_str.replace(' ', ''))

    mensualite_avec_assurance_str = df_resultats.loc[df_resultats["Description"] == "Mensualité avec assurance", "Valeur"].values[0].replace(' €', '').replace('\xa0', '').replace(',', '.')
    mensualite_avec_assurance = float(mensualite_avec_assurance_str.replace(' ', ''))

    # Récupérer le taux d'intérêt et la durée du prêt
    taux_interet_str = df_resultats.loc[df_resultats["Description"] == "Taux d'intérêt", "Valeur"].values[0].replace(' %', '').replace(',', '.')
    taux_interet = float(taux_interet_str) / 100

    duree_pret_annees_str = df_resultats.loc[df_resultats["Description"] == "Durée du prêt (années)", "Valeur"].values[0].replace(' ans', '').strip()
    duree_pret_annees = int(duree_pret_annees_str)

    # Calcul de la nouvelle valeur du bien en utilisant la règle de trois
    valeur_bien_recommande = round((nouvelle_mensualite / mensualite_avec_assurance) * valeur_bien, 2)

    # Calcul du nouveau taux d'endettement
    revenu_annuel_str = df_resultats.loc[df_resultats["Description"] == "Revenu annuel avant impôt", "Valeur"].values[0].replace(' €', '').replace('\xa0', '').replace(',', '.')
    revenu_annuel = float(revenu_annuel_str.replace(' ', ''))
    revenu_mensuel = revenu_annuel / 12
    nouveau_taux_endettement = round((nouvelle_mensualite / revenu_mensuel) * 100, 2)

    # Mise à jour du tableau des résultats
    df_resultats_actualise = pd.DataFrame({
        "Description": [
            "Mensualité souhaitée avec assurance", 
            "Nouvelle valeur du bien recommandée",
            "Nouveau taux d'endettement recommandé",
            "Taux d'intérêt", 
            "Durée du prêt (années)"
        ],
        "Valeur": [
            f"{format_number_fr(nouvelle_mensualite)} €", 
            f"{format_number_fr(valeur_bien_recommande)} €",
            f"{format_number_fr(nouveau_taux_endettement)} %",
            f"{format_number_fr(taux_interet * 100)} %", 
            f"{duree_pret_annees} ans"
        ]
    })

    return df_resultats_actualise

# Fonction pour tracer le graphique de comparaison des mensualités en courbe
def tracer_graphique_comparaison_mensualites_courbe(mensualite_actuelle, valeur_bien_actuelle):
    # Mensualités croissantes et décroissantes avec un écart de 20 €
    mensualites = [mensualite_actuelle + i * 20 for i in range(-10, 11)]
    valeurs_bien = [round((mensualite / mensualite_actuelle) * valeur_bien_actuelle, 2) for mensualite in mensualites]

    fig = go.Figure()

    # Ajouter la courbe des mensualités
    fig.add_trace(go.Scatter(
        x=mensualites,
        y=valeurs_bien,
        mode='lines+markers',
        name="Comparaison des mensualités",
        line=dict(color="blue", width=2),
        marker=dict(size=10, color="blue")
    ))

    # Ajouter une ligne de référence à la mensualité actuelle
    fig.add_shape(type="line",
                  x0=mensualite_actuelle, y0=min(valeurs_bien),
                  x1=mensualite_actuelle, y1=max(valeurs_bien),
                  line=dict(color="red", dash="dash"))

    # Ajouter une annotation pour la mensualité actuelle
    fig.add_annotation(
        x=mensualite_actuelle,
        y=max(valeurs_bien),
        text=f"Mensualité actuelle: {format_number_fr(mensualite_actuelle)} €",
        showarrow=True,
        arrowhead=2,
        arrowsize=1,
        arrowwidth=2,
        ax=20,
        ay=-30
    )

    # Mettre à jour la disposition du graphique
    fig.update_layout(
        title="Comparaison des mensualités et valeur du bien",
        title_x=0.2,  # Centrer le titre
        xaxis_title="Mensualité (€)",
        yaxis_title="Valeur du bien (€)",
        height=500,  # Ajuster la hauteur
        showlegend=True,
        legend=dict(
            x=0.1, y=1.1,  # Position de la légende
            bgcolor="rgba(255, 255, 255, 0)",
        )
    )

    # Afficher le graphique
    st.plotly_chart(fig)

# Fonction pour tracer le graphique de comparaison des mensualités et taux d'endettement
def tracer_graphique_comparaison_taux_endettement(mensualite_actuelle, revenu_annuel):
    mensualites = [mensualite_actuelle + i * 20 for i in range(-10, 11)]
    revenu_mensuel = revenu_annuel / 12
    taux_endettements = [round((mensualite / revenu_mensuel) * 100, 2) for mensualite in mensualites]

    fig = go.Figure()

    # Ajouter la courbe des taux d'endettement
    fig.add_trace(go.Scatter(
        x=mensualites,
        y=taux_endettements,
        mode='lines+markers',
        name="Comparaison des taux d'endettement",
        line=dict(color="green", width=2),
        marker=dict(size=10, color="green")
    ))

    # Ajouter une ligne de référence à la mensualité actuelle
    fig.add_shape(type="line",
                  x0=mensualite_actuelle, y0=min(taux_endettements),
                  x1=mensualite_actuelle, y1=max(taux_endettements),
                  line=dict(color="red", dash="dash"))

    # Ajouter une annotation pour la mensualité actuelle
    fig.add_annotation(
        x=mensualite_actuelle,
        y=max(taux_endettements),
        text=f"Mensualité actuelle: {format_number_fr(mensualite_actuelle)} €",
        showarrow=True,
        arrowhead=2,
        arrowsize=1,
        arrowwidth=2,
        ax=20,
        ay=-30
    )

    # Mettre à jour la disposition du graphique
    fig.update_layout(
        title="Comparaison des taux d'endettement en fonction des mensualités",
        title_x=0.2,  # Centrer le titre
        xaxis_title="Mensualité (€)",
        yaxis_title="Taux d'endettement (%)",
        height=500,  # Ajuster la hauteur
        showlegend=True,
        legend=dict(
            x=0.1, y=1.1,  # Position de la légende
            bgcolor="rgba(255, 255, 255, 0)",
        )
    )

    # Afficher le graphique
    st.plotly_chart(fig)

# Ajout de la gestion des fichiers (CSV, Excel, PDF)
def telecharger_resultats(df_resultats):
    """
    Fonction permettant de télécharger les résultats en CSV, Excel ou PDF.
    """
    # Télécharger en CSV
    df_resultats_csv = df_resultats.copy()
    df_resultats_csv["Valeur"] = df_resultats_csv["Valeur"].apply(lambda x: x.replace('.', ',') if isinstance(x, str) else x)
    csv = df_resultats_csv.to_csv(index=False)
    st.download_button(
        label="Télécharger les résultats en CSV",
        data=csv,
        file_name='resultats_simulation.csv',
        mime='text/csv',
    )
    


    # Télécharger en PDF
    pdf = creer_pdf(df_resultats)
    st.download_button(
        label="Télécharger les résultats en PDF",
        data=pdf,
        file_name="resultats_simulation.pdf",
        mime="application/pdf",
    )

def creer_pdf(df_resultats, logo_path='1_Logo.png'):
    """
    Crée un fichier PDF des résultats de la simulation avec un en-tête et un pied de page
    personnalisés incluant le logo, le titre, et la mention des droits.
    Le tableau est centré, et les textes longs dans les cellules sont renvoyés à la ligne.
    """
    class PDF(FPDF):
        def header(self):
            # Ajouter le logo
            self.image(logo_path, 10, 8, 25)  # (x, y, largeur)
            
            # Ajustement de la position pour éviter le chevauchement avec le logo
            self.set_xy(35, 10)  # Positionner le texte un peu plus à droite pour éviter le chevauchement
            
            # Titre principal
            self.set_font('Arial', 'B', 17)
            self.cell(150, 10, "Simulation de financement immobilier", ln=True, align='C')
            
            # Phrase descriptive centrée (ajustée)
            self.set_font('Arial', '', 12)
            self.cell(200, 10, "Cette application vous permet de simuler votre financement immobilier", ln=True, align='C')
            self.cell(200, 5, "en fonction de divers paramètres financiers.", ln=True, align='C')
            
            # Ligne de séparation
            self.set_draw_color(169, 169, 169)  # Couleur gris pour la ligne
            self.set_line_width(0.5)
            self.line(10, 40, 200, 40)  # Ligne horizontale (x1, y1, x2, y2)
            self.ln(10)  # Espacement après l'en-tête
        
        def footer(self):
            # Positionnement à 1.5 cm du bas
            self.set_y(-30)
            
            # Ligne de séparation
            self.set_draw_color(169, 169, 169)
            self.set_line_width(0.5)
            self.line(10, self.get_y(), 200, self.get_y())  # Ligne horizontale
            
            # Logo dans le pied de page
            self.image(logo_path, 95, self.get_y() + 5, 20)  # (x, y, largeur)
            self.ln(20)
            
            # Texte du pied de page
            self.set_font('Arial', 'I', 8)
            self.cell(0, 10, "© 2024 - Simulation de financement immobilier. Réalisé par CBorges. Tous droits réservés.", align='C')

    # Initialiser le PDF
    pdf = PDF()
    pdf.add_page()
    
    # Taille de la police pour les tableaux
    pdf.set_font('Arial', 'B', 12)
    
    # Largeurs des colonnes
    col_width_desc = 90
    col_width_value = 80
    line_height = pdf.font_size * 1.5
    
    # Calculer la position initiale pour centrer le tableau
    table_x = (210 - (col_width_desc + col_width_value)) / 2
    pdf.set_x(table_x)

    # Couleurs pour l'en-tête du tableau
    pdf.set_fill_color(155, 72, 25)  # Couleur de l'en-tête (code couleur #9B4819)
    pdf.set_text_color(255, 255, 255)  # Texte en blanc pour l'en-tête

    # En-têtes du tableau
    pdf.cell(col_width_desc, line_height, 'Description', border=1, align='C', fill=True)
    pdf.cell(col_width_value, line_height, 'Valeur', border=1, align='C', fill=True)
    pdf.ln(line_height)
    
    # Remplir les cellules du tableau
    pdf.set_font('Arial', '', 10)  # Reset font for the table content
    pdf.set_text_color(0, 0, 0)  # Texte noir pour le contenu
    fill = False  # Toggle for row background color

    # Fonction pour renvoyer à la ligne si le texte est trop long
    def multi_cell_with_centering(pdf, width, height, text, fill):
        # Sauvegarder la position actuelle
        x = pdf.get_x()
        y = pdf.get_y()
        
        # Centrer la cellule
        pdf.multi_cell(width, height, text, border=1, align='C', fill=fill)
        
        # Retourner à la position de départ pour la prochaine cellule
        pdf.set_xy(x + width, y)

    # Obtenir la hauteur maximale de chaque ligne et ajuster
    def ajuster_ligne(pdf, desc, val, col_width_desc, col_width_value, line_height, fill):
        # Calcul de la hauteur requise pour chaque cellule de la ligne
        desc_height = pdf.get_string_width(desc) / col_width_desc * line_height
        val_height = pdf.get_string_width(val) / col_width_value * line_height
        max_height = max(desc_height, val_height, line_height)  # Obtenir la hauteur max

        # Fixer la hauteur de la ligne pour les deux colonnes en fonction de la cellule la plus haute
        pdf.set_x(table_x)  # S'assurer que le tableau reste centré
        pdf.multi_cell(col_width_desc, max_height, desc, border=1, align='C', fill=fill)
        pdf.set_xy(table_x + col_width_desc, pdf.get_y() - max_height)  # Retour pour ajouter la valeur
        pdf.multi_cell(col_width_value, max_height, val, border=1, align='C', fill=fill)

    for index, row in df_resultats.iterrows():
        description = row['Description']
        valeur = row['Valeur'].replace('€', 'EUR').replace('.', ',')  # Remplacer le caractère '€' par 'EUR' et le séparateur décimal par une virgule

        # Couleur de fond alternée
        if fill:
            pdf.set_fill_color(240, 240, 240)  # Gris clair
        else:
            pdf.set_fill_color(255, 255, 255)  # Blanc

        # Utilisation de ajuster_ligne pour ajuster automatiquement la hauteur de la ligne
        ajuster_ligne(pdf, description, valeur, col_width_desc, col_width_value, line_height, fill)

        # Alterner la couleur de fond
        fill = not fill
    
    # Sauvegarde du PDF dans un buffer BytesIO
    pdf_output = BytesIO()
    pdf_content = pdf.output(dest='S').encode('latin1')  # Générer le contenu du PDF en mémoire
    pdf_output.write(pdf_content)  # Écrire le contenu dans BytesIO
    pdf_output.seek(0)  # Revenir au début du buffer avant de le retourner
    return pdf_output

# --- Menu de navigation ---
st.sidebar.title("Menu")

# Conserver l'état de la page sélectionnée
if "page" not in st.session_state:
    st.session_state.page = "Présentation"

# Utiliser un selectbox pour la navigation
page = st.sidebar.selectbox(
    "Aller à :",
    ("Présentation", "Plan de financement", "Mensualité souhaitée", "Comparaison des mensualités"),
    index=0 if st.session_state.page == "Présentation" else 1
)

st.session_state.page = page

# Page 1 : Présentation
if st.session_state.page == "Présentation":
    st.markdown("""
    **🏠 Bienvenue sur votre application de simulation de financement immobilier !**  
    
    Avec cette plateforme interactive, vous pouvez planifier et optimiser votre projet immobilier facilement, en ajustant divers paramètres financiers selon vos besoins. Grâce à nos outils avancés, vous pourrez :
    - **🔍 Simuler votre financement immobilier :** Évaluez les coûts du prêt, les mensualités, ainsi que les frais annexes.
    - **📊 Obtenir des résultats détaillés :** Accédez à un récapitulatif complet, incluant les coûts totaux, votre taux d'endettement, et bien plus.
    - **⚙️ Ajuster vos mensualités :** Testez différentes options pour trouver la mensualité qui convient le mieux à votre situation.
    - **📈 Visualiser vos paiements :** Consultez des graphiques dynamiques qui montrent l'impact de votre choix de **mensualité** sur la **valeur de votre bien** et votre **taux d'endettement**. Visualisez facilement comment chaque **décision financière** influence votre projet immobilier à long terme.
    """)
    
    st.markdown("""### 🚀 Comment utiliser cette application :""")
    st.markdown("""
    1. 👉 **Menu de gauche > Plan de financement** : Remplissez les informations sur votre projet (revenus, prix du bien, apport, etc.).
    2. 🧮 **Chaque étape est pré-calculée** en fonction de vos données précédentes. Par exemple, votre apport personnel est automatiquement calculé à **15 %** du prix du bien.
    3. ✅ **Validez chaque étape** pour obtenir vos mensualités et les coûts associés.
    4. 🔄 Si vous souhaitez corriger une erreur, utilisez le bouton **"Reset"** pour réinitialiser toutes les données.
    5. 💸 Dans **"Mensualité souhaitée"**, entrez un montant pour obtenir des recommandations personnalisées.
    6. 📊 Allez dans **"Comparaison des mensualités"** pour visualiser l'impact de vos décisions financières, en fonction des informations fournies dans le **Plan de financement**.
    7. 💾 **Téléchargez votre simulation** au format de votre choix : CSV ou PDF.
    8. 🖨️ Avec le PDF, vous pourrez **imprimer** ou **partager** votre simulation avec votre conseiller bancaire pour être mieux préparé lors de vos rendez-vous.

    """)
    
    st.markdown("""### 📋 Terminologie et choix des calculs :""")
    st.markdown("""
    - **Prix d'achat :** Valeur totale du bien immobilier.
    - **Montant emprunté :** Prix d'achat moins votre apport personnel.
    - **Frais de notaire :** Estimés à 7,5 % du prix d'achat.
    - **Frais de garantie :** Frais de mise en place de la garantie du prêt (hypothèque, caution), soit 1,5 % du montant emprunté.
    - **Assurance emprunteur :** Protection en cas de décès, d'invalidité ou d'incapacité, estimée à 0,35 % du montant emprunté par an.
    - **Frais de dossier :** Frais bancaires pour la mise en place du prêt, soit 0,8 % du montant emprunté.
    - **Frais de courtage :** Frais du courtier, estimés à 1 % du montant emprunté, si vous en sollicitez un.
    - **Frais d'agence immobilière :** Facturés par l'agence, représentant 4 % du prix d'achat.
    - **PTZ (Prêt à Taux Zéro) :** Prêt dont les intérêts sont à la charge de l'État, disponible selon votre situation géographique, type de bien, vos revenus, et votre situation personnelle.
    - **PEL (Plan Épargne Logement) :** Votre épargne qui peut réduire le montant total à emprunter.
    - **Montant total à financer :** Inclut le montant emprunté et tous les frais associés (notaire, assurance, etc.), en tenant compte des aides (PTZ, PEL).
    - **Taux d'intérêt :** représente le coût du **prêt immobilier**, exprimé en pourcentage annuel. Il est appliqué au **montant emprunté** pour calculer les intérêts que vous devrez rembourser en plus du capital. Les taux d'intérêt sont influencés par plusieurs facteurs, notamment les conditions du **marché**, la **durée du prêt** et votre **profil emprunteur** (revenus, apport, situation professionnelle). Plus le taux d’intérêt est élevé, plus le coût total du crédit sera important. Il est important de **comparer les taux proposés** par différentes institutions financières et de tenir compte des frais supplémentaires (frais de dossier, frais de garantie) pour **évaluer le coût total de votre projet immobilier**.
    - **Prêt immobilier :** est un **crédit** destiné à financer l’achat d’un bien immobilier (maison, appartement, et/ ou travaux de rénovation). En contractant un prêt immobilier, vous vous engagez à rembourser l’emprunt selon un échéancier défini, comprenant des mensualités composées d’une partie du **capital emprunté** et d’**intérêts**. La durée du prêt, les taux d’intérêt, et les différents frais (assurance emprunteur, frais de notaire, garantie) influent sur le montant de chaque mensualité et sur le coût total du crédit. Le prêt immobilier peut être complété par des dispositifs d’aide comme le PTZ et/ ou un PEL pour réduire les coûts. Il est essentiel d’étudier les conditions du prêt et de **simuler les mensualités** pour s’assurer qu’elles correspondent à votre capacité de remboursement.
    """)

    st.markdown("""
    ### 🔢 Formule de calcul de la mensualité :
    
    Pour calculer la mensualité d'un prêt immobilier, nous utilisons la formule suivante, qui correspond à un prêt amortissable avec paiements constants :
    """)
    # Formule de calcul de la mensualité
    st.latex(r'''
    M = \frac{C \times T_m}{1 - (1 + T_m)^{-n}}
    ''')
    
    st.latex(r'''
    M_{\text{total}} = M + \frac{\text{Assurance annuelle emprunteur}}{12}
    ''')
    
    st.markdown("""
    Où :
    """)
    
    st.markdown("""   
    - **M** : Mensualité hors assurance
    - **C** : Montant emprunté (capital)
    - **T_m** : Taux d'intérêt mensuel (taux annuel divisé par 12)
    - **n** : Nombre total de mensualités (durée du prêt en mois)
    - **M_total** : Mensualité incluant l'assurance
    """)

    st.markdown("""   
    **Cette application est conçue pour être simple, efficace et intuitive.**

    **Bonne simulation et succès dans votre projet immobilier !** 🌟
    """)
    
# Page 2 : Simulation de Financement
elif st.session_state.page == "Plan de financement":
    st.markdown("<h1 style='text-align: center;'>🏠 Plan de Financement</h1>", unsafe_allow_html=True)

    # Initialisation des variables dans la session
    if "step" not in st.session_state:
        st.session_state.step = 1
    if "recap" not in st.session_state:
        st.session_state.recap = ""

    # Afficher la barre de progression
    afficher_barre_progression(st.session_state.step, 14)

    # Récapitulatif des informations validées
    if st.session_state.recap:
        st.markdown("<h2 style='text-align: center;'>Informations validées</h2>", unsafe_allow_html=True)
        st.text(st.session_state.recap)

    # Bouton Reset
    if st.button("Reset"):
        reset_calculs()
        #st.experimental_rerun()

    # Validation progressive des étapes
    if st.session_state.step == 1:
        revenu_annuel, bouton_valider = afficher_et_valider_etape("Revenu annuel avant impôt (€)", 60000, 1, min_value=0)
        if bouton_valider:
            st.session_state.revenu_annuel = revenu_annuel
            revenu_annuel_formatte = format_number_fr(revenu_annuel)
            st.session_state.recap += f"Revenu annuel avant impôt : {revenu_annuel_formatte} €\n"
            st.session_state.step = 2
            #st.experimental_rerun()

    elif st.session_state.step == 2:
        valeur_bien, bouton_valider = afficher_et_valider_etape("Valeur du bien / prix d'achat (€)", 200000, 2, min_value=0)
        if bouton_valider:
            st.session_state.valeur_bien = valeur_bien
            valeur_bien_formatte = format_number_fr(valeur_bien)
            st.session_state.recap += f"Valeur du bien / prix d'achat : {valeur_bien_formatte} €\n"
            st.session_state.step = 3
            #st.experimental_rerun()

    elif st.session_state.step == 3:
        apport = round(0.15 * st.session_state.valeur_bien, 2)
        apport_personnel, bouton_valider = afficher_et_valider_etape("Apport personnel (€)", apport, 3, min_value=0, max_value=st.session_state.valeur_bien)
        if bouton_valider:
            st.session_state.apport_personnel = apport_personnel
            st.session_state.montant_pret = st.session_state.valeur_bien - st.session_state.apport_personnel
            apport_personnel_formatte = format_number_fr(apport_personnel)
            st.session_state.recap += f"Apport personnel : {apport_personnel_formatte} €\n"
            st.session_state.step = 4
            #st.experimental_rerun()

    elif st.session_state.step == 4:
        taux_interet, bouton_valider = afficher_et_valider_etape("Taux d'intérêt (%)", 3.50, 4, min_value=0.0, max_value=100.0)
        if bouton_valider:
            st.session_state.taux_interet = taux_interet
            taux_interet_formatte = format_number_fr(taux_interet)
            st.session_state.recap += f"Taux d'intérêt : {taux_interet_formatte} %\n"
            st.session_state.step = 5
            #st.experimental_rerun()

    elif st.session_state.step == 5:
        duree_pret, bouton_valider = afficher_et_valider_etape("Durée du prêt (années)", 25, 5, min_value=1, max_value=40)
        if bouton_valider:
            st.session_state.duree_pret = duree_pret
            st.session_state.recap += f"Durée du prêt : {duree_pret} ans\n"
            st.session_state.step = 6
            #st.experimental_rerun()

    elif st.session_state.step == 6:
        assurance_annuelle = round(0.0035 * st.session_state.montant_pret, 2)
        assurance_emprunteur_annuelle, bouton_valider = afficher_et_valider_etape("Assurance emprunteur annuelle (€)", assurance_annuelle, 6, min_value=0)
        if bouton_valider:
            st.session_state.assurance_emprunteur_annuelle = assurance_emprunteur_annuelle
            assurance_emprunteur_annuelle_formatte = format_number_fr(assurance_emprunteur_annuelle)
            st.session_state.recap += f"Assurance emprunteur annuelle : {assurance_emprunteur_annuelle_formatte} €\n"
            st.session_state.step = 7
            #st.experimental_rerun()

    elif st.session_state.step == 7:
        frais_notaire = round(0.075 * st.session_state.valeur_bien, 2)
        frais_de_notaire, bouton_valider = afficher_et_valider_etape("Frais de notaire (€)", frais_notaire, 7, min_value=0)
        if bouton_valider:
            st.session_state.frais_de_notaire = frais_de_notaire
            frais_de_notaire_formatte = format_number_fr(frais_de_notaire)
            st.session_state.recap += f"Frais de notaire : {frais_de_notaire_formatte} €\n"
            st.session_state.step = 8
            #st.experimental_rerun()

    elif st.session_state.step == 8:
        frais_garantie = round(0.015 * st.session_state.montant_pret, 2)
        frais_de_garantie, bouton_valider = afficher_et_valider_etape("Frais de garantie (€)", frais_garantie, 8, min_value=0)
        if bouton_valider:
            st.session_state.frais_de_garantie = frais_de_garantie
            frais_de_garantie_formatte = format_number_fr(frais_de_garantie)
            st.session_state.recap += f"Frais de garantie : {frais_de_garantie_formatte} €\n"
            st.session_state.step = 9
            #st.experimental_rerun()

    elif st.session_state.step == 9:
        frais_dossier = round(0.008 * st.session_state.montant_pret, 2)
        frais_de_dossier, bouton_valider = afficher_et_valider_etape("Frais de dossier (€)", frais_dossier, 9, min_value=0)
        if bouton_valider:
            st.session_state.frais_de_dossier = frais_de_dossier
            frais_de_dossier_formatte = format_number_fr(frais_de_dossier)
            st.session_state.recap += f"Frais de dossier : {frais_de_dossier_formatte} €\n"
            st.session_state.step = 10
            #st.experimental_rerun()

    elif st.session_state.step == 10:
        frais_courtage = round(0.01 * st.session_state.montant_pret, 2)
        frais_de_courtage, bouton_valider = afficher_et_valider_etape("Frais de courtage (€)", frais_courtage, 10, min_value=0)
        if bouton_valider:
            st.session_state.frais_de_courtage = frais_de_courtage
            frais_de_courtage_formatte = format_number_fr(frais_de_courtage)
            st.session_state.recap += f"Frais de courtage : {frais_de_courtage_formatte} €\n"
            st.session_state.step = 11
            #st.experimental_rerun()

    elif st.session_state.step == 11:
        frais_agence = round(0.04 * st.session_state.valeur_bien, 2)
        frais_agence_immobiliere, bouton_valider = afficher_et_valider_etape("Frais d'agence immobilière (€)", frais_agence, 11, min_value=0)
        if bouton_valider:
            st.session_state.frais_agence_immobiliere = frais_agence_immobiliere
            frais_agence_immobiliere_formatte = format_number_fr(frais_agence_immobiliere)
            st.session_state.recap += f"Frais d'agence immobilière : {frais_agence_immobiliere_formatte} €\n"
            st.session_state.step = 12
            #st.experimental_rerun()

    elif st.session_state.step == 12:
        ptz, bouton_valider = afficher_et_valider_etape("Montant du Prêt à Taux Zéro (PTZ) (€)", 0, 12, min_value=0)
        if bouton_valider:
            st.session_state.ptz = ptz
            ptz_formatte = format_number_fr(ptz)
            st.session_state.recap += f"PTZ : {ptz_formatte} €\n"
            st.session_state.step = 13
            #st.experimental_rerun()

    elif st.session_state.step == 13:
        pel, bouton_valider = afficher_et_valider_etape("Montant du Plan Épargne Logement (PEL) (€)", 0, 13, min_value=0)
        if bouton_valider:
            st.session_state.pel = pel
            pel_formatte = format_number_fr(pel)
            st.session_state.recap += f"PEL : {pel_formatte} €\n"
            st.session_state.step = 14
            #st.experimental_rerun()

    # Simulation des résultats après la dernière étape
    if st.session_state.step == 14:
        df_resultats = simuler_financement_avec_calculs_et_recommandations()

        # Sélectionner uniquement les colonnes "Description" et "Valeurs"
        df_resultats = df_resultats[['Description', 'Valeur']]
        
        # Convertir le DataFrame en HTML sans index
        table_html = df_resultats.to_html(index=False, justify="center", border=0, classes="table-style")
        
        # Ajouter du CSS pour styliser le tableau avec des lignes alternées
        st.markdown(
            """
            <style>
            .table-style {
                margin-left: auto;
                margin-right: auto;
                width: 100%;
                border-collapse: collapse;
            }
            .table-style th, .table-style td {
                border: 1px solid #ddd;
                padding: 8px;
                text-align: center;
            }
            .table-style th {
                background-color: #9B4819;
                color: white;
            }
            /* Lignes paires */
            .table-style tr:nth-child(even) {
                background-color: #F0F2F6;  /* Couleur des lignes paires */
            }
            /* Lignes impaires */
            .table-style tr:nth-child(odd) {
                background-color: #ffffff;  /* Couleur des lignes impaires */
            }
            </style>
            """,
            unsafe_allow_html=True
        )

        # Afficher le tableau en HTML
        st.markdown(f"<h2 style='text-align: center;'>Résultats de la Simulation</h2>{table_html}", unsafe_allow_html=True)
        
        # Saut de ligne
        st.markdown(f"""<br>""", unsafe_allow_html=True)

        # Ajouter la possibilité de télécharger les résultats
        telecharger_resultats(df_resultats)

# Page 3 : Entrer la nouvelle mensualité souhaitée
elif st.session_state.page == "Mensualité souhaitée":
    st.markdown("<h1 style='text-align: center;'>🏡 Mensualité souhaitée</h1>", unsafe_allow_html=True)

    # Barre d'entrée pour la nouvelle mensualité souhaitée
    nouvelle_mensualite = st.number_input("Mensualité souhaitée (€)", value=1000.0, min_value=0.0)

    # Simulation des résultats après actualisation
    if "revenu_annuel" in st.session_state:
        df_resultats = simuler_financement_avec_calculs_et_recommandations()
        df_resultats_actualise = actualiser_financement(df_resultats, nouvelle_mensualite)

        # Sélectionner uniquement les colonnes "Description" et "Valeurs"
        df_resultats_actualise = df_resultats_actualise[['Description', 'Valeur']]

        # Convertir le DataFrame en HTML sans index
        table_html = df_resultats_actualise.to_html(index=False, justify="center", border=0, classes="table-style")

        # Ajouter du CSS pour styliser le tableau avec des lignes alternées
        st.markdown(
            """
            <style>
            .table-style {
                margin-left: auto;
                margin-right: auto;
                width: 100%;
                border-collapse: collapse;
            }
            .table-style th, .table-style td {
                border: 1px solid #ddd;
                padding: 8px;
                text-align: center;
            }
            .table-style th {
                background-color: #9B4819;
                color: white;
            }
            /* Lignes paires */
            .table-style tr:nth-child(even) {
                background-color: #F0F2F6;  /* Couleur des lignes paires */
            }
            /* Lignes impaires */
            .table-style tr:nth-child(odd) {
                background-color: #ffffff;  /* Couleur des lignes impaires */
            }
            </style>
            """,
            unsafe_allow_html=True
        )

        # Afficher le tableau en HTML
        st.markdown(f"<h2 style='text-align: center;'>Résultats après actualisation</h2>{table_html}", unsafe_allow_html=True)
        
        # Saut de ligne
        st.markdown(f"""<br>""", unsafe_allow_html=True)

        # Ajouter la possibilité de télécharger les résultats
        telecharger_resultats(df_resultats_actualise)
    else:
        st.warning("Veuillez d'abord compléter le plan de financement.")

# Page 4 : Comparaison entre la mensualité actuelle et souhaitée
elif st.session_state.page == "Comparaison des mensualités":
    st.markdown("<h1 style='text-align: center;'>📊 Comparaison des mensualités</h1>", unsafe_allow_html=True)

    if "revenu_annuel" in st.session_state:
        df_resultats = simuler_financement_avec_calculs_et_recommandations()
        
        # Utiliser la valeur brute directement sans formatage pour éviter les erreurs de conversion
        mensualite_avec_assurance_str = df_resultats.loc[df_resultats["Description"] == "Mensualité avec assurance", "Valeur"].values[0]
        
        # Nettoyer la valeur pour enlever les espaces et les symboles inutiles
        mensualite_avec_assurance = float(mensualite_avec_assurance_str.replace('€', '').replace('\xa0', '').replace(' ', '').replace(',', '.'))

        # Utiliser les valeurs brutes sans formatage
        valeur_bien = st.session_state.valeur_bien
        revenu_annuel = st.session_state.revenu_annuel

        # Tracer le graphique avec les mensualités croissantes et décroissantes (Valeur du bien)
        tracer_graphique_comparaison_mensualites_courbe(mensualite_avec_assurance, valeur_bien)

        # Tracer le graphique avec les mensualités croissantes et décroissantes (Taux d'endettement)
        tracer_graphique_comparaison_taux_endettement(mensualite_avec_assurance, revenu_annuel)
    else:
        st.warning("Veuillez d'abord compléter le plan de financement.")

# Ajouter un pied de page avec le logo
st.markdown(
    f"""
    <hr style="border:1px solid gray"> </hr>
    <footer style='text-align: center; font-size: 12px; color: gray;'>
        <img src='data:image/png;base64,{logo_base64}' alt='Logo' width='100'><br>
        © 2024 - Simulation de financement immobilier. Réalisé par CBorges. Tous droits réservés.
    </footer>
    """, 
    unsafe_allow_html=True
)
