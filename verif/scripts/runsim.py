#!/usr/bin/env python3

## Standard Packages
from sys import argv, exit, stdout, stderr
import argparse
import os
from os.path import isfile, join
import textwrap
import subprocess
#from pathlib import Path


parser = argparse.ArgumentParser(description='Verification environment for cocotb and VManager.')

# texte
parser.add_argument('-t', '--test', type=str, default="do_wait_only", help='String. Test name. See $VERIF_ROOT/tests for list.')
parser.add_argument('-d', '--testdir', type=str, default="tests", help='String. Specify test subdirectory, defaults to $VERIF_ROOT/tests.')

# int
parser.add_argument('--seed', type=str, help='String. Random seed. Accepts "random" or integer. Defaults to "random" if empty')

# bool
parser.add_argument('-w', '--waves', dest='waves', help="Bool Switch. Save waveforms to disk, default is false.", action='store_true') #action="store_true"
parser.set_defaults(waves=None)

parser.add_argument('-b', '--batch', help="Bool Switch. Batch mode, no gui", action="store_true")
parser.add_argument('--sva', help="Bool Switch. Include SystemVerilog Assertions bindings.", action="store_true")
parser.add_argument('-c', '--cov', help="Bool Switch. Enable functional coverage collection.", action="store_true")
parser.add_argument('--cocotb-sanity-check', dest='cocotbsanity', help="Bool Switch. Run cocotb sanity check.", action="store_true")


# parser.add_argument('integers', metavar='N', type=int, nargs='+',
#                     help='an integer for the accumulator')

args = parser.parse_args()
print(args.waves)


PROJECT_ROOT = os.environ.get('PROJECT_ROOT')
PWD = os.environ.get('PWD')
SIM = os.environ.get('SIM')
HOME = os.environ.get('HOME')
VERIF_ROOT = os.environ.get('VERIF_ROOT')
DESIGN_ROOT = os.environ.get('DESIGN_ROOT')
MODELS_HLM_ROOT = os.environ.get('MODELS_HLM_ROOT')
DUT_INST_NAME = os.environ.get('DUT_INST_NAME')

VMANAGER_REGRESSIONS_AREA = os.environ.get('VMANAGER_REGRESSIONS_AREA')


if (PROJECT_ROOT == None):
    print("No SVE environment found.")
    exit(1)

if(PWD == PROJECT_ROOT):
    print("Running sims from working copy root is possible but not ")
    print("recommended. moving de default simulation directory")
    print("Currently in " + os.getcwd())
    os.chdir(PROJECT_ROOT + "/simdir")
    print("Now in " + os.getcwd())

if(PWD == HOME):
    print("Running sims from the user's home directory is possible")
    print("but not recommended. Please run from other directory")
    exit(1)


if(PWD != (PROJECT_ROOT + "/simdir")) and (VMANAGER_REGRESSIONS_AREA not in PWD):
    print("For development, coherce simulation directory")
    print("Please use   " + PROJECT_ROOT + "/simdir")
    print("or disable checker in script.")
    print("Currently in " + os.getcwd())
    os.chdir(PROJECT_ROOT + "/simdir")
    print("Now in " + os.getcwd())

    #exit(1)



##### Ensure test file exists
###TestPath = join(VERIF_ROOT, args.testdir, args.test + ".sv")
###if not isfile(TestPath):
###    print("Cannot find test")
###    exit(1)
###
###command = ["ln", "-s", "-f", TestPath, join(PWD, "current_test.sv")]
###try:
###    response = subprocess.check_output(command, timeout=10)
###except:
###    ## timeout
###    print("Error on test simlink creation.")
###    exit(1)


# Set default manifest files
DesignFiles="-f " + DESIGN_ROOT + "/digital/digital_design_manifest.f"
Models= "" #"-f " + MODELS_HLM_ROOT + "/mixed_sig_modules_hlm.f"
TestbenchFiles= "" #"-f " + VERIF_ROOT + "/core/tb_corefiles.f"

# simvision command for waveforms.
# 		default saves all signals in design
WavesScript=VERIF_ROOT + "/scripts/waves.tcl"

# Coverage switches
CoverageCommands =  " -coverage all" # code and functional coverage. ICC user guide. Also activates cover properties, so no need for -abvcoveron
CoverageCommands += " -covfile " + VERIF_ROOT + "/scripts/coverage.tcl"
CoverageCommands += " -covdut " + DUT_INST_NAME 	## will not capture coverage from the testbench...
CoverageCommands += " -covoverwrite"
CoverageCommands += " -covtest " + args.test

# Main xrun switches
# 		VHDL '93 support, -v200x also possible
MainOptions  = "-v93"
MainOptions += " -rnm_package" ## real number modeling for SystemVerilog

#set MainOptions="$MainOptions "
MainOptions += " -nowarn COVFHT"
MainOptions += " -nowarn COVCGN"
MainOptions += " -nowarn COVUTA"
MainOptions += " -nowarn ICFCLD"
MainOptions += " -nowarn WSEM2009"

if SIM == "xcellium":
    MainOptions += " -no_analogsolver"


# print out the random seed in the log file to help rerun in case of error
MainOptions= MainOptions + " -input " + VERIF_ROOT + "/scripts/misc_commands.tcl"

# optional arguments
if(args.batch == False):
    MainOptions += " -gui"
    if(args.waves == None):
        print("Gui mode without waveform specification, turn waves on")
        args.waves = True


if(args.batch == True):
    MainOptions += " -run -exit"
    if(args.waves == None):
        print("batch mode without waveform specification, turn waves off")
        args.waves = False

if(args.waves == True):
    # access and +rwc switches taken core of by cocotb
    MainOptions += " -input " + WavesScript

AssertionFiles = ""
if(args.sva == True):
    AssertionFiles += "-f " + VERIF_ROOT + "/tb_sva_bindings.f"

if(args.cov == True):
    MainOptions += CoverageCommands

## Default: do nothing. Note: can also use -svseed, seems to change something for reporting in log...
if(args.seed == None):
    MainOptions += " -seed random"
else:
    MainOptions += (" -seed " + args.seed)


# Method 1 : directly do command line stuff
#CocotbLib = subprocess.run(['cocotb-config', '--lib-name-path', 'vpi', 'xcelium'], stdout=subprocess.PIPE).stdout.decode('utf-8').strip()
#MainOptions += " -define COCOTB_SIM=1"
#MainOptions += " -ACCESS +rwc" +
#MainOptions += " -top top"
#MainOptions += " -loadvpi " + CocotbLib + ":vlog_startup_routines_bootstrap -plinowarn "
#os.environ.setdefault('MODULE', 'register_handshake')
#os.environ.setdefault('TOPLEVEL', 'top')
#os.environ.setdefault('TESTCASE', 'test_basic_uart')
# directly show stdout/stderr in console
#command = ["irun", MainOptions, Models, DesignFiles, TestbenchFiles, AssertionFiles]
#print(command)
#subprocess.run(command)
#exit(0)


# Method 2 Use cocotb_test with force to true
# seems to print stdout to stderr

from cocotb_test.simulator import run
import os

def test_dff():
    run(
        verilog_sources=[os.path.join(VERIF_ROOT, "core", "cocotb_sanitycheck", "dff.sv")],
        force_compile = True,
        sim_args=[MainOptions],
        python_search=[os.path.join(VERIF_ROOT, "core", "cocotb_sanitycheck")],
        toplevel="dff_test",            # top level HDL
        testcase="test_dff_simple",
        module="dff_cocotb"        # name of cocotb test module
    )

def test_start():
    print(DesignFiles)
    run(
        verilog_sources=[],
        force_compile = True, # fixes leaving verilog_sources empty
        compile_args=[DesignFiles],
        sim_args=[MainOptions],
        python_search=[os.path.join(VERIF_ROOT, "tests")],
        toplevel="top",            # top level HDL
        testcase="test_" + args.test,
        module=args.test        # name of cocotb test module
    )

if args.cocotbsanity == True:
    test_dff()
else:
    test_start()
