#!/usr/bin/env node

const fs = require("fs");
const os = require("os");
const path = require("path");
const { spawnSync } = require("child_process");

const skillName = "skincare-product-selector";
const sourceDir = path.resolve(__dirname, "..");
const defaultTarget = path.join(os.homedir(), ".codex", "skills", skillName);

function help() {
  console.log(`skincare-product-selector installer

Usage:
  npx -y github:Hermess/skincare-product-selector install
  npx -y github:Hermess/skincare-product-selector install --with-python
  npx -y github:Hermess/skincare-product-selector doctor

Options:
  --target <path>      Install path. Default: ${defaultTarget}
  --with-python       Also install Python requirements and Playwright Chromium.
  --no-force          Do not overwrite an existing install.
  -h, --help          Show help.
`);
}

function parseArgs(argv) {
  const args = [...argv];
  const command = args[0] && !args[0].startsWith("-") ? args.shift() : "install";
  const options = {
    command,
    target: defaultTarget,
    withPython: false,
    force: true,
  };

  for (let i = 0; i < args.length; i += 1) {
    const arg = args[i];
    if (arg === "--target") {
      options.target = path.resolve(args[++i]);
    } else if (arg === "--with-python") {
      options.withPython = true;
    } else if (arg === "--no-force") {
      options.force = false;
    } else if (arg === "-h" || arg === "--help") {
      options.command = "help";
    } else {
      throw new Error(`Unknown argument: ${arg}`);
    }
  }
  return options;
}

function shouldSkip(relativePath) {
  const parts = relativePath.split(path.sep);
  return (
    parts.includes(".git") ||
    parts.includes("node_modules") ||
    parts.includes("__pycache__") ||
    parts.includes(".pytest_cache") ||
    relativePath === ".DS_Store" ||
    relativePath.endsWith(".pyc") ||
    relativePath.startsWith(path.join("assets", "audit"))
  );
}

function copyRecursive(src, dest, root = src) {
  const relative = path.relative(root, src);
  if (relative && shouldSkip(relative)) return;

  const stat = fs.statSync(src);
  if (stat.isDirectory()) {
    fs.mkdirSync(dest, { recursive: true });
    for (const entry of fs.readdirSync(src)) {
      copyRecursive(path.join(src, entry), path.join(dest, entry), root);
    }
    return;
  }
  fs.mkdirSync(path.dirname(dest), { recursive: true });
  fs.copyFileSync(src, dest);
}

function installPythonDeps(target) {
  const pip = spawnSync("python3", ["-m", "pip", "install", "-r", "requirements.txt"], {
    cwd: target,
    stdio: "inherit",
  });
  if (pip.status !== 0) process.exit(pip.status || 1);

  const playwright = spawnSync("python3", ["-m", "playwright", "install", "chromium"], {
    cwd: target,
    stdio: "inherit",
  });
  if (playwright.status !== 0) process.exit(playwright.status || 1);
}

function runDoctor(target) {
  const result = spawnSync("python3", ["tools/check_dependencies.py"], {
    cwd: target,
    stdio: "inherit",
  });
  process.exit(result.status || 0);
}

function install(options) {
  const target = options.target;
  if (fs.existsSync(target) && !options.force) {
    throw new Error(`Target already exists: ${target}. Use default install or remove --no-force.`);
  }

  fs.mkdirSync(path.dirname(target), { recursive: true });
  copyRecursive(sourceDir, target);

  console.log(`Installed ${skillName} to ${target}`);
  console.log("\nRecommended Codex plugins/connectors:");
  console.log("- Browser: inspect rendered pages and local previews");
  console.log("- Chrome: read user-visible logged-in or verified pages");
  console.log("- Computer Use: navigate dynamic official portals such as NMPA");
  console.log("- Spreadsheets/Documents: optional exports");

  if (options.withPython) {
    installPythonDeps(target);
  } else {
    console.log("\nOptional Python dependencies:");
    console.log(`cd ${target}`);
    console.log("python3 -m pip install -r requirements.txt");
    console.log("python3 -m playwright install chromium");
  }
  console.log("\nCheck install:");
  console.log(`cd ${target} && python3 tools/check_dependencies.py`);
}

try {
  const options = parseArgs(process.argv.slice(2));
  if (options.command === "help") {
    help();
  } else if (options.command === "install") {
    install(options);
  } else if (options.command === "doctor") {
    runDoctor(options.target);
  } else {
    throw new Error(`Unknown command: ${options.command}`);
  }
} catch (error) {
  console.error(`Error: ${error.message}`);
  process.exit(1);
}
