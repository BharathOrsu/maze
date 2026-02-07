import tkinter as tk
from tkinterdnd2 import TkinterDnD, DND_FILES
import shutil
import os

class GUI:
    def __init__(self):
        self.root = TkinterDnD.Tk()
        self.root.title("Maze Solver")
        self.root.geometry("520x350")
        self.setup_ui()

    def setup_ui(self):
        solve_button = tk.Button(self.root, text="Solve Maze", command=self.solve_maze)
        solve_button.pack(pady=20)
        
        drop_label = tk.Label(self.root, text="Drag and Drop Image Here", relief="ridge", width=40, height=4)
        drop_label.pack(pady=10)
        drop_label.drop_target_register(DND_FILES)
        drop_label.dnd_bind("<<Drop>>", self.handle_drop)

    def handle_drop(self, event):
        dropped_files = event.data.strip()
        file_paths = self.root.tk.splitlist(dropped_files)
        for file_path in file_paths:
            if os.path.isfile(file_path):
                shutil.copy(file_path, 'input_folder')
    
    def solve_maze(self):
        print("Solving the maze...")
        pass
