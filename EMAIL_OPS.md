# EMAIL_OPS.md

Fast Gmail helpers.

## Scripts
- `tools/email_brief.py` — triage (`read_now` / `check_soon` / `skip_or_batch`)
- `tools/email_send.py` — policy-aware sender (auto-subject + footer + sender routing)
- `tools/daily_brief.py` — one-shot daily brief (email triage + weather)
- `tools/email_policy.json` — account/footer/priority-sender config

## What it does
- Pulls recent threads from Gmail via `gog`
- Scores each thread for priority (labels + sender/subject hints + priority sender list)
- Buckets into:
  - `read_now`
  - `check_soon`
  - `skip_or_batch`
- Sends emails with your rules enforced:
  - auto-generate subject when missing
  - sender routing (personal/work)
  - footer appended by default

## Usage
```bash
# Triage brief
python3 tools/email_brief.py
python3 tools/email_brief.py --query "newer_than:2d in:inbox" --max 50
python3 tools/email_brief.py --json

# Send with policy rules
python3 tools/email_send.py --to someone@example.com --body "hello there"
python3 tools/email_send.py --to someone@example.com --subject "Custom subject" --body "hello" --sender work

# Daily brief summary
python3 tools/daily_brief.py
```

## Notes
- Default account: `grant.m.anderson2021@gmail.com`
- Work account can be used once OAuth is completed for `grant@acmoate.com`.
