gblcmd_robot(){
    robot --loglevel TRACE --log ./logging.html --report myreport.html --output myoutput.xml $@ .
}