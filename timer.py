import tkinter as tk


def update_timer():
    min, sec = divmod(remaining,60)
    timer_text = f'{str(min).zfill(2)}:{str(sec).zfill(2)}'
    canvas.itemconfigure(timer, text=timer_text)
    main.after(1000, _decrease_time)


def _decrease_time():
    global remaining
    remaining -= 1
    update_timer()


try:
    main = tk.Tk()
    main.geometry(f"1200x300-{main.winfo_screenwidth()}+0")  # offset to left monitor
    main.attributes('-topmost', 1)  # keep window on top of instructions
    main.title("timer")
    canvas = tk.Canvas(main, width=1200, height=300, bg='black')
    canvas.pack()
    # start time (in seconds)
    remaining = 180
    timer = canvas.create_text(600, 150, font=('', 200), fill='white')
    update_timer()
    main.mainloop()
# avoid errors in trial.py
# (CTRL+C used to interrupt task)
except KeyboardInterrupt:
    pass
