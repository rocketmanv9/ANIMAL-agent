# Middleware Hook Contract

Integrate these hooks into agent lifecycle:

## On boot
`python3 tools/persistctl.py boot`

## After every significant step
`python3 tools/persistctl.py step --summary "..." --payload '{...}'`

## On periodic scheduler tick
`bash tools/persistence_scheduler.sh`

## On shutdown
`python3 tools/persistctl.py shutdown --payload '{"status":"clean"}'`

## EOD reflection
`python3 tools/persistctl.py reflect-eod --wins "..." --misses "..." --carry-forward '[]'`

## Weekly reflection
`python3 tools/persistctl.py reflect-weekly --wins "..." --misses "..." --carry-forward '[]'`
