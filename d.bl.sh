
REPO=`pwd`

gblcmd_install(){
    sudo -H pip install -r requirements.txt
    sudo ln -sf $REPO/src/bin/gen_reqs.py /bin/frtac_gen_reqs
    sudo ln -sf $REPO/src/bin/frtac.py /bin/frtac
}