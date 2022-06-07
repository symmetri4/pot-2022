import time, tkinter

# on-screen timer
timer = tkinter.Tk()
timer.geometry(f"450x200-{timer.winfo_screenwidth()}+0")  # offset to left monitor
timer.attributes('-topmost', 1)  # keep window on top of instructions
timer.title("timer")
timer.configure(bg="black")
timerText = tkinter.StringVar(timer)
tkinter.Entry(timer,width=5,font=("Arial",150),textvariable=timerText,justify="center",fg="black",bd=0).place(x=10,y=10)

# count down from 3 minutes
remaining = 180
# task in progress
while remaining>0:
    min, sec = divmod(remaining,60)
    timerText.set(f"{min:0>2d}:{sec:0>2d}")  # on-screen timer
    timer.update()
    time.sleep(1)
    remaining -= 1
