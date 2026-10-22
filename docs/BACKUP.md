# Database backup and rollback

Before applying a schema migration, stop writes to the store or put the app in maintenance mode, then copy the SQLite database and uploaded product images to a private location outside `app/static`. Preserve the backup until the release has passed its smoke checks.

PowerShell example from the project directory:

```powershell
$stamp = Get-Date -Format 'yyyyMMdd-HHmmss'
Copy-Item -LiteralPath 'instance\monster.db' -Destination "instance\monster-$stamp.db"
```

For a clean rollback, restore the backed-up database and the prior code revision together. The new migrations add nullable brand snapshots and fee settings; restoring the old database while leaving the newer code active is not a complete rollback. Keep uploads from before and after the release until the deployment is accepted. Do not put database copies, payment evidence, or customer exports beneath the public static directory.

The local project database was backed up before the IMPORT DISTRICT schema changes as `instance/monster-pre-import-district-20261020-025247.db`. This file is local state and must not be committed or served publicly.
