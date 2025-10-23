#!/usr/bin/env bash
# main.sh - Multi-process spawner for BruteBuddy (revised)
# WSL & Linux Compatible - No root required!
#
# Usage:
#   ./main.sh <target-url> <user-or-users-file> <pass-file> <processes> [concurrency] [global-flag-path] [--no-auto-kill]
#
# Example:
#   Single user:  ./main.sh "http://127.0.0.1/api/login" admin pass.txt 4 8
#   Multi user:   ./main.sh "http://127.0.0.1/api/login" users.txt pass.txt 4 8
#
# Notes:
#  - This script prefers async_bruteforce_autokill.py if present, otherwise falls back to main.py
#  - Use final arg `--no-auto-kill` to disable pkill behavior (passed to worker via --no-auto-kill)

set -euo pipefail
IFS=$'\n\t'

TARGET="${1:-}"
USER_OR_FILE="${2:-}"
PASS_FILE="${3:-}"
PROCESSES="${4:-4}"
CONC="${5:-6}"
GLOBAL_FLAG="${6:-/tmp/brutebuddy_done.flag}"
NO_AUTO_KILL_FLAG="${7:-}"   # pass --no-auto-kill as seventh arg to disable auto-kill in workers

# Colors
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; CYAN='\033[0;36m'; NC='\033[0m'

usage() {
  echo -e "${RED}Usage:${NC} $0 <target-url> <user-or-users-file> <pass-file> <processes> [concurrency] [global-flag-path] [--no-auto-kill]"
  exit 1
}

banner() {
  echo -e "${GREEN}"
  echo "╔═══════════════════════════════════════════════════════╗"
  echo "║               🔥 Aduh Jangan Dek 🔥                   ║"
  echo "║          Fast • Smart • Efficient • Parallel          ║"
  echo "╚═══════════════════════════════════════════════════════╝"
  echo -e "${NC}"
}

# basic validation
if [ -z "$TARGET" ] || [ -z "$USER_OR_FILE" ] || [ -z "$PASS_FILE" ]; then
  banner; usage
fi

if [ ! -f "$PASS_FILE" ]; then
  echo -e "${RED}[ERROR]${NC} Password file not found: $PASS_FILE"; usage
fi

# choose worker script: prefer async_bruteforce_autokill.py, fallback main.py
WORKER_SCRIPT=""
if [ -f "./async_bruteforce_autokill.py" ]; then
  WORKER_SCRIPT="./async_bruteforce_autokill.py"
elif [ -f "./main.py" ]; then
  WORKER_SCRIPT="./main.py"
else
  echo -e "${RED}[ERROR]${NC} No worker script found (async_bruteforce_autokill.py or main.py) in current dir."
  exit 1
fi

# positive integer check
is_pos_int() { [[ "$1" =~ ^[0-9]+$ ]] && [ "$1" -ge 1 ]; }

if ! is_pos_int "$PROCESSES"; then echo -e "${RED}[ERROR]${NC} Invalid processes value: $PROCESSES"; usage; fi
if ! is_pos_int "$CONC"; then echo -e "${RED}[ERROR]${NC} Invalid concurrency value: $CONC"; usage; fi

# detect mode (single vs cartesian)
MODE="single"
if [ -f "$USER_OR_FILE" ]; then
  MODE="cartesian"
  USERS_FLAG="--users-file \"$USER_OR_FILE\""
  USER_COUNT=$(wc -l < "$USER_OR_FILE" | tr -d ' ')
else
  MODE="single"
  USERS_FLAG="--user \"$USER_OR_FILE\""
  USER_COUNT=1
fi

PASS_COUNT=$(wc -l < "$PASS_FILE" | tr -d ' ')
TOTAL_REQUESTS=$((USER_COUNT * PASS_COUNT))

# clear old flag
rm -f "$GLOBAL_FLAG" 2>/dev/null || true

banner
echo -e "${CYAN}[INFO]${NC} Worker script: ${YELLOW}$WORKER_SCRIPT${NC}"
echo -e "  Target:      ${YELLOW}$TARGET${NC}"
echo -e "  Mode:        ${YELLOW}$MODE${NC}"
echo -e "  Users:       ${YELLOW}$USER_COUNT${NC}"
echo -e "  Passwords:   ${YELLOW}$PASS_COUNT${NC}"
echo -e "  Total Reqs:  ${YELLOW}$TOTAL_REQUESTS${NC}"
echo -e "  Processes:   ${YELLOW}$PROCESSES${NC}"
echo -e "  Concurrency: ${YELLOW}$CONC${NC} per process"
echo -e "  Stop Flag:   ${YELLOW}$GLOBAL_FLAG${NC}"
echo ""

# detect tmux
USE_TMUX=false
if command -v tmux >/dev/null 2>&1; then
  USE_TMUX=true
  echo -e "${GREEN}[✓]${NC} tmux detected - will spawn panes"
else
  echo -e "${YELLOW}[!]${NC} tmux not found - falling back to background processes"
fi

# trap so we can cleanup background processes/pidfile on ctrl-c or exit
PID_FILE="/tmp/brutebuddy_pids_$(date +%s).txt"
pids_to_kill=()

cleanup() {
  echo -e "\n${YELLOW}[CLEANUP]${NC} stopping spawned processes..."
  if [ -f "$PID_FILE" ]; then
    while read -r pid; do
      if ps -p "$pid" > /dev/null 2>&1; then
        kill "$pid" 2>/dev/null || true
      fi
    done < "$PID_FILE"
    rm -f "$PID_FILE"
  fi
  exit 0
}
trap cleanup INT TERM EXIT

# helper to build command (safe quoting)
build_cmd() {
  local shard_idx="$1"
  local extra_auto_kill="$2"
  # pass no-auto-kill to worker script if requested
  local no_kill_arg=""
  if [ "$extra_auto_kill" = "no" ]; then
    no_kill_arg="--no-auto-kill"
  fi
  printf 'python3 %s -t "%s" %s -P "%s" --shards %s --shard-index %s --concurrency %s --mode %s --engine async --global-stop-flag "%s" %s' \
    "$WORKER_SCRIPT" "$TARGET" "$USERS_FLAG" "$PASS_FILE" "$PROCESSES" "$shard_idx" "$CONC" "$MODE" "$GLOBAL_FLAG" "$no_kill_arg"
}

# run in tmux
run_with_tmux() {
  SESSION="brutebuddy_$(date +%s)"
  tmux new-session -d -s "$SESSION" -n "shard_0"
  if [ "$PROCESSES" -gt 1 ]; then
    for _ in $(seq 2 "$PROCESSES"); do
      tmux split-window -t "$SESSION:0" -d
    done
    tmux select-layout -t "$SESSION:0" tiled
  fi

  echo -n > "$PID_FILE"

  for i in $(seq 0 $((PROCESSES-1))); do
    CMD=$(build_cmd "$i" "${NO_AUTO_KILL_FLAG:-yes}")
   # --- PERBAIKAN DI SINI ---
   # Guna `tmux send-keys` tanpa `-l` untuk menghantar arahan,
   # dan pastikan C-m (Enter) dihantar dengan betul di hujungnya.
   tmux send-keys -t "$SESSION:0.$i" "$CMD" Enter
  # ATAU cara alternatif yang lebih eksplisit:
  # tmux send-keys -t "$SESSION:0.$i" "$CMD"
 # tmux send-keys -t "$SESSION:0.$i" C-m

    echo -e "${GREEN}[✓]${NC} Spawned shard ${YELLOW}$i${NC} in pane ${YELLOW}$SESSION:0.$i${NC}"
  done 
  echo ""
  echo -e "${CYAN}[ATTACH]${NC} tmux attach -t $SESSION"
  echo -e "${CYAN}[KILL]${NC} tmux kill-session -t $SESSION"
  echo ""
}
# run as background processes (no tmux)
run_with_bg_processes() {
  echo -n > "$PID_FILE"
  for i in $(seq 0 $((PROCESSES-1))); do
    CMD=$(build_cmd "$i" "${NO_AUTO_KILL_FLAG:-yes}")
    LOG_FILE="brutebuddy_shard_${i}.log"
    # shellcheck disable=SC2126
    bash -c "$CMD" > "$LOG_FILE" 2>&1 &
    pid=$!
    echo "$pid" >> "$PID_FILE"
    pids_to_kill+=("$pid")
    echo -e "${GREEN}[✓]${NC} Process ${YELLOW}$i${NC} started (PID: ${YELLOW}$pid${NC}, Log: ${YELLOW}$LOG_FILE${NC})"
    sleep 0.15
  done

  cat > brutebuddy_control.sh <<'EOF'
#!/usr/bin/env bash
PID_FILE='"$PID_FILE"'
case "$1" in
  stop) kill $(cat "$PID_FILE") 2>/dev/null || true ;;
  status) for pid in $(cat "$PID_FILE"); do if ps -p $pid > /dev/null; then echo "PID $pid RUNNING"; else echo "PID $pid STOPPED"; fi; done ;;
  logs) tail -f brutebuddy_shard_*.log ;;
  results) if [ -f found_responses/results.csv ]; then cat found_responses/results.csv; else echo "No results yet"; fi ;;
  *) echo "Usage: $0 {stop|status|logs|results}" ; exit 1 ;;
esac
EOF
  chmod +x brutebuddy_control.sh
  echo -e "${GREEN}[HELPER]${NC} created: ./brutebuddy_control.sh"
}

# Main: choose runner
if [ "$USE_TMUX" = true ]; then
  run_with_tmux
else
  run_with_bg_processes
fi

echo ""
echo -e "${GREEN}[DONE]${NC} Started $PROCESSES workers. Use control script or tmux to monitor."
echo ""
# keep script running so trap can handle ctrl-c while background processes run
# if tmux used, user will attach to tmux; if background used we exit (but trap persists)
if [ "$USE_TMUX" = true ]; then
  # don't exit immediately; allow user to attach
  sleep 1
fi
