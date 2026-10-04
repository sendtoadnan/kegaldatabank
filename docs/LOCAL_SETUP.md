# Running the project on a Mac

One-time setup (about 30 minutes). Type each line in **Terminal** (⌘ Space → "Terminal") and press Return.

1. **Check the tools:** `git --version`, `python3 --version`, `node -v`. If git or python3 is missing, accept the "Command Line Developer Tools" install. If node is missing, install the LTS version from https://nodejs.org.
2. **Install Claude Code:** `curl -fsSL https://claude.ai/install.sh | bash`. If it reports that `~/.local/bin` is not in your PATH, run
   `echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.zshrc && source ~/.zshrc`, then check with `claude --version`.
3. **GitHub CLI:** download `gh_…_macOS_universal.pkg` from https://github.com/cli/cli/releases/latest. If macOS says it "could not verify" it, click Done, then System Settings → Privacy & Security → Open Anyway. Then `gh auth login` (GitHub.com → HTTPS → Yes → Login with a web browser) and `gh auth setup-git`.
4. **Get the project:** `cd ~/Documents`, `git clone https://github.com/sendtoadnan/kegaldatabank.git`, `cd kegaldatabank`.
5. **PDF library:** `python3 -m pip install --user pymupdf` (add `--break-system-packages` if pip refuses). Warnings about PATH or an old pip are harmless.
6. **Test:** `npm test` should end with `fail 0`.
7. **Start Claude:** `claude`, log in with your claude.ai account and trust the folder. Then add the OneDrive working folder once:
   `/add-dir "~/Library/CloudStorage/OneDrive-Personal/Pak Legal Data Bank"`

## Every working day
```
cd ~/Documents/kegaldatabank
git pull
claude
```
In Claude: `/model` switches to a cheaper model for routine work, `/clear` starts a fresh task, `/exit` quits.

## Where things live
- **OneDrive `Pak Legal Data Bank`** — your PDFs, section-wise regulations and notifications, the Unified folder. Work here.
- **Documents/kegaldatabank** — the website project (code and data), backed up on GitHub. Keep it out of OneDrive and iCloud: syncing the hidden `.git` folder can corrupt it.
