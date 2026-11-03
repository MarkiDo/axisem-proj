# Sharing `axisem/SOLVER/model2` as an Instaseis server via VS Code

This guide explains how to serve the `model2` database with the Instaseis server and share it with another person using VS Code port forwarding (Dev Tunnels). The recipient opens it with `instaseis.open_db(url)` and queries seismograms remotely, without downloading the database.

## Prerequisites

- VS Code with a GitHub or Microsoft account to sign in with
- Python environment with Instaseis installed (on both your side and the recipient's)
- The database folder: `axisem/SOLVER/model2` (about 716 MB)
- `model2/PX/Data/ordered_output.nc4` and `model2/PZ/Data/ordered_output.nc4` must exist. They are produced by the AxiSEM post-processing step. `axisem_output.nc4` alone is not enough.

## 1. Check what you are sharing

The Instaseis server only exposes seismogram queries (`/info`, `/seismogram`, etc.), not the raw files. Still, check the database is complete:

```bash
ls /Users/markdobush/Projects/axisem-proj/axisem/SOLVER/model2/PX/Data/ordered_output.nc4
ls /Users/markdobush/Projects/axisem-proj/axisem/SOLVER/model2/PZ/Data/ordered_output.nc4
```

## 2. Start the Instaseis server

Open the VS Code integrated terminal (`` Ctrl+` ``) with the Instaseis environment active and run:

```bash
cd /Users/markdobush/Projects/axisem-proj
python -m instaseis.server --port 8000 axisem/SOLVER/model2
```

Check it locally. This should return JSON, not a 404:

```bash
curl http://localhost:8000/info
```

## 3. Forward the port in VS Code

1. Open the **Ports** panel (next to the Terminal tab). If it is hidden, open the Command Palette and run `Ports: Focus on Ports View`.
2. Port `8000` is usually detected automatically. If it is not, click **Forward a Port** and enter `8000`.
3. Sign in with GitHub or Microsoft if prompted.
4. Right-click the port, choose **Port Visibility**, then pick one:

   | Visibility | Who can open the link |
   |---|---|
   | Private (default) | Only you, signed in with the same account |
   | Organization | Members of your organization |
   | Public | Anyone with the link, with no sign-in |

   Scripts such as `instaseis.open_db` cannot sign in, so use **Public** for non-interactive access.

5. Copy the **Forwarded Address**. It looks like `https://xxxx-8000.devtunnels.ms`.

## 4. Share the link

Send the forwarded address to the recipient. They open the database by URL (see [instaseis/main.py](instaseis/main.py)):

```python
import instaseis
db = instaseis.open_db('https://xxxx-8000.devtunnels.ms/')
print(db)
```

If the port is not Public, the Dev Tunnels warning page blocks scripts. The recipient must open the link in a browser once and click **Continue**, or you must set the port to Public.

Only computed seismograms travel over the tunnel, so the large `.nc4` files are never downloaded. Every query runs on your machine, so the server and VS Code must stay running while they work.

## 5. Stop sharing

- Press `Ctrl+C` in the terminal to stop the server.
- In the Ports panel, right-click the port and choose **Stop Forwarding Port**.

The tunnel only works while VS Code is open and the server is running.

## Troubleshooting

| Problem | Cause / fix |
|---|---|
| `instaseis.open_db(url)` fails or `/info` returns 404 | The tunnel is serving something other than the Instaseis server (e.g. `python3 -m http.server`, which only shows a directory listing). Stop it and run step 2. |
| Server cannot find the database | `PX/Data/ordered_output.nc4` and `PZ/Data/ordered_output.nc4` are missing. Run AxiSEM post-processing first. |
| Public visibility is greyed out | An organization policy disables it. Use Organization visibility, or ask an admin. |
| Port 8000 is not listed | Forward it manually with **Forward a Port**. |
| `Address already in use` | Choose another port, e.g. `--port 8001`, and forward that one. |
| Queries are slow | Every request runs on your machine through the tunnel. Share the database files instead (see below) if the recipient needs heavy use. |

## Other ways to share

- **Same network:** share `http://<your-LAN-IP>:8000`. Get the IP with `ipconfig getifaddr en0`.
- **VS Code Live Share:** share your workspace and forwarded ports with specific invited people instead of a public link.
- **cloudflared / ngrok:** `cloudflared tunnel --url http://localhost:8000` or `ngrok http 8000` (both need installing first).
- **Copy the files:** serve the folder with `python3 -m http.server 8000` and let the recipient download it with `wget -r -np -nH <url>`, then open it locally with `instaseis.open_db('/path/to/model2')`. This exposes the whole folder, so never serve the project root.

## Security notes

- A Public link lets anyone who has it query your database and use your machine's CPU.
- Do not serve the project root: it contains source code and git history.
- Stop the server and tunnel when you are finished.
