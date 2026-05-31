"""
Knowledge-base articles for OCTAGON support — the corpus RAG retrieves from.

These are fictional support articles. Each maps to one or more technical tickets
in eval_set.py, so semantic retrieval has a genuinely relevant target to find:

    kb_automation_setup   <- case 2  (deepak: auto-assign by subject keyword)
    kb_automation_trouble <- case 4  (sam: automation stopped firing)
    kb_export_errors      <- case 5  (lena: export 500 error)
    kb_sso_saml           <- case 9  (anita: configure SAML SSO)
    kb_parent_child        <- H2     (trial.tech: parent-child ticketing)
    kb_import_macros       <- H3     (paid.happy: import canned responses)
    kb_slack_integration   <- H5     (paid.multi: Slack integration disconnecting)
    kb_login_recovery      <- H6     (unknown: forgot login email/password)
    kb_agent_seats         <- general (adding team members / seats)
    kb_portal_branding     <- general (portal customization)

Each article: a stable id, a title, and a few sentences of plausible content.
In production these would be your real Freshdesk solution articles.
"""

KB_ARTICLES = [
    {
        "id": "kb_automation_setup",
        "title": "Setting up ticket automation rules",
        "content": (
            "To automatically assign tickets based on their content, go to "
            "Admin > Automations > Ticket Assignment and create a new rule. "
            "Set the trigger to 'Ticket is created', add a condition such as "
            "'Subject contains' or 'Description contains' with your keyword, and "
            "set the action to 'Assign to Group' choosing the target team. Save "
            "and toggle the rule on. Rules run top to bottom, so order more "
            "specific rules above general ones."
        ),
    },
    {
        "id": "kb_automation_trouble",
        "title": "Automation rule stopped firing",
        "content": (
            "If an automation that previously worked stops triggering, first "
            "confirm the rule is still enabled under Admin > Automations. Check "
            "that its conditions still match incoming tickets (a renamed group or "
            "changed field can silently break a condition). Review the automation "
            "execution log to see whether the rule is being evaluated and skipped, "
            "or not evaluated at all. If the rule evaluates but takes no action, "
            "the conditions no longer match; if it never evaluates, another rule "
            "above it may be stopping further processing."
        ),
    },
    {
        "id": "kb_export_errors",
        "title": "Report export fails with a 500 error",
        "content": (
            "A 500 error when exporting a report is usually caused by an export "
            "that is too large or times out. Try narrowing the date range or "
            "applying filters to reduce the row count, then export again. "
            "Scheduled exports of very large reports are delivered by email "
            "rather than downloaded in-browser. If the error persists on a small "
            "export, clear the browser cache or try an incognito window; if it "
            "still fails, the issue is server-side and should be raised with "
            "support with the report name and time of the attempt."
        ),
    },
    {
        "id": "kb_sso_saml",
        "title": "Configuring SAML single sign-on (SSO)",
        "content": (
            "SAML SSO is available on Growth, Pro, and Enterprise plans. To set "
            "it up, go to Admin > Security > SSO and select SAML. Enter the IdP's "
            "sign-in URL and certificate from your identity provider (Okta, Azure "
            "AD, etc.), then copy OCTAGON's ACS URL and Entity ID back into your "
            "IdP configuration. Map the email attribute so users are matched "
            "correctly. Test with a single account before enabling SSO for all "
            "agents, and keep one local admin login as a fallback."
        ),
    },
    {
        "id": "kb_parent_child",
        "title": "Creating parent and child (linked) tickets",
        "content": (
            "Parent-child ticketing lets you break one request into linked "
            "sub-tickets. Open the parent ticket, choose 'Create Linked Ticket' "
            "or 'Add Child', and select a child template if you use them. Each "
            "child can be assigned to a different group and tracked separately, "
            "while the parent shows overall status. Note that the parent does not "
            "auto-close until all child tickets are resolved. If 'Create Linked "
            "Ticket' is not visible, the feature may need to be enabled under "
            "Admin > Ticket Settings."
        ),
    },
    {
        "id": "kb_import_macros",
        "title": "Importing canned responses from another tool",
        "content": (
            "To bring canned responses (macros) over from another help desk, "
            "export them from the source tool as a CSV with columns for title, "
            "body, and (optionally) folder. In OCTAGON go to Admin > Canned "
            "Responses > Import, upload the CSV, and map the columns. Responses "
            "import into the folder you specify, or a default folder if none is "
            "set. HTML formatting in the body is preserved; review a few after "
            "import to confirm placeholders and links carried over correctly."
        ),
    },
    {
        "id": "kb_slack_integration",
        "title": "Slack integration keeps disconnecting",
        "content": (
            "If the Slack integration repeatedly disconnects, the cause is almost "
            "always an expired or revoked authorization rather than a product "
            "fault. Go to Admin > Integrations > Slack and check the connection "
            "status. Click 'Reconnect' and complete the Slack OAuth prompt with "
            "an account that has permission to install apps in your workspace. If "
            "it disconnects again within a day, a Slack workspace admin may be "
            "removing the app or a token policy may be revoking it; confirm the "
            "OCTAGON app is approved in your Slack workspace's app settings."
        ),
    },
    {
        "id": "kb_login_recovery",
        "title": "Recovering access when you forget your login",
        "content": (
            "If you have forgotten your password, go to the login page and click "
            "'Forgot password' to receive a reset link by email. If you have also "
            "forgotten which email your account uses, ask a colleague who is an "
            "account admin to look up your user under Admin > Agents, or contact "
            "support from a verified company email. For security, support cannot "
            "send credentials directly and will verify ownership before restoring "
            "access. Accounts using SSO must be reset through your identity "
            "provider rather than the OCTAGON password reset."
        ),
    },
    {
        "id": "kb_agent_seats",
        "title": "Adding agents and managing seats",
        "content": (
            "To add a team member, go to Admin > Agents > New Agent, enter their "
            "email and role, and send the invite. Each active agent consumes one "
            "seat; if you are at your seat limit you will be prompted to add "
            "seats before the invite can be sent. Seats can be added from "
            "Admin > Plans & Billing, and changes are prorated to your billing "
            "cycle. Deactivating an agent frees their seat for reuse."
        ),
    },
    {
        "id": "kb_portal_branding",
        "title": "Customizing your support portal",
        "content": (
            "To match the support portal to your brand, go to Admin > Portal > "
            "Appearance. From there you can set your logo, primary color, and "
            "favicon, and edit the portal header and footer. For deeper changes, "
            "the portal supports custom CSS and editable page templates. Changes "
            "can be previewed before publishing, and you can revert to the "
            "default theme at any time. Custom domains for the portal are "
            "available on paid plans under Admin > Portal > Domain."
        ),
    },
]