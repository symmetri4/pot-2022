import argparse, random, sqlite3, time

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
    # write to database
    try:
        db.execute("INSERT INTO Participants (identifier,trial_no) VALUES (?,(SELECT IFNULL(MAX(trial_no),0)+1 FROM Participants))",[identifier])
    except:
        print("\n"+"SQL error: record data on paper!")

    # initiate trial part 1: tasks
    print("\n"+"--- Part 1: Computerised Tasks ---"+"\n")
    trial_tasks(db,identifier)

    # initiate trial part 2: pot tests
    print("\n"+"--- Part 2: POT Tests ---"+"\n")
    trial_pot(db,identifier)

    # close connection to database
    db.close()


"""PART 1: COMPUTERISED TASKS"""

# map of computerised tasks
task_map = {
    1: "task1 name",
    2: "task2 name",
    3: "task3 name",
    4: "task4 name",
    5: "task5 name",
    6: "task6 name",
    7: "task7 name",
    8: "task8 name",
    9: "task9 name",
    10: "task10 name",
    11: "task11 name",
    12: "task12 name"
}


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


# independent TASKS trial for each participant
def trial_tasks(db, identifier: int):
    # randomise tasks
    task_order = randomise([[x for x in task_map],[]])
    print("Randomised order:"+"\n")
    for i, x in enumerate(task_order):
        print(i+1, f": {task_map[x]}")

    # loop through each task
    for i, x in enumerate(task_order):
        input("\n"+f"ENTER to begin task {i+1}")
        begin = time.time()
        # count down from three minutes
        remaining = 3*60
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
        print("\r"+f"Task failed! Time elapsed: {min:0>2d}:{sec:0>2d}") if remaining==0 else print("\r"+f"Task successful! Time elapsed: {min:0>2d}:{sec:0>2d}")
        # write result to database
        try:
            db.execute("INSERT INTO Tasks (task_no,participant_id,success,time_elapsed) VALUES (?,?,?,?)",[x,identifier,success,elapsed])
        except:
            print("\n"+"SQL error: record data on paper!")
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
