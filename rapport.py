import numpy as np

import matplotlib.pyplot as plt
import comtrade 

import tkinter as tk
from tkinter import filedialog
from fpdf import FPDF
import os
print(os.getcwd())

# ///////////////////CHEMIN///////////////////  
def get_file_path():
    # Crée une fenêtre Tkinter
    root = tk.Tk()
    root.withdraw()  # Cache la fenêtre principale<<<<<<<<<<<<<<<<<<<<<<<
    # Ouvre l'explorateur de fichiers
    file_path = filedialog.askopenfilename()
    type_fichier = file_path[-3:]
    nom_variable = file_path[:-3]
    
    data_file = nom_variable+"DAT"
    cfg_file = nom_variable+"CFG"
   
    return (cfg_file,data_file)
# Exécute la fonction et affiche le chemin d'accès
file = get_file_path()
cfg_file = file[0]
dat_file = file[1]

"""
 # Read the CFG file and remove BOM if present
with open(cfg_file, 'r', encoding='utf-8-sig') as file:
    cfg_content = file.read()

 # Write the cleaned content back to the file
with open(cfg_file, 'w', encoding='utf-8') as file:
    file.write(cfg_content)
"""
# Create a Comtrade object and load the files
rec = comtrade.Comtrade()
rec.load(cfg_file, dat_file)
print("Trigger time = {}s".format(rec.trigger_time))
#Déclaration des variables
date = rec.start_timestamp
trigger_signal_name = '~~~~~~~~~~~~~~ Inconnue ~~~~~~~~~~~~~~'
rec_number = '~~~~~~~~~~~~~~ Inconnue ~~~~~~~~~~~~~~'
total_rec_time = rec.time[-1]
frequence = rec.cfg.frequency
sampling_rate = rec.cfg.sample_rates
nbr_analogique = rec.analog_count
nbr_binaire = rec.status_count
temps = []
print(f"Year: {rec.station_name}")
print(f"Total Channels: {rec.total_samples}")
print(f"La frequence est de {frequence} Hz") 
print(f"La date et l'heure d'engrensitrement est : {date}")
#print(f"trigger_signal_name: {trigger_signal_name}")
print(f"rec_number: {rec_number}")
print(f"total_rec_time: {total_rec_time}")
print(f"debut de l'enregistrement {sampling_rate[0][0]} ms")
print(f"fin de l'enregistrement {sampling_rate[0][1]} ms")
print(f"Nombre de canaux analogiques : {nbr_analogique}")
print(f"Nombre de canaux binaire : {nbr_binaire}")

print("/////////////////////////////////////////////////////")



def mise_en_liste_analog(nbr_analog):
    """ recupere les valeurs analog brut ADC """
    liste_data = []
    temps = []
    for lanalog in range(nbr_analog):
        liste_data.append([])
        for i in range(len(rec.time)):
            temps.append(rec.time[i])
            liste_data[lanalog].append(rec.analog[lanalog][i])
    return liste_data

def recup_AB():
    liste_ab = []
    for i in rec.cfg.analog_channels:
        liste_ab.append((i.a,i.b))
    return liste_ab

def rapportPri_Sec():
    liste= []
    for i,analog_channel in enumerate(rec.cfg.analog_channels):
        liste.append(analog_channel.primary/analog_channel.secondary)
    return liste



liste_data= mise_en_liste_analog(nbr_analogique)
analogique0=liste_data[0]
temps = rec.time
div = recup_AB() #changer div par la liste des coef a b
#print(div) #changer div par la liste des coef a b
liste_div = rapportPri_Sec()
#print(liste_div,"ligne 122")

def brut_secondaire(listeAB,data):
    for coef in listeAB:
        a =  coef[0]
        b = coef[1]
        for liste in data:
           
            for element in liste:
               element = element*a +b
               
    return data     
temp = (brut_secondaire(div,liste_data)) #changer div par la liste des coef a b

def transfo_primaire(analog,liste_div):
    for analo in rec.cfg.analog_channels:
        signal_type = analo.pors
        if signal_type == "S": 
            for sousliste in range(len(analog)):  
                analogique_prime =[[element * liste_div[i] for element in analog[i]] for i in range(len(analog))]

    return analogique_prime
                   
temp2 = transfo_primaire(temp,liste_div)

def creer_repertoire_ganalog(chemin_dossier):
    #chemin_dossier = r"C:\Users\SESA817224\Documents\fichier comtrade\COMTRADE 2013\DOSSIER GRAPHIQUE"
    try:
        os.makedirs(chemin_dossier,exist_ok=True)
        print(f"le dossier{chemin_dossier} a été créé avec succès.")
    except Exception as e:
        print(f"Une erreur est survenue lors de la creation du dossier.")
    return chemin_dossier

def graph_analogique(x,y):
    # Étape 3 : zoom sur un intervalle spécifique (par exemple 0 à 1)
    plt.figure()
    plt.plot(x,y)
    plt.xlabel('temps')
    plt.ylabel('valeurs binaire')
    #plt.show()   
    #plt.clf()# Clear 

def save_graph_analog(temp,liste_data,path):
    a = creer_repertoire_ganalog(path)
    chemin_images = []
    #output_folder = "chemin/vers/votre/dossier"
    if not os.path.exists(path):
        os.makedirs(path)

    for i in range(len(liste_data)):
        
        graph_analogique(temp,liste_data[i])
        nom_fichier = f"{path}/graphique{i}.png"
        chemin_images.append(nom_fichier)
        plt.savefig(nom_fichier)
        plt.close()

    return chemin_images


# === 2. CONVERSION EN TABLEAUX NUMPY POUR CALCUL ===
def fresnel(temps,analogique):
    t = np.array(temps)
    y = np.array(analogique)
    # === 3. CALCUL DE LA FRÉQUENCE D'ÉCHANTILLONNAGE ===
    dt = t[1] - t[0]  # suppose un échantillonnage régulier
    f_ech = 1 / dt 
    # === 4. FFT POUR EXTRAIRE LE PHASOR ===
    Y = np.fft.fft(y)
    frequencies = np.fft.fftfreq(len(t), d=1/f_ech)
    # === 5. NE GARDER QUE LES FRÉQUENCES POSITIVES ===
    mask_pos = frequencies > 0
    frequencies = frequencies[mask_pos]
    Y = Y[mask_pos]

    # === 6. TROUVER LA FRÉQUENCE PRINCIPALE ===
    index_max = np.argmax(np.abs(Y))
    freq_fondamentale = frequencies[index_max]
    phasor = Y[index_max] / len(t)

    # === 7. CALCUL DE L’AMPLITUDE ET DE LA PHASE ===
    amplitude = 2 * np.abs(phasor)  # facteur 2 car unilatéral
    phase_rad = np.angle(phasor)
    phase_deg = np.rad2deg(phase_rad)

    # === 8. AFFICHAGE DES RÉSULTATS ===
    print(f"Fréquence fondamentale : {freq_fondamentale:.2f} Hz")
    print(f"Amplitude : {amplitude:.2f} V")
    print(f"Phase : {phase_deg:.2f}°") 

    # === 9. DIAGRAMME DE FRESNEL ===
    fig, ax = plt.subplots(subplot_kw={'projection': 'polar'})
    ax.arrow(phase_rad, 0, 0, amplitude,
         head_width=0.1, head_length=amplitude*0.05,
         linewidth=2, label="Signal mesuré")
    ax.set_title("Diagramme de Fresnel liste -> analogique0")
    ax.legend()
    #plt.show()
        

def parcoursFresnel(temps,liste_data,path):
    chemin_images = []
    if not os.path.exists(path):
        os.makedirs(path)
    i=0
    for sousListe in liste_data:
        i+=1
        fresnel(temps,sousListe)
        nom_fichier = f"{path}/graphiqueFresnel{i}.png"
        chemin_images.append(nom_fichier)
        plt.savefig(nom_fichier)
        plt.close()

    return chemin_images
      

#CHEMIN = "C:/Users/SESA817224/Documents/fichier comtrade/COMTRADE 2013/fichier img"  #penser à changer le chemin d'acces
CHEMIN2 = "C:/Users/SESA817224/Documents/fichier comtrade/COMTRADE 2013/fichier img"


liste_chemin = []#Contient toute les listes des chemin de chaque type de graphique


#chemin_image = save_graph_analog(temps,temp2,CHEMIN)
chemin_analog = save_graph_analog(temps,temp2,CHEMIN2)

#liste_chemin.append(chemin_image)
liste_chemin.append(chemin_analog)
liste_chemin.append(parcoursFresnel(temps,temp2,CHEMIN2))

        
def create_pdf(path,liste_img_path):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=10)
    #pdf.cell(200, 10, txt="Hello, World!", ln=True, align='C')


    #pdf.cell(200, 10, txt=f"nom fichier: {name}", ln=True)
    pdf.cell(200, 10, txt=f"annee norme: {rec.station_name}", ln=True)
    pdf.cell(200, 10, txt=f"Total Channels:  {frequence}", ln=True)
    pdf.cell(200, 10, txt=f"La frequence est de:  {rec.total_samples}" ,ln=True)
    pdf.cell(200, 10, txt=f"La date et l'heure d'engrensitrement est :  {date}" ,ln=True)
    #//////////////////////////////////////////////////////////////////////////////////////////
    pdf.cell(200, 10, txt=f"rec_number:  {rec_number}" ,ln=True)
    pdf.cell(200, 10, txt=f"total_rec_time:  {total_rec_time}" ,ln=True)
    pdf.cell(200, 10, txt=f"debut de l'enregistrement:  {sampling_rate[0][0]}" ,ln=True)
    pdf.cell(200, 10, txt=f"fin de l'enregistrement :  {sampling_rate[0][1]}" ,ln=True)
    pdf.cell(200, 10, txt=f"Nombre de canaux analogiques :  {nbr_analogique}" ,ln=True)
    pdf.cell(200, 10, txt=f"Nombre de canaux binaire :  {nbr_binaire}" ,ln=True)

    
    for sousliste in range(len(liste_img_path)):
        
        
        imagePdf(pdf,liste_img_path[sousliste])#pour les graphique basique
    #imagePdf(pdf,liste_img_path[1])#pour les graphique vectotiel
    pdf.cell(200, 10, txt=f"annee norme: {rec.station_name}", ln=True)
    #imagePdf(pdf,liste_img_path)#pour les graphique binaire
# Check if the next image will fit on the current page
       # pdf.add_page()
    #file_name = "example3.pdf"
    #file_path = os.path.join(os.getcwd(), file_name)
    #pdf.output(file_path)
    NOM = 'mon_documentTST5.pdf'
    pdf.output(NOM)
    print(f"The PDF has been saved at: {NOM}")

def imagePdf(pdf,img_path):
    x = 10
    y = 130
    w = 100
    h = 100
    
    print(img_path,"imagepdf")
    for elt in img_path:
    
        if y + h > pdf.h - 1:# pdf.h is the height of the page
            pdf.add_page()
            y = 5# Reset y for the new page

        print(elt,"L 315")  
        pdf.image(elt,x,y,w)  
        y += h
        
print(create_pdf(CHEMIN2,liste_chemin))

print(liste_chemin[1])

""""
def graph_bi(x,y):
    X = np.array(x)
    Y = np.array(y)
    # Create a mask for positive values
    positive_mask = Y > 0

    # Use the mask to select only positive values
    axey = Y[positive_mask]
    print(axey)
    plt.figure()
    #####plt.plot(len(axey),axey)
    #plt.xlabel('temps')
    #####plt.ylabel('valeurs analogique')
    #plt.show()
#print(graph_bi(temps,temp2))
"""
print('fin') 
