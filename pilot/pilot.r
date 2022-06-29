###
# --- functionality ---
# graph time elapsed by task: tet()
# graph time elapsed by participant: pet()
# graph nasa-tlx: smw()
# export SQL tables to CSV: csv()
###

library(DBI)  # reference: https://db.rstudio.com/databases/sqlite/

# connect to pilot.db
con <- dbConnect(RSQLite::SQLite(), "pilot.db")

# create dirs if not exist
dir.create("pilot_graphs", showWarnings=FALSE)
dir.create("pilot_csv", showWarnings=FALSE)

# boxplots: elapsed time (inc. task success) by task
tet <- function() {
    # store task success data
    task_success <- c()
    # store boxplot cols (based on success rate)
    cols <- c()
    for (i in seq(1,17)) {  # useful: sort(unique(tasks$task_no))
        # durs
        durs <- dbGetQuery(con, paste("SELECT time_elapsed as x FROM Tasks WHERE task_no=",i,sep=""))$x
        eval(parse(text=paste("t",i," <- durs",sep="")))
        # successes
        successes <- dbGetQuery(con, paste("SELECT success as x FROM Tasks WHERE task_no=",i,sep=""))$x
        task_success <- append(task_success, sum(successes)/length(successes)*100)
        # append appropriate col
        if (task_success[i]<10 || task_success[i]>90) cols <- append(cols, "#cc3333") # red if success % in [0,10)U(90,100]
        else if (task_success[i]>=10 & task_success[i]<30) cols <- append(cols, "#ffcc00") # yellow if in [10,30)
        else if (task_success[i]>=30 & task_success[i]<=70) cols <- append(cols, "#99cc33") # green if in [30,70]
        else if (task_success[i]>70 & task_success[i]<=90) cols <- append(cols, "#ffcc00") # yellow if in (70,90]
    }
    # task durs -> df
    task_durs <- data.frame(t1,t2,t3,t4,t5,t6,t7,t8,t9,t10,t11,t12,t13,t14,t15,t16,t17)
    # filename
    pdf(file="pilot_graphs/elapsed_tasks.pdf")
    # generate and save boxplots
    bounds <- boxplot(task_durs, xlab = "Task number", ylab="Time elapsed (s)", col=cols, xaxt="n", yaxt="n", ylim=c(0,180), cex.lab=0.9)
    legend("bottomright", legend = c("[0,10)U(90,100]", "[10,30)U(70,90]", "[30,70]"), cex=0.75, border="black", title = "Success rate (%)", title.adj = 0.5, fill = c("#cc3333", "#ffcc00", "#99cc33")) 
    title(main="Pilot task difficulty (tasks 1-17)")
    axis(side=1, lwd=0.3, at=seq(1,17,1), mgp=c(3,1,0), cex.axis=0.75)
    axis(side=2, lwd=0.3, at=seq(0,180,30), las=2, mgp=c(3,1,0), cex.axis=0.75)
    abline(h=180, col="#cc3333", lty=2)
    mtext(side=4, "deadline", col="#cc3333", at=180, adj=0, line=0.1, cex=0.5, las=2)
    text(x=c(1:17), y=bounds$stats[1,]-5, paste("n = ",nrow(task_durs),sep=""), cex=0.5)
    # mtext(side=1, "Success rate (%):", at=-2.5, cex=0.6, line=-29, adj=0)
    # mtext(side=1, task_success, at=seq(1,17,1), cex=0.6, line=-29)
    # mtext(side=1, "Observations (n):", at=-2.5, cex=0.6, line=-28, adj=0)
    # mtext(side=1, nrow(task_durs), at=seq(1,17,1), cex=0.6, line=-28)
    dev.off()
}

# boxplots: elapsed time (inc. task success) by participant
pet <- function() {
    # empty data frame for participant data
    participants <- data.frame(matrix(NA,nrow=17,ncol=0))
    # store task success data
    task_success <- c()
    # fetch participant ids
    ids <- dbGetQuery(con, "SELECT DISTINCT identifier as x FROM Participants")$x
    # store boxplot cols (based on success rate)
    cols <- c()
    # loop through each participant
    for (i in ids) {
        # durs
        durs <- dbGetQuery(con, paste("SELECT time_elapsed as x FROM Tasks WHERE participant_id=",i,sep=""))$x
        participants <- cbind(participants, durs)
        # task success
        successes <- dbGetQuery(con, paste("SELECT success as x FROM Tasks WHERE participant_id=",i,sep=""))$x
        # round task success to 2 d.p.
        task_success <- append(task_success, round(sum(successes)/length(successes)*100, 2))
        # append appropriate col
        if (task_success[length(task_success)]<10 || task_success[length(task_success)]>90) cols <- append(cols, "#cc3333") # red if success % in [0,10)U(90,100]
        else if (task_success[length(task_success)]>=10 & task_success[length(task_success)]<30) cols <- append(cols, "#ffcc00") # yellow if in [10,30)
        else if (task_success[length(task_success)]>=30 & task_success[length(task_success)]<=70) cols <- append(cols, "#99cc33") # green if in [30,70]
        else if (task_success[length(task_success)]>70 & task_success[length(task_success)]<=90) cols <- append(cols, "#ffcc00") # yellow if in (70,90]
    }
    # rename df cols to participants ids
    colnames(participants) <- ids
    # filename
    pdf(file="pilot_graphs/elapsed_participants.pdf")
    # generate and save boxplots
    bounds <- boxplot(participants, xlab = "Participant ID", ylab="Time elapsed (s)", col=cols, xaxt="n", yaxt="n", ylim=c(0,180), cex.lab=0.9)
    legend("bottomright", legend = c("[0,10)U(90,100]", "[10,30)U(70,90]", "[30,70]"), cex=0.75, border="black", title = "Success rate (%)", title.adj = 0.5, fill = c("#cc3333", "#ffcc00", "#99cc33")) 
    title(main="Pilot participant success (tasks 1-17)")
    axis(side=1, lwd=0.3, at=seq(1,length(ids),1), mgp=c(3,1,0), cex.axis=0.75, labels=ids)
    axis(side=2, lwd=0.3, at=seq(0,180,30), las=2, mgp=c(3,1,0), cex.axis=0.75)
    abline(h=180, col="#cc3333", lty=2)
    mtext(side=4, "deadline", col="#cc3333", at=180, adj=0, line=0.1, cex=0.5, las=2)
    text(x=c(1:length(ids)), y=bounds$stats[1,]-5, paste(task_success,"% success",sep=""), cex=0.5)
    dev.off()
}

# boxplots: nasa-tlx for each task
smw <- function() {
    for (i in seq(1,17)) {
        # fetch data for each task
        nasa_tlx <- dbGetQuery(con, paste("SELECT hv,fv,av,os,vn,tur FROM LoadNasa WHERE task_no=",i,sep=""))
        # filename
        png(file=paste("pilot_graphs/t",i,"_nasa-tlx.png",sep=""))
        # generate and save boxplots
        boxplot(nasa_tlx, ylab="Kuormitus", col="#ccccff", xaxt="n", yaxt="n", ylim=c(0,100), cex.lab=0.9)
        title(main=paste("NASA-TLX (task #",i,")",sep=""))
        axis(side=1, lwd=0.3, labels=c("Henkinen\nvaativuus", "Fyysinen\nvaativuus", "Ajallinen\nvaativuus", "Oma\nsuoriutuminen", "Vaivannäkö", "Turhautuneisuus"), at=seq(1,6,1), mgp=c(3,1,0), cex.axis=0.7, las=1, adj=1)
        axis(side=2, lwd=0.3, at=seq(0,100,10), las=2, mgp=c(3,1,0), cex.axis=0.75)
        dev.off()
    }
}

# SQL tables -> CSV
csv <- function() {
    # table names
    tables <- c("tasks", "load", "trials", "participants")
    # fetch tables
    tasks <- dbReadTable(con,"Tasks")
    load <- dbReadTable(con,"LoadNasa")
    trials <- dbReadTable(con,"Trials")
    participants <- dbReadTable(con,"Participants")
    # write to csv
    for (i in seq(1,length(tables))) {
        write.csv(eval(parse(text=tables[i])), paste("pilot_csv/",tables[i],".csv",sep=""), row.names=FALSE)
    }
}
