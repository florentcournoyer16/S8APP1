#! /bin/tcsh
########################################################################
## Author  :    Marc-André Tétrault
## Project :    Verification Primer
##
## Université de Sherbrooke
################################################################################
#
# Purpose   :   Verification environment setup
#               - Variables
#               - Aliases
#               - Software environment/version selection
################################################################################

# set environment working copy root
setenv PROJECT_ROOT                 $PWD

if ( -f "/opt/pycharm-2021.1.3/bin/pycharm.sh" ) then
    # use lab workstation local installation
    alias pycharm /opt/pycharm-2021.1.3/bin/pycharm.sh
else
    echo "default pycharm not found for lab setup, please ensure the shell"
    echo "with the which command or specify your own alias"
endif

# load cocotb, from virtual environment (
if ( -f "$PROJECT_ROOT/cocotb-env/bin/activate.csh" ) then
    source $PROJECT_ROOT/cocotb-env/bin/activate.csh
else
    echo "Please generate the python3 cocotb environment, for example using Pycharm"
    echo "For the moment, this is not included in the installation image."
endif

################################################################
# Load Cadence tools
################################################################
# Xcellium, very recent Cadence simulator package
#setenv SIM    xcelium
#source $CMC_HOME/scripts/cadence.xceliummain21.09.003.csh
#source $CMC_HOME/scripts/cadence.vmanagermain21.09.002.csh
##In order to enable coverage analysis, please set the environment variable MDV_XLM_HOME to point to the XCELIUM$
#setenv MDV_XLM_HOME $CMC_CDS_XCELIUM_HOME
## for vmanager administration/server mode setup tools
#setenv PATH $CMC_CDS_VMANAGERMAIN_HOME/vmgr/admin:$PATH

# Incisive setting, older but compatible simulator package
setenv SIM    ius
source $CMC_HOME/scripts/cadence.incisive15.20.079.csh

# analog simulator
source $CMC_HOME/scripts/cadence.spectre19.10.162.csh

# Licence patch. Replace with your local licence server name
#echo 'lmserver-24 cadconnect.3it.usherbrooke.ca' >> ~/.hosts_local
setenv  HOSTALIASES PROJECT_ROOT/.hosts_local

# Override multiple licence servers - creates delays
setenv CDS_LIC_FILE 6055@cadence.gegi.usherbrooke.ca:7055@cadence.gegi.usherbrooke.ca
################################################################


################################################################
# Verification environment local setup
################################################################


setenv DESIGN_ROOT	                $PROJECT_ROOT/design
setenv VERIF_ROOT	                  $PROJECT_ROOT/verif
setenv DUT_INST_NAME                OscilloTop
setenv MODELS_HLM_ROOT	            $DESIGN_ROOT/models
setenv MODELS_MLM_ROOT	            $DESIGN_ROOT/models/mlm

setenv VMANAGER_CONFIG_HOME         $VERIF_ROOT/vmanager
setenv VMANAGER_REGRESSIONS_AREA    $VERIF_ROOT/regression_area
setenv PYTHONPATH                   $VERIF_ROOT/tests:$VERIF_ROOT/core

# Simulation command
alias srun $VERIF_ROOT/scripts/runsim.py

# Vmanager in standalone mode
# with GUI
alias vmanager \vmanager -cs -64 -gui -local $VERIF_ROOT/vmgr_db
alias vplanner \vplanner -standalone $VERIF_ROOT/vmgr_db

# command line mode, for operation on headless cluster
#alias cmanager \vmanager -cs -64 -batch -local $VERIF_ROOT/vmgr_db

# Vmanager in server mode
#alias smanager \vmanager -cs -64 -gui -server servername.cmc.ca:8080




