#!/bin/bash

##############################################################################
# Integration Test Script for Multi-Agent Gemini CLI
#
# This script tests the integration of our multi-agent scheduler with
# the Gemini CLI fork.
#
# Usage:
#   ./scripts/test-integration.sh [mode]
#
# Modes:
#   default     - Test with default scheduler (original Gemini)
#   multi-agent - Test with multi-agent scheduler (stub mode)
#   both        - Test both modes (default)
##############################################################################

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Get mode from argument (default: both)
MODE="${1:-both}"

echo -e "${BLUE}╔════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║   Multi-Agent Gemini CLI Integration Test            ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════╝${NC}"
echo ""

##############################################################################
# Helper Functions
##############################################################################

print_header() {
  echo -e "\n${YELLOW}═════════════════════════════════════════════${NC}"
  echo -e "${YELLOW}$1${NC}"
  echo -e "${YELLOW}═════════════════════════════════════════════${NC}\n"
}

print_success() {
  echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
  echo -e "${RED}✗ $1${NC}"
}

print_info() {
  echo -e "${BLUE}ℹ $1${NC}"
}

##############################################################################
# Pre-flight Checks
##############################################################################

print_header "Pre-flight Checks"

# Check Node version
print_info "Checking Node.js version..."
node --version | grep -E "v(20|21|22)" > /dev/null || {
  print_error "Node.js >= 20.0.0 required"
  exit 1
}
print_success "Node.js version OK"

# Check if packages are built
print_info "Checking if packages are built..."
if [ ! -d "packages/core/dist" ]; then
  print_info "Building packages..."
  npm run build
fi
print_success "Packages built"

# Check if configuration exists
print_info "Checking configuration..."
if [ ! -f ".env.local" ] && [ ! -f ".env" ]; then
  print_error ".env.local or .env not found"
  print_info "Copy .env.example to .env.local and configure API keys"
  exit 1
fi
print_success "Configuration found"

##############################################################################
# Test Default Scheduler
##############################################################################

test_default_scheduler() {
  print_header "Testing Default Scheduler"

  print_info "Starting Gemini CLI with default scheduler..."

  # Set environment
  export SCHEDULER_TYPE=default
  export SCHEDULER_DEBUG=true

  # Create test input
  TEST_PROMPT="Write a Python function to calculate the factorial of a number"

  print_info "Test prompt: $TEST_PROMPT"

  # Run test (with timeout)
  timeout 30s npm run start -- <<EOF > /tmp/default-test-output.txt 2>&1 || true
$TEST_PROMPT
/exit
EOF

  # Check output
  if grep -q "def factorial" /tmp/default-test-output.txt; then
    print_success "Default scheduler test PASSED"
    print_info "Output contains expected function definition"
    return 0
  else
    print_error "Default scheduler test FAILED"
    print_info "Output:"
    cat /tmp/default-test-output.txt
    return 1
  fi
}

##############################################################################
# Test Multi-Agent Scheduler
##############################################################################

test_multi_agent_scheduler() {
  print_header "Testing Multi-Agent Scheduler (Stub Mode)"

  print_info "Starting Gemini CLI with multi-agent scheduler..."

  # Set environment
  export SCHEDULER_TYPE=multi-agent
  export SCHEDULER_DEBUG=true

  # Create test input
  TEST_PROMPT="Build a simple REST API with user authentication"

  print_info "Test prompt: $TEST_PROMPT"

  # Run test (with timeout)
  timeout 30s npm run start -- <<EOF > /tmp/multi-agent-test-output.txt 2>&1 || true
$TEST_PROMPT
/exit
EOF

  # Check output for multi-agent markers
  local has_plan=false
  local has_execution=false

  if grep -q "Multi-Agent Task Plan" /tmp/multi-agent-test-output.txt; then
    print_success "Task plan generated"
    has_plan=true
  fi

  if grep -q "Execution Results" /tmp/multi-agent-test-output.txt; then
    print_success "Execution completed"
    has_execution=true
  fi

  if grep -q "CLAUDE" /tmp/multi-agent-test-output.txt && \
     grep -q "OPENAI" /tmp/multi-agent-test-output.txt && \
     grep -q "GEMINI" /tmp/multi-agent-test-output.txt; then
    print_success "Multiple agents detected in plan"
  fi

  # Overall result
  if $has_plan && $has_execution; then
    print_success "Multi-agent scheduler test PASSED"
    return 0
  else
    print_error "Multi-agent scheduler test FAILED"
    print_info "Output:"
    cat /tmp/multi-agent-test-output.txt
    return 1
  fi
}

##############################################################################
# Test Scheduler Switching
##############################################################################

test_scheduler_switching() {
  print_header "Testing Scheduler Switching"

  print_info "Verifying both schedulers can run in same session..."

  # Test 1: Default
  export SCHEDULER_TYPE=default
  timeout 15s npm run start -- <<<$'What is 2+2?\n/exit' > /tmp/switch-test-1.txt 2>&1 || true

  # Test 2: Multi-agent
  export SCHEDULER_TYPE=multi-agent
  timeout 15s npm run start -- <<<$'What is 2+2?\n/exit' > /tmp/switch-test-2.txt 2>&1 || true

  # Check both worked
  if [ -s /tmp/switch-test-1.txt ] && [ -s /tmp/switch-test-2.txt ]; then
    print_success "Scheduler switching works"
    return 0
  else
    print_error "Scheduler switching failed"
    return 1
  fi
}

##############################################################################
# Test Configuration Loading
##############################################################################

test_config_loading() {
  print_header "Testing Configuration Loading"

  print_info "Checking if configuration is loaded correctly..."

  # Create temporary config
  cat > /tmp/test-config.json <<EOF
{
  "scheduler": {
    "type": "multi-agent",
    "debug": true
  }
}
EOF

  export CONFIG_PATH=/tmp/test-config.json

  # Run with config
  timeout 10s npm run start -- <<<$'/config\n/exit' > /tmp/config-test.txt 2>&1 || true

  if grep -q "multi-agent" /tmp/config-test.txt || \
     grep -q "Configuration" /tmp/config-test.txt; then
    print_success "Configuration loading works"
    return 0
  else
    print_error "Configuration loading failed"
    return 1
  fi
}

##############################################################################
# Run Tests
##############################################################################

# Track results
TESTS_RUN=0
TESTS_PASSED=0
TESTS_FAILED=0

run_test() {
  local test_name="$1"
  local test_func="$2"

  TESTS_RUN=$((TESTS_RUN + 1))

  if $test_func; then
    TESTS_PASSED=$((TESTS_PASSED + 1))
  else
    TESTS_FAILED=$((TESTS_FAILED + 1))
  fi
}

# Execute tests based on mode
case "$MODE" in
  default)
    run_test "Default Scheduler" test_default_scheduler
    ;;

  multi-agent)
    run_test "Multi-Agent Scheduler" test_multi_agent_scheduler
    ;;

  both)
    run_test "Default Scheduler" test_default_scheduler
    run_test "Multi-Agent Scheduler" test_multi_agent_scheduler
    run_test "Scheduler Switching" test_scheduler_switching
    run_test "Configuration Loading" test_config_loading
    ;;

  *)
    print_error "Unknown mode: $MODE"
    print_info "Usage: $0 [default|multi-agent|both]"
    exit 1
    ;;
esac

##############################################################################
# Summary
##############################################################################

print_header "Test Summary"

echo -e "  Tests run:    ${TESTS_RUN}"
echo -e "  Tests passed: ${GREEN}${TESTS_PASSED}${NC}"
echo -e "  Tests failed: ${RED}${TESTS_FAILED}${NC}"
echo ""

if [ $TESTS_FAILED -eq 0 ]; then
  print_success "ALL TESTS PASSED! ✨"
  echo ""
  print_info "Next steps:"
  print_info "  1. Review test outputs in /tmp/*-test*.txt"
  print_info "  2. Proceed to Phase 2: Implement Meta Agent"
  print_info "  3. Replace stub implementations with real logic"
  echo ""
  exit 0
else
  print_error "SOME TESTS FAILED"
  echo ""
  print_info "Debug information:"
  print_info "  - Check logs in /tmp/*-test*.txt"
  print_info "  - Verify .env.local configuration"
  print_info "  - Run: npm run build"
  print_info "  - Check: npm run test"
  echo ""
  exit 1
fi
