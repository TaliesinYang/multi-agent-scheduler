#!/bin/bash
timeout 90 claude -p "Execute this SQL query on agentbench_cli.db: SELECT user_id FROM users WHERE email = 'alice@example.com'. Return the user_id. When done, say 'FINAL_ANSWER: ' followed by the user_id." --tools Bash --permission-mode bypassPermissions 2>&1
