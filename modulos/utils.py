import os
import json
import time

attempts_state_path = "data/state_attempts.json"

def load_attempts_state():
    if os.path.exists(attempts_state_path):
        with open(attempts_state_path, "r") as f:
            return json.load(f)
    return {}

def save_attempts_state(state):
    with open(attempts_state_path, "w") as f:
        json.dump(state, f)

def check_attempts(file):
    state = load_attempts_state()
    if file in state:
        attempts, last_attempt = state[file]
        if attempts >= 3 and time.time() - last_attempt < 86400:
            return False, 86400 - (time.time() - last_attempt)
    return True, 0

def register_failed_attempt(file):
    state = load_attempts_state()
    if file in state:
        state[file][0] += 1
        state[file][1] = time.time()
    else:
        state[file] = [1, time.time()]
    save_attempts_state(state)

def reset_attempts(file):
    state = load_attempts_state()
    if file in state:
        del state[file]
    save_attempts_state(state)