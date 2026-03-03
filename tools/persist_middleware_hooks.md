# Middleware Hook Contract

Integrate these hooks into agent lifecycle:

## On boot (mandatory open-loop surfacing)
```bash
python3 tools/persistctl.py boot
python3 tools/persistctl.py startup-summary
```

## After every significant step
`python3 tools/persistctl.py step --summary "..." --payload '{...}'`

## On periodic scheduler tick (6h reevaluation)
`bash tools/persistence_scheduler.sh`

## If stalled open loops detected
- Ask user for direction when `ask_for_direction=true`.
- If infra task exists in `infra_confirmation_needed`, explicitly ask for infra status confirmation.
- If `credential_prompts` contains entries, prompt for credentials with required scopes.

## On shutdown
`python3 tools/persistctl.py shutdown --payload '{"status":"clean"}'`

## EOD reflection
`python3 tools/persistctl.py reflect-eod --wins "..." --misses "..." --carry-forward '[]'`

## Weekly reflection
`python3 tools/persistctl.py reflect-weekly --wins "..." --misses "..." --carry-forward '[]'`
