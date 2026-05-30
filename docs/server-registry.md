# Server Registry

The MobileCodex server registry tracks only preview servers started by MobileCodex. It is stored outside git in the operating system temp directory and scoped by workspace path.

## Start A Server

```powershell
py .\skills\mobile-codex-dev\scripts\mobile_dev.py server-start --root . --name app --port 5173 -- npm run dev -- --host 127.0.0.1 --port 5173
```

## List Servers

```powershell
py .\skills\mobile-codex-dev\scripts\mobile_dev.py server-list --root .
```

## Stop A Registered Server

```powershell
py .\skills\mobile-codex-dev\scripts\mobile_dev.py server-stop --root . --name app
```

## Safety Rule

MobileCodex should not stop arbitrary processes. It should only stop a server when the process was recorded in the registry for the current workspace.

## Handoff Use

The registry lets a Codex Mobile user ask what previews are still running, where the logs are, which port is active, and what can be stopped safely.

