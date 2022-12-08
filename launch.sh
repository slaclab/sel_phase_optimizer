export TMUX_SSH_USER=laci
export TMUX_SSH_SERVER=lcls-srv03

source use_pydm.sh
cd /home/physics/srf/gitRepos/sel_phase_opt && python sel_phase_optimizer.py