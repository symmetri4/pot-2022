import argparse, random, sqlite3, subprocess, time

# optional arguments
parser = argparse.ArgumentParser(description=None)
parser.add_argument("-t", "--test",
                    type=int,
                    default=0,
                    help="Integer: 1 for test run (values are not committed to database).")
parser.add_argument("-db", "--database",
                    type=str,
                    default="pot.db",
                    help="String: define database file (.db).")
args = parser.parse_args()


"""MAIN PROGRAM
queries user for input and writes data to SQL database"""

def init():
    # connect to SQL database
    db = sqlite3.connect(args.database)
    db.isolation_level = "DEFERRED"

    # create tables from schema if not exist
    [db.execute(x) for x in open("sql_schema.txt","r").read().split(";")]

    print("\n"+"--- NEW TRIAL COMMENCED ---"+"\n")
   
    # participant details
    identifier = int(input("Participant identifier: "))
    # covariates (take integer inputs to avoid mislabelling)
    age = int(input("Age: "))
    exp = int(input("Experience (1 Novice, 2 Casual, 3 Expert): "))  # computer experience
    pri_os = int(input("Primary OS (1 Linux, 2 Windows, 3 Macos, 4 Other): "))  # primary os used
    # map covariate values: input -> database label
    exp_map = {1: "novice", 2: "casual", 3: "expert"}
    os_map = {1: "linux", 2: "windows", 3: "macos", 4: "other"}
    # write to database
    try:
        db.execute("INSERT INTO Trials (participant_id) VALUES (?)",[identifier])
        db.execute("INSERT INTO Participants (identifier,age,experience,primary_os) VALUES (?,?,?,?)",[identifier,age,exp_map[exp],os_map[pri_os]])
    except:
        print("\n"+"SQL error: record data on paper!")

    # initiate trial part 1: tasks
    print("\n"+"--- Part 1: Computerised Tasks ---"+"\n")
    practice_task()  # practice task
    trial_tasks(db,identifier)

    # initiate trial part 2: pot tests
    print("\n"+"--- Part 2: POT Tests ---"+"\n")
    trial_pot(db,identifier)

    # close connection to database
    db.close()


"""Helper functions"""

# recursive function for randomising tasks
# input nested list [[task_list],[]]
# output [randomised_tasks]
def randomise(tasks: list):
    # sample from uniform distribution
    index = random.randint(0,len(tasks[0])-1)
    # move a task from tasks[0] to tasks[1] using random index
    tasks[1].append(tasks[0].pop(index))
    # call function unless tasks[0] empty
    return tasks[1] if len(tasks[0])==0 else randomise(tasks)


# change powerpoint slide
# TO DO: create custom presentation from randomised task list and run slide show
def change_slide(slide_no: int):
    subprocess.Popen(['osascript', '-e', f'''
        tell application "Microsoft PowerPoint"
          tell active presentation
            select slide {slide_no}
          end tell
        end tell'''])


# start timer (participant display)
# TO DO: Python timer - current solution looks awful
# mode 1 enter starts/cancels timer, anything else esc for resetting if timer depleted
def screen_timer(mode: int):
    key = 36 if mode==1 else 53
    subprocess.Popen(['osascript', '-e', f'''
        tell application "AS Timer"
          activate
          tell application "System Events" to key code {key}
        end tell
        activate application "Terminal"'''])


# practice task
# TO DO: integrate this into trial_tasks -function, this is just quick fix for pilot
def practice_task():
    input("ENTER to begin practice task")
    print()
    change_slide(2)
    begin = time.time()
    screen_timer(1)
    try:
        time.sleep(180)
        time.sleep(3)
        screen_timer(0)
        time.sleep(1)
        screen_timer(1)
    except KeyboardInterrupt:
        screen_timer(1)
    change_slide(3)


"""PART 1: COMPUTERISED TASKS"""

# map of computerised tasks
task_map = {
    1: "Verkkopankkitehtävä",
    2: "Verkkolomaketehtävä",
    3: "Tiedostonjakotehtävä",
    4: "Laskun syöttö",
    5: "Ohjelmiston asennus",
    6: "Tekstinkäsittelytehtävä",
    7: "Taulukkolaskentatehtävä",
    8: "Myynti-ilmoitus",
    9: "Vakuutustehtävä",
    10: "Tiedonhakutehtävä",
    11: "CAPTCHA -tehtävä",
    12: "Sähköpostitehtävä"
}


# independent TASKS trial for each participant
def trial_tasks(db, identifier: int):
    # randomise tasks
    task_order = randomise([[x for x in task_map],[]])
    print("\r"+"Randomised order:"+"\n")
    for i, x in enumerate(task_order):
        print(i+1, f": {task_map[x]}")
    
    # loop through each task (including practice task)
    for i, x in enumerate(task_order):
        input("\n"+f"ENTER to begin task {i+1} : {task_map[x]}")
        # display instructions + start timer
        change_slide(x+3)   # slide 1 welcome, slide 2 practice task, slide 3 nasa-tlx, slides 4-15 tasks
        screen_timer(1)
        # count down from three minutes
        begin = time.time()
        remaining = 180
        # default values below stored to database if task fail
        success = False
        elapsed = remaining
        # task in progress
        while remaining>0:
            try:
                min, sec = divmod(remaining,60)
                print(f"Time remaining: {min:0>2d}:{sec:0>2d}", end="\r")
                time.sleep(1)
                remaining -= 1
            # CTRL+C to interrupt task (=> task success)
            except KeyboardInterrupt:
                success = True
                end = time.time()
                # elapsed time rounded to nearest millisecond
                elapsed = round(end-begin,3)
                break
        # rounded elapsed time for display
        min, sec = divmod(round(elapsed),60)
        if remaining==0:
            print("\r"+f"Task failed! Time elapsed: {min:0>2d}:{sec:0>2d}")
            # reset timer if depleted (wait due to latency in app)
            time.sleep(3)
            screen_timer(0)
            time.sleep(1)
            screen_timer(1)
        else:
            print("\r"+f"Task successful! Time elapsed: {min:0>2d}:{sec:0>2d}")
            # cancel timer if success
            screen_timer(1)
        # print("\r"+f"Task failed! Time elapsed: {min:0>2d}:{sec:0>2d}") if remaining==0 else print("\r"+f"Task successful! Time elapsed: {min:0>2d}:{sec:0>2d}")
        # NASA-TLX
        change_slide(3)  # nasa-tlx
        nasa_tlx = []
        nasa_dims = ["Mental demand","Pysical demand","Temporal demand","Performance","Effort","Frustration"]
        for y in nasa_dims:
            try:
                nasa_tlx.append(int(input(f"{y}: ")))
            except:
                # prevent program exit if empty score entered
                nasa_tlx.append(0)
        # write result to database
        try:
            db.execute("INSERT INTO Tasks (task_no,participant_id,success,time_elapsed) VALUES (?,?,?,?)",[x,identifier,success,elapsed])
            db.execute("INSERT INTO LoadNasa (task_no,participant_id,mental_demand,physical_demand,temporal_demand,performance,effort,frustration) VALUES (?,?,?,?,?,?,?,?)",[x,identifier,nasa_tlx[0],nasa_tlx[1],nasa_tlx[2],nasa_tlx[3],nasa_tlx[4],nasa_tlx[5]])
        except:
            print("\n"+"SQL error: record data on paper!")
    
    # complete
    change_slide(16)
    # commit changes if not in test mode
    if args.test==0:
        db.commit()
        print("\n"+f"Part 1 complete! Data committed to {args.database}.")
    else:
        db.rollback()
        print("\n"+"Part 1 complete! Data not committed (in test mode).")


"""PART 2: POT TESTS"""

# independent POT trial for each participant
# TO DO
def trial_pot(db, identifier: int):
    pass
    # commit changes if not in test mode
    # if args.test==0:
    #     db.commit()
    #     print("\n"+f"Part 2 complete! Data committed to {args.database}.")
    # else:
    #     db.rollback()
    #     print("\n"+"Part 2 complete! Data not committed (in test mode).")


if __name__ == "__main__":
    init()
