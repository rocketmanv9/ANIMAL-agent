# Google Calendar Integration Runbook (Personal)

Status: In progress

## What’s installed
- `gcalcli` installed at:
  - `C:\Users\grant\AppData\Roaming\Python\Python312\Scripts\gcalcli.exe`

## Current setup choice
- Scope: **Personal calendar only** (for now)
- Application type used in Google Cloud: **Desktop app**

## Credentials (stored per your explicit request)
- Client ID: `<CLIENT_ID>`
- Client Secret: `<CLIENT_SECRET>`

## One-time auth step (you run in Windows PowerShell)
```powershell
& "$env:USERPROFILE\AppData\Roaming\Python\Python312\Scripts\gcalcli.exe" init --client-id "<CLIENT_ID>" --client-secret "<CLIENT_SECRET>"
```

Then:
1. Sign into your personal Google account
2. Approve Calendar access
3. Return to terminal and confirm init completed

## Verification commands
```powershell
# today agenda
gcalcli --nocolor agenda today tomorrow

# list calendars
gcalcli --nocolor list
```

## Assistant operating rules (after auth)
- Default to **today-only** agenda unless you ask for a wider range.
- I can add/edit/delete events on request.
- If a request is ambiguous (multiple matching events), I will ask to disambiguate first.

## Security notes
- Do **not** store client secret in plain docs long-term.
- Rotate/reissue secret if shared in chat or logs.

## Next planned expansion
- Add Work calendar as separate profile after personal is stable.
