import argparse, datetime, os, random, sqlite3, subprocess, time

# optional arguments
parser = argparse.ArgumentParser(description=None)
parser.add_argument("-t", "--test",
                    type=int,
                    default=0,
                    help="Integer: 1 for test run (values are not committed to database).")
parser.add_argument("-db", "--database",
                    type=str,
                    default="pilot.db",
                    help="String: define database file (.db).")
args = parser.parse_args()


"""MAIN PROGRAM
queries user for input and writes data to SQL database"""

def init():
    # connect to SQL database
    db = sqlite3.connect(args.database)
    db.isolation_level = "DEFERRED"

    # create tables from schema if not exist
    [db.execute(x) for x in open("../sql_schema.txt","r").read().split(";")]

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
def randomise_id(db: sqlite3.Connection):
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
def commit(db: sqlite3.Connection):
    if args.test==0:
        db.commit()
        print("\n"+f"Data committed to {args.database}.")
    else:
        db.rollback()
        print("\n"+"Data not committed (in test mode).")


"""PART 1: COMPUTERISED TASKS"""

# map of computerised tasks
task_map = {
    0: "Harjoitusteht??v??",
    1: "Verkkopankkiteht??v??",
    2: "Verkkokyselyteht??v??",
    3: "Tiedostonjakoteht??v??",
    4: "Laskun sy??tt??",
    5: "Ohjelmiston asennus",
    6: "Tekstink??sittelyteht??v??",
    7: "Taulukkolaskentateht??v??",
    8: "Ty??paikkailmoitus",
    9: "Vakuutusteht??v??",
    10: "Tiedonhakuteht??v??",
    11: "Kela -teht??v??",
    12: "Navigointiteht??v??",
    13: "S??hk??postiteht??v??",
    14: "Lomakkeenhakuteht??v??",
    15: "Komentoriviteht??v??",
    16: "CAPTCHA -teht??v??",
    17: "Videopuheluteht??v??"
}


# TASKS trial
def trial_tasks(db: sqlite3.Connection, identifier: int):
    # NASA-TLX intro
    change_slide(2)

    # randomise tasks
    task_order = randomise_tasks([[x for x in task_map][1:],[]])  # all but practice task
    print("\r"+"Randomised order:"+"\n")
    for i, x in enumerate(task_order):
        print(i+1, f": {task_map[x]}")
    # insert practice task to beginning
    task_order.insert(0,0)

    # loop through each task
    for i, x in enumerate(task_order):
        # 2 min break half-way
        if i==10:
            print("\n"+"2 minute break!")
            os.system('say "tauko"')
            remaining = 120
            begin = time.time()
            change_slide(24)
            while remaining>0:
                min, sec = divmod(remaining,60)
                print(f"Time remaining: {min:0>2d}:{sec:0>2d}", end="\r")  # terminal timer
                time.sleep(1)
                remaining -= 1
            print("Break over. Continue tasks...")
            os.system('say "tauko ohi"')
        # enter to begin task
        input("\n"+f"ENTER to begin task {i} : {task_map[x]}")
        # display task instructions + start timer on enter
        change_slide(x+3)   # slide 1 welcome, 2 nasa-tlx, 3 practice task, 4-21 tasks, 22-23 questionnaire, 24 break
        # count down from three minutes
        begin = time.time()
        timestamp = datetime.datetime.now()
        remaining = 180
        # timer = subprocess.Popen("exec python timer.py", shell=True)  # on-screen timer
        # subprocess.Popen(["osascript", "-e", 'activate application "Terminal"'])  # reactivate main program window
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
                if remaining==30:
                    print('\a')  # alert bell for 30s left
                    remaining -= 2  # temp fix for system voice time delay
            # CTRL+C to interrupt task
            except KeyboardInterrupt:
                end = time.time()
                # timer.kill()  # kill on-screen timer
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
        # kill on-screen timer (if still running)
        # timer.kill()
        # rounded elapsed time for display
        min, sec = divmod(round(elapsed),60)
        print("\r"+f"Task failed! Time elapsed: {min:0>2d}:{sec:0>2d}") if success is False else print("\r"+f"Task successful! Time elapsed: {min:0>2d}:{sec:0>2d}")
        # NASA-TLX
        change_slide(2)  # nasa-tlx
        print("--- NASA-TLX ---")
        nasa_tlx = []
        nasa_dims = ["Henkinen vaativuus","Fyysinen vaativuus","Ajallinen vaativuus","Oma suoriutuminen","Vaivann??k??","Turhautuneisuus"]
        for y in nasa_dims:
            try:
                nasa_tlx.append(int(input(f"{y}: ")))
            # prevent program exit if empty score entered
            except:
                # missing data sent to database as 0
                nasa_tlx.append(0)
        # write task results to database (exclude practice task)
        if i!=0:
            try:
                db.execute("INSERT INTO Tasks (task_no,participant_id,begin,success,time_elapsed) VALUES (?,?,?,?,?)",[x,identifier,timestamp,success,elapsed])
                db.execute("INSERT INTO LoadNasa (task_no,participant_id,hv,fv,av,os,vn,tur) VALUES (?,?,?,?,?,?,?,?)",[x,identifier,nasa_tlx[0],nasa_tlx[1],nasa_tlx[2],nasa_tlx[3],nasa_tlx[4],nasa_tlx[5]])
            except:
                print("\n"+"SQL error: record data on paper!")
    # complete
    change_slide(22)
    # commit changes if not in test mode
    commit(db)


"""QUESTIONNAIRE"""

# covariate questionnaire (take integer inputs to avoid mislabelling)
def questionnaire(db: sqlite3.Connection, identifier: int):
    # list for digitising questionnaire answers
    qs = []
    for i in range(26):  # number of questions
        if i==14:
            change_slide(23)  # second page of questionnaire
        try:
            qs.append(int(input(f"Q{i+1}: ")))
        # prevent program exit if empty score entered
        except:
            # missing data sent to database as 0
            qs.append(0)
            print("Nothing entered; writing 0. Take note.")
    # map covariate values where text labels: input -> database label
    gender_map = {0: "NA", 1: "mies", 2: "nainen", 3: "muu"}
    ed_map = {0: "NA", 1: "perusaste", 2: "keskiaste", 3: "alempi", 4: "ylempi"}
    eng_map = {0: "NA", 1: "alkeet", 2: "hyv??", 3: "sujuva", 4: "??idinkieli"}
    exp_map = {0: "NA", 1: "aloittelija", 2: "arkik??ytt??j??", 3: "asiantuntija"}
    os_map = {0: "NA", 1: "linux", 2: "macos", 3: "windows", 4: "muu"}
    browser_map = {0: "NA", 1: "chrome", 2: "microsoft", 3: "firefox", 4: "safari", 5: "muu"}
    # write to database
    # general questions
    try:
        db.execute("INSERT INTO Participants (identifier,age,hrs_pc,hrs_mob,gender,ed,eng,exp,os,browser) VALUES (?,?,?,?,?,?,?,?,?,?)",[identifier,qs[0],qs[1],qs[2],gender_map[qs[3]],ed_map[qs[4]],eng_map[qs[5]],exp_map[qs[6]],os_map[qs[7]],browser_map[qs[8]]])
    except:
        print("\n"+"SQL error: record data on paper!")
    # task-specific questions
    for i, x in enumerate(qs[9:]):
        try:
            db.execute(f"UPDATE Participants SET t{i+1}=? WHERE identifier=?",[x,identifier])
        except:
            print("\n"+f"SQL error for t{i+1}: record data on paper!")
    # complete
    change_slide(1)
    # commit changes if not in test mode
    commit(db)


"""PART 2: POT TESTS"""

# independent POT trial for each participant
# TO DO
def trial_pot(db: sqlite3.Connection, identifier: int):
    pass
    # commit changes if not in test mode
    # commit(db)


if __name__ == "__main__":
    init()
