import tkinter as tk
from tkinter import ttk, messagebox
import random
import time
from threading import Thread

class Tache:
    """Représente une tâche avec une taille et une durée de vie."""
    def __init__(self, nom, taille, duree, priorite=0):
        self.nom = nom
        self.taille = taille
        self.duree = duree  # Durée de vie en secondes
        self.priorite = priorite  # 0 = basse, 1 = haute

class GestionnaireMemoire:
    """Gère l'allocation et la libération de la mémoire."""
    def __init__(self, taille_memoire):
        self.taille_memoire = taille_memoire
        self.memoire = [None] * taille_memoire  # Mémoire simulée

    def allouer(self, tache, strategie):
        """Alloue un espace mémoire à la tâche selon la stratégie."""
        blocs_libres = self.obtenir_blocs_libres()

        if strategie == "premier_emplacement":
            bloc_choisi = next((bloc for bloc in blocs_libres if bloc[1] >= tache.taille), None)
        elif strategie == "plus_petit_emplacement":
            bloc_choisi = min((bloc for bloc in blocs_libres if bloc[1] >= tache.taille), key=lambda b: b[1], default=None)
        elif strategie == "plus_grand_emplacement":
            bloc_choisi = max((bloc for bloc in blocs_libres if bloc[1] >= tache.taille), key=lambda b: b[1], default=None)
        else:
            return False

        if bloc_choisi:
            indice_debut = bloc_choisi[0]
            for i in range(indice_debut, indice_debut + tache.taille):
                self.memoire[i] = tache
            return True
        return False

    def obtenir_blocs_libres(self):
        """Retourne les blocs de mémoire disponibles."""
        blocs_libres = []
        debut, compteur = None, 0

        for i in range(self.taille_memoire):
            if self.memoire[i] is None:
                if debut is None:
                    debut = i
                compteur += 1
            else:
                if debut is not None:
                    blocs_libres.append((debut, compteur))
                    debut, compteur = None, 0

        if debut is not None:
            blocs_libres.append((debut, compteur))

        return blocs_libres

    def liberer_memoire(self, tache):
        """Libère l'espace occupé par une tâche."""
        for i in range(self.taille_memoire):
            if self.memoire[i] == tache:
                self.memoire[i] = None

    def defragmenter(self):
        """Défragmente la mémoire en regroupant les blocs libres."""
        nouvelle_memoire = [None] * self.taille_memoire
        index = 0
        for tache in self.memoire:
            if tache is not None:
                nouvelle_memoire[index:index + tache.taille] = [tache] * tache.taille
                index += tache.taille
        self.memoire = nouvelle_memoire

class ApplicationMemoire:
    """Interface graphique pour afficher et gérer la mémoire."""
    def __init__(self, fenetre, taille_memoire=8192):  # Taille de la mémoire augmentée à 8192
        self.fenetre = fenetre
        self.fenetre.title("Gestion de Mémoire Dynamique")
        self.taille_memoire = taille_memoire
        self.gestionnaire = GestionnaireMemoire(taille_memoire)
        self.taches = []
        self.couleurs = {}
        self.index_couleur = 0
        self.palette = ["red", "green", "blue", "yellow", "purple", "orange"]

        # Zone d'affichage de la mémoire (utilisation d'un diagramme)
        self.zone_affichage = tk.Canvas(fenetre, width=1024, height=100, bg="white")  # Largeur augmentée à 1024 pixels
        self.zone_affichage.pack(pady=10)

        # Zone de logs
        self.zone_logs = tk.Text(fenetre, height=5, width=60)
        self.zone_logs.pack()
        
        # Champs de saisie et boutons
        cadre = tk.Frame(fenetre)
        cadre.pack(pady=10)
        
        tk.Label(cadre, text="Nom :").grid(row=0, column=0)
        self.nom_tache = tk.Entry(cadre)
        self.nom_tache.grid(row=0, column=1)
        
        tk.Label(cadre, text="Taille :").grid(row=1, column=0)
        self.taille_tache = tk.Entry(cadre)
        self.taille_tache.grid(row=1, column=1)
        
        tk.Label(cadre, text="Durée :").grid(row=2, column=0)
        self.duree_tache = tk.Entry(cadre)
        self.duree_tache.grid(row=2, column=1)
        
        tk.Label(cadre, text="Stratégie :").grid(row=3, column=0)
        self.strategie_var = tk.StringVar(value="premier_emplacement")
        strategies = ["premier_emplacement", "plus_petit_emplacement", "plus_grand_emplacement"]  # Suppression de "best_fit" et "worst_fit"
        tk.OptionMenu(cadre, self.strategie_var, *strategies).grid(row=3, column=1)
        
        tk.Button(cadre, text="Ajouter Tâche", command=self.ajouter_tache).grid(row=4, column=0, columnspan=2)
        tk.Button(cadre, text="Supprimer Tâche", command=self.supprimer_tache).grid(row=5, column=0, columnspan=2)
        tk.Button(cadre, text="Défragmenter", command=self.defragmenter).grid(row=6, column=0, columnspan=2)
        tk.Button(cadre, text="Générer Tâche Aléatoire", command=self.generer_tache_aleatoire).grid(row=7, column=0, columnspan=2)
        tk.Button(cadre, text="Sauvegarder État", command=self.sauvegarder_etat).grid(row=8, column=0, columnspan=2)
        tk.Button(cadre, text="Charger État", command=self.charger_etat).grid(row=9, column=0, columnspan=2)

        # Statistiques
        self.label_statistiques = tk.Label(fenetre, text=f"Statistiques : Mémoire libre = {taille_memoire}, Mémoire occupée = 0")
        self.label_statistiques.pack()

        self.mettre_a_jour_affichage()

        # Thread pour surveiller les tâches
        self.en_cours = True
        self.fil_taches = Thread(target=self.surveiller_taches, daemon=True)
        self.fil_taches.start()

    def journaliser(self, message):
        """Ajoute un message aux logs."""
        self.zone_logs.insert(tk.END, message + "\n")
        self.zone_logs.see(tk.END)

    def ajouter_tache(self):
        """Ajoute une tâche."""
        nom = self.nom_tache.get()
        try:
            taille = int(self.taille_tache.get())
            duree = int(self.duree_tache.get())
            if taille <= 0 or duree <= 0:
                raise ValueError
            if taille > self.taille_memoire:
                self.journaliser("Erreur : La taille de la tâche dépasse la mémoire disponible.")
                return
        except ValueError:
            self.journaliser("Erreur : Valeurs numériques positives requises pour taille et durée.")
            return

        strategie = self.strategie_var.get()
        tache = Tache(nom, taille, duree)
        
        if self.gestionnaire.allouer(tache, strategie):
            self.taches.append(tache)
            self.couleurs[nom] = self.palette[self.index_couleur % len(self.palette)]
            self.index_couleur += 1
            self.journaliser(f"Tâche {nom} ajoutée avec {strategie}.")
        else:
            self.journaliser(f"Échec d'allocation pour {nom}.")

        self.mettre_a_jour_affichage()

    def supprimer_tache(self):
        """Supprime une tâche."""
        if self.taches:
            tache = self.taches.pop(0)
            self.gestionnaire.liberer_memoire(tache)
            self.journaliser(f"Tâche {tache.nom} supprimée manuellement.")
        self.mettre_a_jour_affichage()

    def defragmenter(self):
        """Défragmente la mémoire."""
        self.gestionnaire.defragmenter()
        self.journaliser("Mémoire défragmentée.")
        self.mettre_a_jour_affichage()

    def generer_tache_aleatoire(self):
        """Génère une tâche aléatoire."""
        nom = f"Tâche_{random.randint(1, 100)}"
        taille = random.randint(1, 10)
        duree = random.randint(5, 20)
        self.nom_tache.insert(0, nom)
        self.taille_tache.insert(0, taille)
        self.duree_tache.insert(0, duree)
        self.ajouter_tache()

    def sauvegarder_etat(self):
        """Sauvegarde l'état de la mémoire dans un fichier."""
        with open("etat_memoire.txt", "w") as f:
            for tache in self.taches:
                f.write(f"{tache.nom},{tache.taille},{tache.duree}\n")
        self.journaliser("État de la mémoire sauvegardé.")

    def charger_etat(self):
        """Charge l'état de la mémoire depuis un fichier."""
        try:
            with open("etat_memoire.txt", "r") as f:
                for ligne in f:
                    nom, taille, duree = ligne.strip().split(",")
                    tache = Tache(nom, int(taille), int(duree))
                    self.taches.append(tache)
                    self.gestionnaire.allouer(tache, "premier_emplacement")
            self.journaliser("État de la mémoire chargé.")
        except FileNotFoundError:
            self.journaliser("Erreur : Fichier de sauvegarde introuvable.")

    def surveiller_taches(self):
        """Surveille la durée de vie des tâches."""
        while self.en_cours:
            for tache in self.taches[:]:  # Copie de la liste pour éviter les erreurs de modification
                tache.duree -= 1
                if tache.duree <= 0:
                    self.taches.remove(tache)
                    self.gestionnaire.liberer_memoire(tache)
                    self.journaliser(f"Tâche {tache.nom} supprimée automatiquement.")
            self.mettre_a_jour_affichage()
            time.sleep(1)

    def mettre_a_jour_affichage(self):
        """Met à jour l'affichage graphique de la mémoire sous forme de diagramme."""
        self.zone_affichage.delete("all")
        largeur_case = 1024 / self.taille_memoire  # Largeur ajustée pour 4096 unités
        x_position = 0

        # Affichage des tâches allouées
        for tache in self.taches:
            self.zone_affichage.create_rectangle(
                x_position, 0, x_position + tache.taille * largeur_case, 100, fill=self.couleurs.get(tache.nom, "gray"), outline="black")
            x_position += tache.taille * largeur_case

        # Affichage des blocs libres
        for bloc in self.gestionnaire.obtenir_blocs_libres():
            x1 = bloc[0] * largeur_case
            x2 = x1 + bloc[1] * largeur_case
            self.zone_affichage.create_rectangle(x1, 0, x2, 100, fill="white", outline="black")

        # Mettre à jour les statistiques
        blocs_libres = self.gestionnaire.obtenir_blocs_libres()
        total_libre = sum(bloc[1] for bloc in blocs_libres)
        total_occupe = self.taille_memoire - total_libre
        self.label_statistiques.config(text=f"Statistiques : Mémoire libre = {total_libre}, Mémoire occupée = {total_occupe}")

# Création de l'interface graphique
fenetre = tk.Tk()
app = ApplicationMemoire(fenetre)
fenetre.mainloop()
