library(DBI)  # reference: https://db.rstudio.com/databases/sqlite/
library(tidyverse)

# connect to pilot.db
con <- dbConnect(RSQLite::SQLite(), "../pilot.db")

# boxplots: elapsed time (inc. task success) by task
tet <- function() {
    # create dir if not exist
    dir.create("pilot_graphs", showWarnings=FALSE)
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
    bounds <- boxplot(task_durs, xlab = "Task number", ylab="Time elapsed (s)", col=cols, outbg=cols, outpch=21, xaxt="n", yaxt="n", ylim=c(0,180), cex.lab=0.9)
    legend("bottomright", legend = c("[0,10)U(90,100]", "[10,30)U(70,90]", "[30,70]"), cex=0.75, border="black", title = "Success rate (%)", title.adj = 0.5, fill = c("#cc3333", "#ffcc00", "#99cc33")) 
    title(main="Pilot task completion (tasks 1-17)")
    axis(side=1, lwd=0.3, at=seq(1,17,1), mgp=c(3,1,0), cex.axis=0.75)
    axis(side=2, lwd=0.3, at=seq(0,180,30), las=2, mgp=c(3,1,0), cex.axis=0.75)
    abline(h=180, col="#cc3333", lty=2)
    mtext(side=4, "deadline", col="#cc3333", at=180, adj=0, line=0.1, cex=0.5, las=2)
    text(x=c(1:17), y=bounds$stats[1,]-5, paste("n = ",nrow(task_durs),sep=""), cex=0.5)
    dev.off()
}

# boxplots: elapsed time (inc. task success) by participant
pet <- function() {
    # create dir if not exist
    dir.create("pilot_graphs", showWarnings=FALSE)
    # empty data frame for participant data
    participants <- data.frame(matrix(NA,nrow=17,ncol=0))
    # store task success data
    task_success <- c()
    # fetch participant ids
    ids <- dbGetQuery(con, "SELECT DISTINCT identifier as x FROM Participants")$x
    # fetch participant background data
    age <- dbGetQuery(con, "SELECT age as x FROM Participants")$x
    ed <- dbGetQuery(con, "SELECT ed as x FROM Participants")$x
    exp <- dbGetQuery(con, "SELECT exp as x FROM Participants")$x
    # replace db abbreviations with full labels
    ed_map <- c("perusaste"="perusaste", "keskiaste"="keskiaste", "alempi"="alempi kk", "ylempi"="ylempi kk")
    for (i in seq(1,length(ed))) {
        ed[i] <- ed_map[ed[i]]
    }
    # store boxplot cols (based on success rate)
    cols <- c()
    # loop through each participant
    for (i in ids) {
        # task success
        successes <- dbGetQuery(con, paste("SELECT success as x FROM Tasks WHERE participant_id=",i,sep=""))$x
        # round task success percentage to 2 d.p.
        task_success <- append(task_success, round(sum(successes)/length(successes)*100, 2))
        # durs
        durs <- dbGetQuery(con, paste("SELECT time_elapsed as x FROM Tasks WHERE participant_id=",i,sep=""))$x
        # bind to df
        participants <- cbind(participants, durs)
        # append appropriate colour
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
    bounds <- boxplot(participants, xlab = "Participant ID", ylab="Time elapsed (s)", col=cols, outbg=cols, outpch=21, xaxt="n", yaxt="n", ylim=c(0,180), cex.lab=0.9)
    legend("bottomright", legend = c("[0,10)U(90,100]", "[10,30)U(70,90]", "[30,70]"), cex=0.75, border="black", title = "Success rate (%)", title.adj = 0.5, fill = c("#cc3333", "#ffcc00", "#99cc33"))
    title(main="Pilot participant success (tasks 1-17)")
    axis(side=1, lwd=0.3, at=seq(1,length(ids),1), mgp=c(3,1,0), cex.axis=0.75, labels=ids)
    axis(side=2, lwd=0.3, at=seq(0,180,30), las=2, mgp=c(3,1,0), cex.axis=0.75)
    abline(h=180, col="#cc3333", lty=2)
    mtext(side=4, "deadline", col="#cc3333", at=180, adj=0, line=0.1, cex=0.5, las=2)
    text(x=c(1:length(ids)), y=bounds$stats[1,]-5, paste(task_success,"% success",sep=""), cex=0.5)
    text(x=c(1:length(ids)), y=bounds$stats[1,]-10, paste(exp," (",age,"v)",sep=""), cex=0.5)
    text(x=c(1:length(ids)), y=bounds$stats[1,]-15, ed, cex=0.5)
    dev.off()
}

# boxplots: nasa-tlx for each task
tlx <- function() {
    # create dir if not exist
    dir.create("pilot_graphs", showWarnings=FALSE)
    # nasa-tlx for each task
    for (i in seq(1,17)) {
        # fetch data for each task
        nasa_tlx <- dbGetQuery(con, paste("SELECT hv,fv,av,os,vn,tur FROM LoadNasa WHERE task_no=",i,sep=""))
        # filename
        pdf(file=paste("pilot_graphs/t",i,"_nasa-tlx.pdf",sep=""))
        # generate and save boxplots
        boxplot(nasa_tlx, ylab="Kuormitus", col="#ccccff", xaxt="n", yaxt="n", ylim=c(0,100), cex.lab=0.9)
        title(main=paste("NASA-TLX (task #",i,")",sep=""))
        ### huom! alla todo
        mtext(side=1, paste("n = ",nrow(nasa_tlx),sep=""), col="#cc3333", at=0, adj=0, line=0, cex=0.5, las=1)
        ###
        axis(side=1, lwd=0.3, labels=c("Henkinen\nvaativuus", "Fyysinen\nvaativuus", "Ajallinen\nvaativuus", "Oma\nsuoriutuminen", "Vaivannäkö", "Turhautuneisuus"), at=seq(1,6,1), mgp=c(3,1,0), cex.axis=0.7, las=1, adj=1)
        axis(side=2, lwd=0.3, at=seq(0,100,10), las=2, mgp=c(3,1,0), cex.axis=0.75)
        dev.off()
    }
    # nasa-tlx summary of all tasks
    # to do: histograms for each dim
    # to do: boxplot summary for all tasks
}

# SQL tables -> CSV
csv <- function() {
    # create dir if not exist
    dir.create("pilot_csv", showWarnings=FALSE)
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

# PCA: task similarity (based on task instructions and optimal path)
pca_op <- function() {
    # create dir if not exist
    dir.create("pilot_graphs", showWarnings=FALSE)
    data <- read.csv("optimal_path.csv", sep=";")
    data <- t(data)  # transpose df (cols represent features and rows tasks)
    colnames(data) <- c("min clicks", "min keys", "task depth", "words", "info")
    results <- prcomp(data, scale=TRUE)  # scale=TRUE to standardise columns
    # reverse signs
    results$rotation <- (-1)*results$rotation
    results$x <- (-1)*results$x
    # filename
    pdf(file="pilot_graphs/pca_tasks.pdf")
    biplot(results, scale=0, cex=0.6, col=c("purple","red"), main="PCA: Task similarity (task instructions and optimal path)")  # scale=0 to ensure arrows represent loadings
    dev.off()
}

# PCA: participant performance (based on time elapsed for tasks 1-17)
pca_perf <- function() {
    # create dir if not exist
    dir.create("pilot_graphs", showWarnings=FALSE)
    # empty data frame for participant data
    participant_durs <- data.frame(matrix(NA,nrow=17,ncol=0))
    # get number of participants
    n <- dbGetQuery(con, "SELECT COUNT(*) as x FROM Participants")$x
    # fetch participant ids
    ids <- dbGetQuery(con, "SELECT DISTINCT identifier as x FROM Participants")$x
    # fetch task durs for each participant
    for (i in ids) {
        durs <- dbGetQuery(con, paste("SELECT time_elapsed as x FROM Tasks WHERE participant_id=",i," ORDER BY task_no",sep=""))$x
        successes <- dbGetQuery(con, paste("SELECT success as x FROM Tasks WHERE participant_id=",i," ORDER BY task_no",sep=""))$x
        # failed tasks duration 03:00 (for instances where participant has given up early)
        for (j in seq(1,length(successes))) {
            if (successes[j]==0) durs[j] <- 180
        }
        participant_durs <- cbind(participant_durs, durs)
    }
    # rename df cols to ids
    colnames(participant_durs) <- ids
    rownames(participant_durs) <- paste("t", seq(1,17), sep="")
    # pca
    data <- t(participant_durs)
    results <- prcomp(data, scale=FALSE)  # scale=FALSE as no need to standardise
    # reverse signs
    results$rotation <- (-1)*results$rotation
    results$x <- (-1)*results$x
    # filename
    pdf(file="pilot_graphs/pca_participants.pdf")
    biplot(results, scale=0, cex=0.6, col=c("purple","red"), main="PCA: Participant performance (time elapsed for tasks 1-17)")  # scale=0 to ensure arrows represent loadings
    dev.off()
}

# plotting variance explained by pc's
# var_explained = results$sdev^2 / sum(results$sdev^2)
# plot(x=c(1:length(no of pc's)), y=var_explained, type="b")