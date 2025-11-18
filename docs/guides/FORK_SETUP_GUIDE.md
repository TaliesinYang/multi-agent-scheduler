# Fork Setup Guide: Multi-Agent Gemini CLI

**Goal**: Fork Gemini CLI and set up the foundation for multi-agent integration

---

## Prerequisites

- Node.js >= 20.0.0
- npm >= 10.0.0
- Git
- GitHub account
- API Keys: `ANTHROPIC_API_KEY`, `OPENAI_API_KEY`, `GOOGLE_API_KEY`

---

## Step 1: Fork and Clone

### 1.1 Fork on GitHub

1. Go to https://github.com/google-gemini/gemini-cli
2. Click "Fork" button (top right)
3. Choose your organization/account
4. Wait for fork to complete

### 1.2 Clone Your Fork

```bash
# Clone your fork
git clone https://github.com/YOUR_USERNAME/gemini-cli.git
cd gemini-cli

# Add upstream remote (Google's official repo)
git remote add upstream https://github.com/google-gemini/gemini-cli.git

# Verify remotes
git remote -v
# Should show:
# origin    https://github.com/YOUR_USERNAME/gemini-cli.git (fetch)
# origin    https://github.com/YOUR_USERNAME/gemini-cli.git (push)
# upstream  https://github.com/google-gemini/gemini-cli.git (fetch)
# upstream  https://github.com/google-gemini/gemini-cli.git (push)
```

### 1.3 Create Feature Branch

```bash
# Create branch for multi-agent integration
git checkout -b multi-agent-integration

# This is our working branch
# main branch stays clean for merging upstream updates
```

---

## Step 2: Install Dependencies

```bash
# Install dependencies
npm install

# Build packages
npm run build

# Verify build works
npm run test
```

**Expected Output**:
```
✓ All tests passing
✓ Build successful
```

---

## Step 3: Verify Original Gemini CLI Works

```bash
# Try running the original Gemini CLI
npm run start

# Or if you have it globally:
# npm install -g .
# gemini
```

**Test Prompt**:
```
> Hello, can you write a Python hello world function?

# Should get response from Gemini
```

**Exit**: Ctrl+C

---

## Step 4: Create Project Structure for Our Code

```bash
# Create directories for our multi-agent code
mkdir -p packages/core/src/schedulers
mkdir -p packages/multi-agent-core/src
mkdir -p packages/multi-agent-core/src/agents
mkdir -p packages/multi-agent-core/tests
```

**New structure**:
```
gemini-cli/
├── packages/
│   ├── core/
│   │   └── src/
│   │       └── schedulers/          # 🆕 Scheduler interface layer
│   │           ├── port.ts
│   │           ├── default-scheduler.ts
│   │           └── multi-agent-scheduler.ts
│   │
│   └── multi-agent-core/            # 🆕 Our independent package
│       ├── package.json
│       ├── tsconfig.json
│       └── src/
│           ├── meta-agent.ts
│           ├── scheduler.ts
│           └── agents/
│               ├── claude-agent.ts
│               ├── openai-agent.ts
│               └── gemini-agent.ts
```

---

## Step 5: Setup Multi-Agent Core Package

### 5.1 Create package.json

```bash
cat > packages/multi-agent-core/package.json << 'EOF'
{
  "name": "@gemini-cli/multi-agent-core",
  "version": "0.1.0",
  "type": "module",
  "description": "Multi-agent orchestration for Gemini CLI",
  "main": "./dist/index.js",
  "types": "./dist/index.d.ts",
  "exports": {
    ".": {
      "types": "./dist/index.d.ts",
      "default": "./dist/index.js"
    },
    "./meta-agent": {
      "types": "./dist/meta-agent.d.ts",
      "default": "./dist/meta-agent.js"
    },
    "./scheduler": {
      "types": "./dist/scheduler.d.ts",
      "default": "./dist/scheduler.js"
    }
  },
  "scripts": {
    "build": "tsc",
    "test": "vitest run",
    "test:watch": "vitest",
    "clean": "rm -rf dist"
  },
  "dependencies": {
    "@anthropic-ai/sdk": "^0.30.0",
    "openai": "^4.70.0",
    "@google/generative-ai": "^0.21.0"
  },
  "devDependencies": {
    "typescript": "^5.6.0",
    "vitest": "^2.0.0"
  }
}
EOF
```

### 5.2 Create tsconfig.json

```bash
cat > packages/multi-agent-core/tsconfig.json << 'EOF'
{
  "extends": "../../tsconfig.base.json",
  "compilerOptions": {
    "outDir": "./dist",
    "rootDir": "./src",
    "composite": true,
    "declarationMap": true
  },
  "include": ["src/**/*"],
  "exclude": ["node_modules", "dist", "**/*.test.ts"]
}
EOF
```

### 5.3 Add to Workspace

Edit root `package.json` to include our new package:

```bash
# Add to workspaces array
# "workspaces": [
#   "packages/*"  # This already includes our new package
# ]

# Install dependencies
npm install
```

---

## Step 6: Configure Environment

### 6.1 Create .env.local

```bash
cat > .env.local << 'EOF'
# API Keys for Multi-Agent System
ANTHROPIC_API_KEY=your_anthropic_key_here
OPENAI_API_KEY=your_openai_key_here
GOOGLE_API_KEY=your_google_key_here

# Scheduler Configuration
SCHEDULER_TYPE=multi-agent  # or "default"
SCHEDULER_DEBUG=true
EOF
```

### 6.2 Load Environment Variables

Edit `packages/core/src/config/config.ts` to support our new env vars:

```typescript
// Add to Config class
export class Config {
  // ... existing code

  getSchedulerType(): 'default' | 'multi-agent' {
    return (process.env.SCHEDULER_TYPE as any) || 'default';
  }

  isSchedulerDebugEnabled(): boolean {
    return process.env.SCHEDULER_DEBUG === 'true';
  }
}
```

---

## Step 7: Install patch-package

```bash
# Install patch-package for managing our modifications
npm install -D patch-package postinstall-postinstall

# Add to package.json scripts
npm pkg set scripts.postinstall="patch-package"
```

**Why?**
- When we modify `executor.ts`, we'll save it as a patch
- Future `npm install` will auto-apply our patch
- Makes upstream sync easier

---

## Step 8: Git Configuration

### 8.1 Update .gitignore

```bash
cat >> .gitignore << 'EOF'

# Multi-Agent Integration
.env.local
packages/multi-agent-core/dist/
packages/multi-agent-core/node_modules/

# Patch backups
*.orig
*.rej
EOF
```

### 8.2 Create .git/hooks/pre-commit

```bash
cat > .git/hooks/pre-commit << 'EOF'
#!/bin/bash
# Pre-commit hook: Run tests before commit

echo "Running pre-commit checks..."

# Run type check
npm run build --workspace @gemini-cli/multi-agent-core
if [ $? -ne 0 ]; then
  echo "❌ Build failed"
  exit 1
fi

# Run tests
npm run test --workspace @gemini-cli/multi-agent-core
if [ $? -ne 0 ]; then
  echo "❌ Tests failed"
  exit 1
fi

echo "✅ Pre-commit checks passed"
exit 0
EOF

chmod +x .git/hooks/pre-commit
```

---

## Step 9: Commit Initial Setup

```bash
# Stage all changes
git add .

# Commit
git commit -m "feat: setup multi-agent integration foundation

- Add multi-agent-core package
- Configure scheduler environment variables
- Add patch-package for modification management
- Update gitignore and git hooks
"

# Push to your fork
git push origin multi-agent-integration
```

---

## Step 10: Verify Setup

Run verification script:

```bash
# Create verification script
cat > scripts/verify-setup.sh << 'EOF'
#!/bin/bash

echo "🔍 Verifying Multi-Agent Setup..."
echo ""

# Check Node version
echo "✓ Checking Node.js version..."
node --version | grep -E "v(20|21|22)" || {
  echo "❌ Node.js >= 20.0.0 required"
  exit 1
}

# Check remotes
echo "✓ Checking Git remotes..."
git remote -v | grep upstream || {
  echo "❌ Upstream remote not configured"
  exit 1
}

# Check package structure
echo "✓ Checking package structure..."
[ -d "packages/multi-agent-core" ] || {
  echo "❌ multi-agent-core package missing"
  exit 1
}

[ -d "packages/core/src/schedulers" ] || {
  echo "❌ schedulers directory missing"
  exit 1
}

# Check dependencies
echo "✓ Checking dependencies..."
npm ls @anthropic-ai/sdk openai @google/generative-ai --workspace @gemini-cli/multi-agent-core > /dev/null 2>&1 || {
  echo "❌ Dependencies not installed"
  exit 1
}

# Check environment
echo "✓ Checking environment variables..."
[ -f ".env.local" ] || {
  echo "⚠️  .env.local not found (optional but recommended)"
}

echo ""
echo "✅ Setup verification passed!"
echo ""
echo "Next steps:"
echo "  1. Edit .env.local with your API keys"
echo "  2. Continue to Phase 2: Implement Scheduler Interface"
echo ""
EOF

chmod +x scripts/verify-setup.sh
./scripts/verify-setup.sh
```

---

## Troubleshooting

### Issue: Build fails with module errors

**Solution**:
```bash
# Clean and rebuild
npm run clean
rm -rf node_modules package-lock.json
npm install
npm run build
```

### Issue: Upstream remote already exists

**Solution**:
```bash
git remote remove upstream
git remote add upstream https://github.com/google-gemini/gemini-cli.git
```

### Issue: Permission denied for git hooks

**Solution**:
```bash
chmod +x .git/hooks/pre-commit
```

---

## What We've Accomplished

✅ Forked Gemini CLI and added upstream remote
✅ Created project structure for multi-agent code
✅ Set up independent package `@gemini-cli/multi-agent-core`
✅ Configured environment variables
✅ Installed patch-package for modification management
✅ Set up git hooks for quality checks

---

## Next Steps

Proceed to implementing the Scheduler Interface:

1. Create `packages/core/src/schedulers/port.ts`
2. Implement `DefaultScheduler`
3. Implement `MultiAgentScheduler` (stub)
4. Modify `AgentExecutor` injection point
5. Test the integration

See: `IMPLEMENTATION_STEP_BY_STEP.md`

---

## Quick Reference

### Important Directories
```
packages/core/src/schedulers/     # Scheduler interface
packages/multi-agent-core/        # Our core logic
packages/core/src/agents/         # Where we modify executor.ts
packages/cli/src/ui/              # UI customizations
```

### Important Commands
```bash
npm run build                     # Build all packages
npm run test                      # Run all tests
npm run start                     # Start Gemini CLI
git fetch upstream                # Fetch upstream changes
npm run build --workspace @gemini-cli/multi-agent-core  # Build our package
```

### Environment Variables
```bash
SCHEDULER_TYPE=multi-agent        # Enable our scheduler
SCHEDULER_DEBUG=true              # Debug logging
ANTHROPIC_API_KEY=...             # Claude API
OPENAI_API_KEY=...                # GPT API
GOOGLE_API_KEY=...                # Gemini API
```
