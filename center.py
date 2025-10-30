import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk
import random
import pygame
import threading
import time

# --- AUDIO SETUP ---
pygame.mixer.init()
pygame.mixer.music.load("background_music.mp3")
pygame.mixer.music.play(-1)
pygame.mixer.music.set_volume(0.5)

dice_roll_sound = pygame.mixer.Sound("dice_roll.mp3")
snake_hiss_sound = pygame.mixer.Sound("snake_hiss.mp3")

dice_roll_sound.set_volume(0.5)
snake_hiss_sound.set_volume(1.0)

# --- GAME ELEMENTS ---
snakes = {44: 22, 46: 15, 48: 9, 52: 11, 59: 18, 64: 24, 68: 2, 69: 33, 83: 22, 92: 51, 95: 37, 98: 13}
ladders = {8: 26, 19: 38, 21: 82, 28: 53, 36: 57, 43: 77, 50: 91, 54: 88, 62: 96, 66: 87, 80: 99}

def toggle_music():
    if pygame.mixer.music.get_busy():
        pygame.mixer.music.pause()
    else:
        pygame.mixer.music.unpause()

def set_volume(val):
    pygame.mixer.music.set_volume(float(val))

def show_congratulations_popup(winner_name):
    popup = tk.Toplevel()
    popup.title("Congratulations!")
    popup.configure(bg="#FFFACD")
    popup.attributes("-topmost", True)
    popup.grab_set()

    popup_width, popup_height = 500, 500
    x = (popup.winfo_screenwidth() - popup_width) // 2
    y = (popup.winfo_screenheight() - popup_height) // 2
    popup.geometry(f"{popup_width}x{popup_height}+{x}+{y}")
    popup.resizable(False, False)

    canvas = tk.Canvas(popup, width=popup_width, height=popup_height, bg="#FFFACD", highlightthickness=0)
    canvas.pack(fill="both", expand=True)

    try:
        img = Image.open("congrats.jpg").resize((300, 180), Image.Resampling.LANCZOS)
        img_photo = ImageTk.PhotoImage(img)
        canvas.create_image(popup_width//2, 110, image=img_photo)
        canvas.image = img_photo
    except Exception as e:
        print("Image not found:", e)

    canvas.create_text(popup_width//2, 230, text=f"🎉 Congratulations, {winner_name}! 🎉",
                       font=("Arial", 18, "bold"), fill="#2E8B57")

    close_btn = tk.Button(popup, text="Close", command=popup.destroy,
                          font=("Arial", 12), bg="#90EE90")
    canvas.create_window(popup_width//2, 280, window=close_btn)

    popup.attributes("-alpha", 0.0)
    fade_in(popup)
    start_confetti(canvas, popup_width, popup_height)

def fade_in(window, alpha=0.0):
    alpha += 0.05
    if alpha <= 1.0:
        window.attributes("-alpha", alpha)
        window.after(30, lambda: fade_in(window, alpha))

def start_confetti(canvas, width, height):
    colors = ["red", "yellow", "green", "blue", "magenta", "orange", "purple"]
    particles = []
    for _ in range(50):
        x = random.randint(0, width)
        y = random.randint(-200, 0)
        r = random.randint(4, 8)
        color = random.choice(colors)
        circle = canvas.create_oval(x, y, x + r, y + r, fill=color, outline="")
        particles.append((circle, random.randint(2, 6)))

    def animate():
        for _ in range(50):
            for circle, speed in particles:
                canvas.move(circle, 0, speed)
            canvas.update()
            time.sleep(0.05)

    threading.Thread(target=animate, daemon=True).start()

# --- GAME CLASS ---
class SnakeLadderGame:
    def __init__(self, parent, player1, player2):
        self.root = parent
        self.root.pack(fill="both", expand=True)
        self.screen_width = self.root.winfo_screenwidth()
        self.screen_height = self.root.winfo_screenheight()
        self.player_names = [player1, player2]

        bg_image = Image.open("dicebg.jpg").resize((self.screen_width, self.screen_height))
        self.bg_photo = ImageTk.PhotoImage(bg_image)
        self.bg_label = tk.Label(self.root, image=self.bg_photo)
        self.bg_label.place(x=0, y=0, relwidth=1, relheight=1)

        self.board_size = min(self.screen_height * 0.98, self.screen_width * 0.6)
        self.board = tk.Canvas(self.root, width=self.board_size, height=self.board_size, bg='white')
        self.board.place(x=0, y=0)

        self.dice_images = [ImageTk.PhotoImage(Image.open(f"dice{i}.jpg").resize((60, 60))) for i in range(1, 7)]

        self.status = tk.Label(self.root, text=f"{player1}'s turn.", font=('Arial', 18), bg='black', fg='white')
        self.status.place(x=self.board_size + 20, y=20)

        self.player1_label = tk.Label(self.root, text=player1, font=('Arial', 14), bg='black', fg='white')
        self.player1_label.place(x=self.board_size + 50, y=80)
        self.dice1_label = tk.Label(self.root, image=self.dice_images[0], bg='white')
        self.dice1_label.place(x=self.board_size + 50, y=120)

        self.player2_label = tk.Label(self.root, text=player2, font=('Arial', 14), bg='black', fg='white')
        self.player2_label.place(x=self.board_size + 50, y=self.screen_height - 160)
        self.dice2_label = tk.Label(self.root, image=self.dice_images[0], bg='white')
        self.dice2_label.place(x=self.board_size + 50, y=self.screen_height - 120)

        self.roll_button = tk.Button(self.root, text="Roll Dice", font=('Arial', 16), command=self.roll_dice)
        self.roll_button.place(x=self.board_size + 50, y=self.screen_height // 2)

        self.load_background("custom_board.jpg")

        self.token1_img = ImageTk.PhotoImage(Image.open("token.jpg").resize((50, 50)))
        self.token2_img = ImageTk.PhotoImage(Image.open("token2.jpg").resize((50, 50)))
        self.player_positions = [1, 1]
        self.current_player = 0
        self.player_pieces = [
            self.board.create_image(*self.get_cell_center(1), image=self.token1_img),
            self.board.create_image(*self.get_cell_center(1), image=self.token2_img)
        ]

        self.dice_history = [[], []]
        self.create_dashboard()

    def load_background(self, file_path):
        bg_img = Image.open(file_path).resize((int(self.board_size), int(self.board_size)))
        self.bg_board = ImageTk.PhotoImage(bg_img)
        self.board.create_image(0, 0, anchor=tk.NW, image=self.bg_board)

    def get_cell_center(self, pos):
        size = self.board_size / 10
        pos -= 1
        row = pos // 10
        col = pos % 10 if row % 2 == 0 else 9 - (pos % 10)
        x = col * size + size / 2
        y = (9 - row) * size + size / 2
        return x, y

    def create_dashboard(self):
        dash_width = 350
        self.dashboard = tk.Frame(self.root, bg="#1C1C1C", bd=2, relief=tk.RIDGE)
        self.dashboard.place(x=self.screen_width - dash_width - 10, y=0, width=dash_width, height=self.screen_height)

        tk.Label(self.dashboard, text="🎲 Dice Rolls", font=("Arial", 20, "bold"), bg="#1C1C1C", fg="white").pack(pady=20)
        self.p1_rolls_label = tk.Label(self.dashboard, text="Player 1:", font=("Arial", 14, "bold"), bg="#222", fg="lightblue")
        self.p1_rolls_label.pack(fill="x", padx=10)
        self.p1_rolls_text = tk.Text(self.dashboard, height=12, font=("Arial", 12), bg="#2E2E2E", fg="white")
        self.p1_rolls_text.pack(fill="x", padx=10)

        self.p2_rolls_label = tk.Label(self.dashboard, text="Player 2:", font=("Arial", 14, "bold"), bg="#222", fg="lightgreen")
        self.p2_rolls_label.pack(fill="x", padx=10)
        self.p2_rolls_text = tk.Text(self.dashboard, height=12, font=("Arial", 12), bg="#2E2E2E", fg="white")
        self.p2_rolls_text.pack(fill="x", padx=10)

    def add_to_dashboard(self, message):
        if self.current_player == 0:
            self.p1_rolls_text.insert("end", message + "\n")
            self.p1_rolls_text.see("end")
        else:
            self.p2_rolls_text.insert("end", message + "\n")
            self.p2_rolls_text.see("end")

    def roll_dice(self):
        roll = random.randint(1, 6)
        dice_roll_sound.play()
        player_num = self.current_player
        player_name = self.player_names[player_num]

        if player_num == 0:
            self.dice1_label.config(image=self.dice_images[roll - 1])
        else:
            self.dice2_label.config(image=self.dice_images[roll - 1])

        roll_msg = f"{player_name} rolled a {roll}"
        self.status.config(text=roll_msg)
        self.add_to_dashboard(roll_msg)

        next_pos = self.player_positions[player_num] + roll
        if next_pos > 100:
            self.add_to_dashboard(f"{player_name} can't move.")
            self.next_player()
            return

        if next_pos in ladders:
            next_pos = ladders[next_pos]
            self.add_to_dashboard(f"{player_name} climbed ladder to {next_pos}")
        elif next_pos in snakes:
            snake_hiss_sound.play()
            next_pos = snakes[next_pos]
            self.add_to_dashboard(f"{player_name} bitten by snake to {next_pos}")

        self.player_positions[player_num] = next_pos
        self.update_player_position(player_num)

        if next_pos == 100:
            self.status.config(text=f"{player_name} wins!")
            self.add_to_dashboard(f"{player_name} wins!")
            self.roll_button.config(state=tk.DISABLED)
            show_congratulations_popup(player_name)
            return

        self.next_player()

    def next_player(self):
        self.current_player = 1 - self.current_player
        self.status.config(text=f"{self.player_names[self.current_player]}'s turn.")

    def update_player_position(self, player_index):
        x, y = self.get_cell_center(self.player_positions[player_index])
        offset = -10 if player_index == 0 else 10
        self.board.coords(self.player_pieces[player_index], x + offset, y)

# --- MODIFIED NAME ENTRY SCREEN ---
def get_player_names():
    win = tk.Toplevel(root)
    win.title("Enter Names")
    win_width, win_height = 400, 300
    sw, sh = root.winfo_screenwidth(), root.winfo_screenheight()
    x = (sw - win_width) // 2
    y = (sh - win_height) // 2
    win.geometry(f"{win_width}x{win_height}+{x}+{y}")
    win.resizable(False, False)
    win.grab_set()

    try:
        bg_img = Image.open("players_entry.jpg").resize((400, 300), Image.Resampling.LANCZOS)
        bg_photo = ImageTk.PhotoImage(bg_img)
    except Exception as e:
        print("Error loading image:", e)
        messagebox.showerror("Image Error", "Background image not found.")
        return

    canvas = tk.Canvas(win, width=400, height=300)
    canvas.pack(fill="both", expand=True)
    canvas.create_image(0, 0, anchor="nw", image=bg_photo)
    canvas.image = bg_photo

    canvas.create_text(200, 40, text="Enter Player Names", fill="white", font=("Arial", 20, "bold"))
    canvas.create_text(100, 100, text="Player 1: ", fill="white", font=("Arial", 14, "bold"))
    e1 = tk.Entry(win, font=("Arial", 14))
    canvas.create_window(250, 100, window=e1)

    canvas.create_text(100, 160, text="Player 2: ", fill="white", font=("Arial", 14, "bold"))
    e2 = tk.Entry(win, font=("Arial", 14))
    canvas.create_window(250, 160, window=e2)

    names = []

    def submit():
        if e1.get().strip() and e2.get().strip():
            names.extend([e1.get().strip(), e2.get().strip()])
            win.destroy()
        else:
            messagebox.showwarning("Input", "Please enter both names.")

    start_btn = tk.Button(win, text="Start", font=("Arial", 12), bg="#7A5DE8", fg="white", command=submit)
    canvas.create_window(200, 230, window=start_btn)

    win.wait_window()
    return names if names else None

# --- MAIN GAME SETUP ---
def start_game():
    names = get_player_names()
    if not names:
        return
    pygame.mixer.music.stop()
    welcome_frame.pack_forget()
    game_frame.pack(fill="both", expand=True)
    SnakeLadderGame(game_frame, *names)

def show_instructions():
    messagebox.showinfo("Instructions", "🎮 How to Play:\n\n• Roll the dice.\n• Ladders take you up.\n• Snakes pull you down.\n• Reach 100 to win.")

def exit_game():
    pygame.mixer.music.stop()
    root.destroy()

root = tk.Tk()
root.title("Snake and Ladder")
root.attributes("-fullscreen", True)
root.bind("<Escape>", lambda e: root.attributes("-fullscreen", False))

welcome_frame = tk.Frame(root)
game_frame = tk.Frame(root)
welcome_frame.pack(fill="both", expand=True)

sw, sh = root.winfo_screenwidth(), root.winfo_screenheight()
bg = Image.open("snake_ladder_board.jpg").resize((sw, sh), Image.Resampling.LANCZOS)
bg_photo = ImageTk.PhotoImage(bg)
canvas = tk.Canvas(welcome_frame, width=sw, height=sh)
canvas.pack(fill="both", expand=True)
canvas.create_image(0, 0, image=bg_photo, anchor="nw")
canvas.create_text(sw//2, 100, text="🐍 Snake and Ladder 🎲", font=("Comic Sans MS", 36, "bold"), fill="lavender")

button_font = ("Arial", 16)
start_btn = tk.Button(welcome_frame, text="Start Game", font=button_font, bg="#7A5DE8", width=15, command=start_game)
instr_btn = tk.Button(welcome_frame, text="Instructions", font=button_font, bg="#524C9D", width=15, command=show_instructions)
exit_btn = tk.Button(welcome_frame, text="Exit", font=button_font, bg="#B04A5A", width=15, command=exit_game)
canvas.create_window(sw//2, sh//2 - 80, window=start_btn)
canvas.create_window(sw//2, sh//2, window=instr_btn)
canvas.create_window(sw//2, sh//2 + 80, window=exit_btn)

mute_btn = tk.Button(welcome_frame, text="🔇 Mute / Unmute", font=("Arial", 12), command=toggle_music)
volume_slider = tk.Scale(welcome_frame, from_=0, to=1, resolution=0.1, orient=tk.HORIZONTAL, command=set_volume)
volume_slider.set(0.5)
canvas.create_window(sw - 150, 30, window=mute_btn)
canvas.create_window(sw - 150, 80, window=volume_slider)

root.mainloop()
