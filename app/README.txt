Windows student API lab - no authentication

1. Extract the complete ZIP into your own writable folder.
2. Open guide.html or the PDF and follow it from the beginning.
3. Prepare WSL 2 and Docker Desktop.
4. Run 01_Start.cmd and enter your assigned ID (S01-S20).
5. Run 02_Check.cmd to check both local and public URLs.
6. Read generated/my_lab.txt for your URL, employee and accounts.
7. Import generated/hr_training.yaml and bank_training.yaml into Orchestrate.
   Choose No authentication if an authentication selection appears.
8. Connect your tools to your agents and verify actual calls.
9. Run 03_Stop.cmd after the lab.

Only three CMD files are used: 01_Start, 02_Check and 03_Stop.
No API key is needed. No separate Python, Git or IBM Cloud CLI installation is required.
Cloudflare Quick Tunnel needs no Cloudflare account or personal domain.
Use your existing Orchestrate SaaS training account.

Each start creates a new tunnel. Update your imported tools with the new YAML.
Training data is preserved. Keep your PC, Docker and internet running during the lab.
Anyone who knows the public URL can read and change the fictional training data.
The ZIP includes no instructor credentials or live data.
Do not delete Docker volumes to fix connection problems.

To update an older kit: stop the containers, copy these files into the same folder,
leave .env.training and Docker volumes in place, then run 01_Start.cmd.
Use only the three CMD files listed above and update your own tools with the new YAML.
