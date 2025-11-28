import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import json
import os
import copy
from collections import deque

# =============================================================================
# CONFIGURATION MATERIELLE & CONSTANTES
# =============================================================================
GRID_SIZE = 16        # Taille totale (16x16)
MATRIX_SIZE = 8       # Taille d'une sous-matrice (8x8)

# Couleurs (Thème Dark Mode Pro)
COLOR_BG = "#1e1e1e"           # Fond fenêtre
COLOR_PANEL = "#2d2d2d"        # Fond panneaux
COLOR_GRID_BG = "#000000"      # Fond grille LED (Noir profond)
COLOR_LED_OFF = "#1a331a"      # LED éteinte
COLOR_LED_ON = "#00ff00"       # LED allumée (Vert fluo Proteus)
COLOR_QUAD_SEP = "#0088ff"     # Séparateur (Bleu)
COLOR_TEXT = "#ffffff"
COLOR_ACCENT = "#007acc"

class MatrixStudioApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Matrix Studio - Hard Logic EEPROM Generator")
        self.root.geometry("1100x800")
        self.root.configure(bg=COLOR_BG)

        # --- Données du projet ---
        self.frames = [] 
        self.current_frame_index = 0
        self.is_playing = False
        self.play_speed = 200 # ms
        
        # --- CONFIGURATION D'EXPORT ---
        # Paramètres validés pour ton Hardware Proteus :
        self.var_bit_reversal = tk.BooleanVar(value=True)   # D0 <-> D7 (Activé)
        self.var_flip_x = tk.BooleanVar(value=False)         # Flip Horizontal (Désactivé)
        self.var_flip_y = tk.BooleanVar(value=False)        # Flip Vertical (Désactivé)
        self.var_invert_output = tk.BooleanVar(value=True)  # Active Low (Activé)
        self.var_offset = tk.IntVar(value=-1)               # Correction Translation (-1)
        
        # NOUVEAU : Gestion de la boucle mémoire
        # 64 est la valeur standard pour 5 bits d'adresse de frame (A3..A7)
        self.var_memory_loop = tk.IntVar(value=64) 

        self.setup_ui()
        self.add_new_frame()

    def setup_ui(self):
        # Conteneur Principal
        main_frame = tk.Frame(self.root, bg=COLOR_BG)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # --- 1. Panneau Gauche : Timeline ---
        left_panel = tk.Frame(main_frame, bg=COLOR_PANEL, width=200)
        left_panel.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))
        
        tk.Label(left_panel, text="TIMELINE", bg=COLOR_PANEL, fg=COLOR_TEXT, font=("Arial", 12, "bold")).pack(pady=10)
        
        self.listbox_frames = tk.Listbox(left_panel, bg="#111", fg="white", selectbackground=COLOR_ACCENT, height=20, bd=0)
        self.listbox_frames.pack(fill=tk.X, padx=5)
        self.listbox_frames.bind('<<ListboxSelect>>', self.on_frame_select)

        btn_frame = tk.Frame(left_panel, bg=COLOR_PANEL)
        btn_frame.pack(fill=tk.X, pady=10)
        self.create_flat_button(btn_frame, "+ Ajouter", self.add_new_frame).pack(fill=tk.X, padx=5, pady=2)
        self.create_flat_button(btn_frame, "++ Dupliquer", self.duplicate_frame).pack(fill=tk.X, padx=5, pady=2)
        self.create_flat_button(btn_frame, "- Supprimer", self.delete_frame, bg="#cc0000").pack(fill=tk.X, padx=5, pady=2)
        
        self.create_flat_button(left_panel, "Monter ▲", self.move_frame_up).pack(fill=tk.X, padx=5, pady=2)
        self.create_flat_button(left_panel, "Descendre ▼", self.move_frame_down).pack(fill=tk.X, padx=5, pady=2)

        # --- 2. Panneau Central : Grille ---
        center_panel = tk.Frame(main_frame, bg=COLOR_BG)
        center_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.canvas_size = 520
        self.cell_size = self.canvas_size // GRID_SIZE
        
        info_frame = tk.Frame(center_panel, bg=COLOR_BG)
        info_frame.pack(fill=tk.X, pady=5)
        self.lbl_current_info = tk.Label(info_frame, text="Frame 1/1", bg=COLOR_BG, fg=COLOR_TEXT, font=("Arial", 14))
        self.lbl_current_info.pack()

        self.canvas = tk.Canvas(center_panel, width=self.canvas_size, height=self.canvas_size, 
                                bg=COLOR_GRID_BG, highlightthickness=0)
        self.canvas.pack(anchor=tk.CENTER)
        
        # Dessin
        self.canvas.bind("<Button-1>", lambda e: self.paint(e, 1))
        self.canvas.bind("<B1-Motion>", lambda e: self.paint(e, 1))
        self.canvas.bind("<Button-3>", lambda e: self.paint(e, 0))
        self.canvas.bind("<B3-Motion>", lambda e: self.paint(e, 0))

        # --- 3. Panneau Droit : Export & Contrôles ---
        right_panel = tk.Frame(main_frame, bg=COLOR_PANEL, width=250)
        right_panel.pack(side=tk.RIGHT, fill=tk.Y, padx=(10, 0))

        tk.Label(right_panel, text="ANIMATION", bg=COLOR_PANEL, fg=COLOR_TEXT, font=("Arial", 11, "bold")).pack(pady=10)
        self.btn_play = self.create_flat_button(right_panel, "▶ LECTURE", self.toggle_play, bg=COLOR_ACCENT)
        self.btn_play.pack(fill=tk.X, padx=10)
        
        self.scale_speed = tk.Scale(right_panel, from_=50, to=1000, orient=tk.HORIZONTAL, bg=COLOR_PANEL, fg="white", highlightthickness=0, label="Vitesse (ms)", command=self.update_speed)
        self.scale_speed.set(200)
        self.scale_speed.pack(fill=tk.X, padx=10)

        # CONFIGURATION HARDWARE
        tk.Label(right_panel, text="HARDWARE CONFIG", bg=COLOR_PANEL, fg="#ffaa00", font=("Arial", 11, "bold")).pack(pady=(20, 5))
        
        self.create_chk(right_panel, "Inverser Bits (D0↔D7)", self.var_bit_reversal)
        self.create_chk(right_panel, "Inverser Polarité (Low)", self.var_invert_output)
        self.create_chk(right_panel, "Flip Horizontal (X)", self.var_flip_x)
        self.create_chk(right_panel, "Flip Vertical (Y)", self.var_flip_y)

        # OFFSET
        frm_offset = tk.Frame(right_panel, bg=COLOR_PANEL)
        frm_offset.pack(fill=tk.X, pady=5)
        tk.Label(frm_offset, text="Offset Y:", bg=COLOR_PANEL, fg="#aaa").pack(side=tk.LEFT, padx=10)
        tk.Spinbox(frm_offset, from_=-8, to=8, textvariable=self.var_offset, width=5).pack(side=tk.RIGHT, padx=10)

        # NOUVEAU : MEMORY LOOP
        tk.Label(right_panel, text="GESTION MÉMOIRE", bg=COLOR_PANEL, fg="#00ccff", font=("Arial", 11, "bold")).pack(pady=(20, 5))
        
        tk.Label(right_panel, text="Taille Boucle Hardware :", bg=COLOR_PANEL, fg="white", font=("Arial", 9)).pack(anchor=tk.W, padx=10)
        tk.Label(right_panel, text="(Répète l'animation pour remplir)", bg=COLOR_PANEL, fg="#888", font=("Arial", 8)).pack(anchor=tk.W, padx=10)
        
        spin_loop = tk.Spinbox(right_panel, from_=1, to=1024, textvariable=self.var_memory_loop, 
                               bg="#444", fg="white", buttonbackground="#666", font=("Arial", 11))
        spin_loop.pack(fill=tk.X, padx=10, pady=5)


        self.create_flat_button(right_panel, "💾 GÉNÉRER BINAIRES", self.export_binaries, bg="#009900", height=2).pack(fill=tk.X, padx=10, pady=20)
        
        self.create_flat_button(right_panel, "Sauvegarder Projet", self.save_project).pack(fill=tk.X, padx=10, pady=5)
        self.create_flat_button(right_panel, "Charger Projet", self.load_project).pack(fill=tk.X, padx=10, pady=5)

    def create_flat_button(self, parent, text, command, bg="#444", fg="white", height=1):
        return tk.Button(parent, text=text, command=command, bg=bg, fg=fg, 
                         relief=tk.FLAT, activebackground="#666", activeforeground="white", height=height)

    def create_chk(self, parent, text, variable):
        tk.Checkbutton(parent, text=text, variable=variable, bg=COLOR_PANEL, fg="white", 
                       selectcolor="#444", activebackground=COLOR_PANEL).pack(anchor=tk.W, padx=10)

    # =========================================================================
    # LOGIQUE DESSIN
    # =========================================================================
    def get_empty_frame(self):
        return [[0 for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]

    def draw_grid(self):
        self.canvas.delete("all")
        if not self.frames: return
        grid = self.frames[self.current_frame_index]
        
        for r in range(GRID_SIZE):
            for c in range(GRID_SIZE):
                x1, y1 = c * self.cell_size, r * self.cell_size
                x2, y2 = x1 + self.cell_size, y1 + self.cell_size
                color = COLOR_LED_ON if grid[r][c] else COLOR_LED_OFF
                self.canvas.create_oval(x1+2, y1+2, x2-2, y2-2, fill=color, outline="")

        mid = (GRID_SIZE * self.cell_size) / 2
        self.canvas.create_line(mid, 0, mid, self.canvas_size, fill=COLOR_QUAD_SEP, width=2)
        self.canvas.create_line(0, mid, self.canvas_size, mid, fill=COLOR_QUAD_SEP, width=2)

    def paint(self, event, state):
        col, row = event.x // self.cell_size, event.y // self.cell_size
        if 0 <= col < GRID_SIZE and 0 <= row < GRID_SIZE:
            self.frames[self.current_frame_index][row][col] = state
            self.draw_grid()

    # =========================================================================
    # GESTION FRAMES
    # =========================================================================
    def add_new_frame(self):
        self.frames.append(self.get_empty_frame())
        self.current_frame_index = len(self.frames) - 1
        self.update_timeline()

    def duplicate_frame(self):
        new_frame = copy.deepcopy(self.frames[self.current_frame_index])
        self.frames.insert(self.current_frame_index + 1, new_frame)
        self.current_frame_index += 1
        self.update_timeline()

    def delete_frame(self):
        if len(self.frames) > 1:
            del self.frames[self.current_frame_index]
            if self.current_frame_index >= len(self.frames): self.current_frame_index = len(self.frames) - 1
            self.update_timeline()
        else: messagebox.showwarning("Erreur", "Il faut au moins une frame.")

    def move_frame_up(self):
        i = self.current_frame_index
        if i > 0:
            self.frames[i], self.frames[i-1] = self.frames[i-1], self.frames[i]
            self.current_frame_index -= 1
            self.update_timeline()

    def move_frame_down(self):
        i = self.current_frame_index
        if i < len(self.frames) - 1:
            self.frames[i], self.frames[i+1] = self.frames[i+1], self.frames[i]
            self.current_frame_index += 1
            self.update_timeline()

    def update_timeline(self):
        self.listbox_frames.delete(0, tk.END)
        for i in range(len(self.frames)):
            self.listbox_frames.insert(tk.END, f"Frame {i+1}")
        self.listbox_frames.selection_clear(0, tk.END)
        self.listbox_frames.selection_set(self.current_frame_index)
        self.lbl_current_info.config(text=f"Frame {self.current_frame_index + 1}/{len(self.frames)}")
        self.draw_grid()

    def on_frame_select(self, event):
        sel = event.widget.curselection()
        if sel:
            self.current_frame_index = sel[0]
            self.lbl_current_info.config(text=f"Frame {self.current_frame_index + 1}/{len(self.frames)}")
            self.draw_grid()

    # =========================================================================
    # ANIMATION
    # =========================================================================
    def update_speed(self, val): self.play_speed = int(val)

    def toggle_play(self):
        self.is_playing = not self.is_playing
        if self.is_playing:
            self.btn_play.config(text="⏹ STOP", bg="#cc0000")
            self.run_animation()
        else:
            self.btn_play.config(text="▶ LECTURE", bg=COLOR_ACCENT)

    def run_animation(self):
        if self.is_playing:
            self.current_frame_index = (self.current_frame_index + 1) % len(self.frames)
            self.update_timeline()
            self.root.after(self.play_speed, self.run_animation)

    # =========================================================================
    # I/O PROJET
    # =========================================================================
    def save_project(self):
        f = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON", "*.json")])
        if f:
            with open(f, "w") as file: json.dump({"frames": self.frames}, file)
            messagebox.showinfo("OK", "Projet sauvegardé.")

    def load_project(self):
        f = filedialog.askopenfilename(filetypes=[("JSON", "*.json")])
        if f:
            with open(f, "r") as file:
                self.frames = json.load(file)["frames"]
                self.current_frame_index = 0
                self.update_timeline()

    # =========================================================================
    # EXPORTATION INTELLIGENTE (BOUCLAGE)
    # =========================================================================
    def export_binaries(self):
        if not self.frames:
            messagebox.showwarning("Vide", "Aucune frame à exporter.")
            return

        # 1. PREPARATION : BOUCLAGE LOGICIEL (Pattern Repeating)
        # On va créer une liste étendue de frames pour remplir l'espace mémoire demandé
        try:
            target_loop_size = self.var_memory_loop.get()
            if target_loop_size < 1: target_loop_size = 64
        except:
            target_loop_size = 64

        # Création de la séquence finale répétée
        final_sequence = []
        user_frames_count = len(self.frames)
        
        # On remplit 'target_loop_size' slots.
        # Si on a 3 frames (A,B,C) et qu'on veut 64 slots :
        # Slot 0 = A, Slot 1 = B, Slot 2 = C, Slot 3 = A... etc.
        for i in range(target_loop_size):
            # L'opérateur modulo (%) permet de boucler indéfiniment sur la liste source
            frame_to_use = self.frames[i % user_frames_count]
            final_sequence.append(frame_to_use)

        # 2. GENERATION DES BINAIRES SUR LA SEQUENCE ETENDUE
        data_TL = bytearray()
        data_TR = bytearray()
        data_BL = bytearray()
        data_BR = bytearray()
        
        bit_rev = self.var_bit_reversal.get()
        flip_x = self.var_flip_x.get()
        flip_y = self.var_flip_y.get()
        inv_pol = self.var_invert_output.get()
        offset_val = self.var_offset.get()

        for frame in final_sequence:
            
            def process_8x8_block(start_row, start_col):
                block_bytes = []
                # Lecture brute (gestion Flip Y incluse ici)
                rows_range = range(start_row + 7, start_row - 1, -1) if flip_y else range(start_row, start_row + 8)
                
                raw_rows = []
                for r in rows_range:
                    row_pixels = frame[r][start_col : start_col + 8]
                    if flip_x: row_pixels = row_pixels[::-1]
                    raw_rows.append(row_pixels)
                
                # Correction Offset (Décalage Circulaire)
                dq_rows = deque(raw_rows)
                dq_rows.rotate(offset_val)
                shifted_rows = list(dq_rows)

                # Encodage Byte
                for row_pixels in shifted_rows:
                    if inv_pol: row_pixels = [0 if p else 1 for p in row_pixels]
                    byte_val = 0
                    for i, pixel in enumerate(row_pixels):
                        if pixel:
                            shift = (7 - i) if bit_rev else i
                            byte_val |= (1 << shift)
                    block_bytes.append(byte_val)
                return block_bytes

            data_TL.extend(process_8x8_block(0, 0))
            data_TR.extend(process_8x8_block(0, 8))
            data_BL.extend(process_8x8_block(8, 0))
            data_BR.extend(process_8x8_block(8, 8))

        # 3. ECRITURE
        base_name = filedialog.asksaveasfilename(title="Enregistrer Binaires", defaultextension=".bin")
        if base_name:
            if base_name.lower().endswith('.bin'): base_name = base_name[:-4]
            try:
                with open(f"{base_name}_TL.bin", "wb") as f: f.write(data_TL)
                with open(f"{base_name}_TR.bin", "wb") as f: f.write(data_TR)
                with open(f"{base_name}_BL.bin", "wb") as f: f.write(data_BL)
                with open(f"{base_name}_BR.bin", "wb") as f: f.write(data_BR)
                
                msg = (f"Export réussi !\n\n"
                       f"Frames dessinées : {user_frames_count}\n"
                       f"Frames générées : {target_loop_size} (Bouclage auto)\n"
                       f"Taille totale : {len(data_TL)} octets par EEPROM")
                messagebox.showinfo("Succès", msg)
            except Exception as e:
                messagebox.showerror("Erreur", str(e))

if __name__ == "__main__":
    root = tk.Tk()
    app = MatrixStudioApp(root)
    root.mainloop()