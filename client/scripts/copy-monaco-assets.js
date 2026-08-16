// Copies Monaco's pre-built AMD bundle into public/ so the code editor loads
// it from this app's own origin instead of a third-party CDN (no external
// dependency at runtime, works offline/behind restrictive network policies).
// Runs automatically after `npm install` via the package.json postinstall hook.
const fs = require("fs");
const path = require("path");

const source = path.join(__dirname, "..", "node_modules", "monaco-editor", "min", "vs");
const destination = path.join(__dirname, "..", "public", "monaco", "vs");

if (!fs.existsSync(source)) {
  console.warn("monaco-editor package not found; skipping asset copy.");
  process.exit(0);
}

fs.rmSync(destination, { recursive: true, force: true });
fs.mkdirSync(path.dirname(destination), { recursive: true });
fs.cpSync(source, destination, { recursive: true });

console.log(`Copied Monaco assets to ${path.relative(process.cwd(), destination)}`);
