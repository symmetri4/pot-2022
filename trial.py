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
   
    # allocate id
    identifier = randomise_id(db)
    print(f"Randomised ID (take note!): {identifier}")
    # write trial to database
    try:
        db.execute("INSERT INTO Trials (participant_id) VALUES (?)",[identifier])
    except:
        print("\n"+"SQL error: record data on paper!")
    # commit to database
    commit(db)

    # initiate trial part 1: tasks
    print("\n"+"--- Part 1: Computerised Tasks ---"+"\n")
    trial_tasks(db,identifier)

    # covariate questionnaire
    print("\n"+"--- Covariate questionnaire ---"+"\n")
    questionnaire(db,identifier)

    # initiate trial part 2: pot tests
    print("\n"+"--- Part 2: POT Tests ---"+"\n")
    trial_pot(db,identifier)

    # close connection to database
    db.close()


"""Helper functions"""

# allocate participant random id X
# read existing ids from SQL database
# sample X from discrete uniform distribution where X in {1,2,...,100}-{[list of existing ids]}
def randomise_id(db):
    # get ids
    fetch_ids = db.execute("SELECT identifier FROM Participants").fetchall()
    ids = [x[0] for x in fetch_ids]
    # return random id excluding existing ids
    return random.choice(list(set([x for x in range(1,101)])-set(ids)))


# recursive function for randomising tasks
# input nested list [[task_list],[]]
# output [randomised_tasks]
def randomise_tasks(tasks: list):
    # sample from uniform distribution
    index = random.randint(0,len(tasks[0])-1)
    # move a task from tasks[0] to tasks[1] using random index
    tasks[1].append(tasks[0].pop(index))
    # call function unless tasks[0] empty
    return tasks[1] if len(tasks[0])==0 else randomise_tasks(tasks)


# change powerpoint slide
# TO DO: create custom presentation from randomised task list and run slide show
def change_slide(slide_no: int):
    subprocess.Popen(["osascript", "-e", f'''
        tell application "Microsoft PowerPoint"
          tell active presentation
            select slide {slide_no}
          end tell
        end tell'''])


# commit changes to database
# or rollback if in test mode
def commit(db):
    if args.test==0:
        db.commit()
        print("\n"+f"Data committed to {args.database}.")
    else:
        db.rollback()
        print("\n"+"Data not committed (in test mode).")


"""PART 1: COMPUTERISED TASKS"""

# map of computerised tasks
task_map = {
    0: "Harjoitustehtävä",
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


# TASKS trial
def trial_tasks(db, identifier: int):
    # display NASA-TLX for training
    change_slide(2)

    # randomise tasks
    task_order = randomise_tasks([[x for x in task_map][1:13],[]])  # randomise all but practice task
    print("\r"+"Randomised order:"+"\n")
    for i, x in enumerate(task_order):
        print(i+1, f": {task_map[x]}")
    # insert practice task to beginning
    task_order.insert(0,0)

    # loop through each task
    for i, x in enumerate(task_order):
        input("\n"+f"ENTER to begin task {i} : {task_map[x]}")
        # display task instructions + start timer on enter
        change_slide(x+3)   # slide 1 welcome, slide 2 nasa-tlx, slide 3 practice task, slides 4-15 tasks
        # count down from three minutes
        begin = time.time()
        remaining = 180
        timer = subprocess.Popen("exec python timer.py", shell=True)  # on-screen timer
        subprocess.Popen(["osascript", "-e", 'activate application "Terminal"'])  # reactivate main program window
        # default values below stored to database if task fail
        success = False
        elapsed = remaining
        # task in progress
        while remaining>0:
            try:
                min, sec = divmod(remaining,60)
                print(f"Time remaining: {min:0>2d}:{sec:0>2d}", end="\r")  # terminal timer
                time.sleep(1)
                remaining -= 1
            # CTRL+C to interrupt task
            except KeyboardInterrupt:
                end = time.time()
                # query whether task success/fail
                try:
                    success = int(input("\r"+"Task success (1 success 0 fail): "))
                # prevent program exit if empty score entered
                except:
                    # default to success and warn about missing data
                    success = 1
                    print("Nothing entered. Defaulting to success. Take note if task result fail.")
                success = True if success==1 else False
                # elapsed time rounded to nearest millisecond
                elapsed = round(end-begin,3)
                break
        # kill on-screen timer
        timer.kill()
        # rounded elapsed time for display
        min, sec = divmod(round(elapsed),60)
        print("\r"+f"Task failed! Time elapsed: {min:0>2d}:{sec:0>2d}") if success is False else print("\r"+f"Task successful! Time elapsed: {min:0>2d}:{sec:0>2d}")
        # NASA-TLX
        change_slide(2)  # nasa-tlx
        nasa_tlx = []
        nasa_dims = ["Mental demand","Pysical demand","Temporal demand","Performance","Effort","Frustration"]
        for y in nasa_dims:
            try:
                nasa_tlx.append(int(input(f"{y}: ")))
            # prevent program exit if empty score entered
            except:
                # missing data sent to database as 0
                nasa_tlx.append(0)
        # write result to database (exclude practice task)
        if i!=0:
            try:
                db.execute("INSERT INTO Tasks (task_no,participant_id,success,time_elapsed) VALUES (?,?,?,?)",[x,identifier,success,elapsed])
                db.execute("INSERT INTO LoadNasa (task_no,participant_id,mental_demand,physical_demand,temporal_demand,performance,effort,frustration) VALUES (?,?,?,?,?,?,?,?)",[x,identifier,nasa_tlx[0],nasa_tlx[1],nasa_tlx[2],nasa_tlx[3],nasa_tlx[4],nasa_tlx[5]])
            except:
                print("\n"+"SQL error: record data on paper!")
    
    # complete
    change_slide(16)
    # commit changes if not in test mode
    commit(db)


"""QUESTIONNAIRE"""

# covariate questionnaire (take integer inputs to avoid mislabelling)
def questionnaire(db, identifier: int):
    # TO DO: add some map for covariates and loop through all
    #        making sure that errors do not cause program to exit
    age = int(input("Age: "))
    exp = int(input("Experience (1 Novice, 2 Casual, 3 Expert): "))  # computer experience
    pri_os = int(input("Primary OS (1 Linux, 2 Windows, 3 Macos, 4 Other): "))  # primary os used
    # .
    # .
    # . task-specific questions, etc.
    # map covariate values: input -> database label
    exp_map = {1: "novice", 2: "casual", 3: "expert"}
    os_map = {1: "linux", 2: "windows", 3: "macos", 4: "other"}
    # write to database
    try:
        db.execute("INSERT INTO Participants (identifier,age,experience,primary_os) VALUES (?,?,?,?)",[identifier,age,exp_map[exp],os_map[pri_os]])
    except:
        print("\n"+"SQL error: record data on paper!")
    # commit changes if not in test mode
    commit(db)


"""PART 2: POT TESTS"""

# independent POT trial for each participant
# TO DO
def trial_pot(db, identifier: int):
    pass
    # commit changes if not in test mode
    # commit(db)


if __name__ == "__main__":
    init()
