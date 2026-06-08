# Connectors

## How tool references work

Plugin files use `~~category` as a placeholder for whatever tool the user connects
in that category. Plugins are tool-agnostic - they describe workflows in terms of
categories rather than specific products. During customization (via the
cowork-plugin-customizer skill) these get mapped to the user's actual connector.

## Connectors for this plugin

| Category | Placeholder | Supported connectors | Used by |
|---|---|---|---|
| Email | `~~email` | Microsoft 365 / Outlook, Gmail | review-inbox, manage-ndas, request-bids, select-and-hot, client-report, deal-desk agent |
| Calendar | `~~calendar` | Microsoft 365 / Outlook Calendar, Google Calendar | deal-desk agent (books buyer and client meetings) |

Connect one email connector and one calendar connector. The plugin works with either
provider in each category; Outlook and Gmail are interchangeable for email, and
Outlook Calendar and Google Calendar are interchangeable for calendar.

## Notes

- **Email** reads the inbox (to detect new buyers, signed NDAs, and incoming bids) and
  sends NDAs, chasers, bid requests, and (in `auto` mode) client correspondence. Both
  **Microsoft 365 / Outlook** and **Gmail** are first-class options; pick whichever
  the agent already uses. The Deal Desk agent uses email to draft buyer follow-up and
  chaser messages.
- **Calendar** is used by the Deal Desk agent to book meetings at the relevant stages:
  buyer viewings/access, the bid-deadline call, the preferred-bidder/Heads of Terms
  meeting, and exchange/completion checkpoints with the client. Use **Outlook
  Calendar** (with Microsoft 365) or **Google Calendar** (with Gmail). If no calendar
  is connected, the agent proposes times in its standup instead of booking.
- **Document storage is local.** All deal files (tracker, NDA template, Heads of Terms,
  signed NDAs, bid log, change log) live in the agent's connected Cowork folder, not in
  a cloud connector. No storage connector is required.
- **Scheduling and the live dashboard** use built-in Cowork features (scheduled tasks
  and live artifacts), so they need no connector. The Deal Desk agent is designed to be
  run by a weekday-morning scheduled task.
