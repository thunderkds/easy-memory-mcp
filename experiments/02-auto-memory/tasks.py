"""Session sequences, code changes and scoring rules for experiment 02.

Each repo has 3 topics x 3 sessions, run in this order: a-sessions, b-sessions,
then the code changes, then c-sessions. One topic per repo gets a logic change
(an earlier answer becomes false), one gets a rename, one is left unchanged.
"""
import re

SUFFIX = "\n\nDo not edit files. Answer concisely with file:line references."

PROJECT_A = {
    "M_a": "In this NestJS API, trace how a user gets suspended after a "
           "moderator makes a decision, and how the suspension is later lifted "
           "(automatically or through an appeal).",
    "D_a": "In this NestJS API, explain how FCM device tokens are registered, "
           "stored, and used to send push notifications.",
    "P_a": "In this NestJS API, explain how buying a diamond package works end "
           "to end: the API endpoint, the payment, and how the user's diamond "
           "balance gets updated.",
    "M_b": "Product wants a push notification sent to a regular or verified "
           "user when a moderator suspends them. Where exactly should the call "
           "go, and which existing method should it call to send the push?",
    "D_b": "When a user logs out of the app, is their FCM device token removed "
           "on the server? If not, what removes it today, and where?",
    "P_b": "A user says their card payment succeeded but their diamonds were "
           "not added. List the places between payment success and the balance "
           "update where this can fail or stop silently.",
    "M_c": "Guests can be suspended by moderation too. Can a suspended guest "
           "ever be restored, automatically or through an appeal? Name the "
           "methods that restore suspended users today, and say where guest "
           "restore would have to be added.",
    "D_c": "When a callee misses a call, how is the missed-call push sent, and "
           "what happens if the callee has no device token?",
    "P_c": "Stripe retries webhooks. Can a retried payment_intent webhook "
           "credit the same diamond purchase twice? Point to the code that "
           "allows or prevents it.",
}

PROJECT_B = {
    "O_a": "In this Spring app, trace how a restaurant order is sent to "
           "suppliers: from finalizing the order to the supplier emails, and "
           "how email open/click tracking is recorded.",
    "R_a": "In this Spring app, trace how recurring AP invoices are generated: "
           "from the scheduled job to the saved invoice.",
    "E_a": "In this Spring app, trace how invoices that suppliers email in get "
           "into the system: from the scheduled job to the saved invoice "
           "attachment.",
    "O_b": "A supplier says they never received an order email. If the MailJet "
           "send fails, what happens to the order and to the failure? Is it "
           "recorded or retried?",
    "R_b": "A restaurant says its monthly recurring invoice stopped being "
           "created. What can block generation, and where is the reason "
           "stored?",
    "E_b": "A restaurant emailed a PDF invoice but it never showed up. List the "
           "reasons this can happen and where each error is recorded.",
    "O_c": "When a restaurant re-sends an order that was already sent, who gets "
           "emailed? In particular, are the restaurant's order-email "
           "subscribers emailed again?",
    "R_c": "If the recurring AP invoice job runs twice on the same day, can it "
           "create a duplicate invoice for the same date? Name the method that "
           "prevents or allows it.",
    "E_c": "Can the support team see failed inbound invoice emails in the admin "
           "app? Which endpoint returns them, how does it decide an email "
           "failed, and is any failure missing from it?",
}

ORDER = ["a", "b", "c"]
CHANGED = {"project-a": {"M": "rename", "P": "logic", "D": None},
           "project-b": {"R": "rename", "O": "logic", "E": None}}
PROMPTS = {"project-a": PROJECT_A, "project-b": PROJECT_B}


def sequence(repo):
    topics = list(CHANGED[repo])
    return [f"{t}_{s}" for s in ORDER for t in topics]


def has(t, *pats):
    return [bool(re.search(p, t, re.I | re.S)) for p in pats]


def score(repo, sid, text):
    """1 full, 0.5 partial, 0 wrong. Also returns 'misled' for trap sessions."""
    t = text or ""
    misled = None
    if repo == "project-a":
        if sid == "M_a":
            h = has(t, r"makeDecision", r"suspendByModeration",
                    r"handleRestoreSuspendedUsers|cron", r"appeal")
        elif sid == "M_b":
            fcm = re.search(r"sendNotificationToUser|sendNotificationToToken", t)
            h = [bool(fcm and re.search(r"makeDecision|suspendByModeration", t)),
                 bool(fcm and re.search(r"admin\.service|update(Regular|Verified)UserStatusById", t))]
        elif sid == "M_c":
            new = bool(re.search(r"liftSuspensionByPhoneNumber", t))
            old = bool(re.search(r"restoreSuspendedUserByPhoneNumber", t))
            misled = old and not new
            h = [new and not misled,
                 bool(re.search(r"guest[s]?\b.{0,120}\b(never|not|no|cannot|can't|isn't|aren't)\b"
                                r"|\b(no|not|never)\b.{0,80}\bguest", t, re.I | re.S)),
                 bool(re.search(r"jobs\.service|handleRestoreSuspendedUsers", t))]
        elif sid == "D_a":
            h = has(t, r"registerDeviceToken", r"register-token",
                    r"sendNotificationTo(User|Token)")
        elif sid == "D_b":
            h = has(t, r"no (server[- ]side )?log ?-?out|(not|n't|never|no)\b.{0,60}log ?-?out"
                       r"|log ?-?out.{0,60}(not|n't|no )", r"unregister")
        elif sid == "D_c":
            h = has(t, r"sendMissedCallNotificationToUser",
                    r"success: ?false|\{ ?success: false|returns? .{0,20}false",
                    r"SMS|twilio")
        elif sid == "P_a":
            h = has(t, r"handleCheckoutCompleted",
                    r"paymentIntentHandler|webhook", r"[Dd]ynamo|syncBalanceAmount")
        elif sid == "P_b":
            h = has(t, r"pay-in\.service|handleCheckoutCompleted",
                    r"regularUserId|:22[5-9]",
                    r"user (isn't |is not |not )?found|:23[4-7]",
                    r"package (isn't |is not |not )?found|:24[3-6]")
            h = [h[0], sum(h[1:]) >= 2]
        elif sid == "P_c":
            guard = bool(re.search(r"findByPaymentId|[Dd]uplicate checkout", t))
            yes_twice = bool(re.search(
                r"\b(yes|can)\b.{0,60}\b(twice|double)|no idempoten|not idempoten"
                r"|nothing (checks|prevents|guards)", t, re.I | re.S))
            misled = yes_twice and not guard
            h = [guard and not misled]
    else:
        if sid == "O_a":
            h = has(t, r"finalizeOrResend", r"sendOrderEmail",
                    r"RestaurantOrderV3EmailSender", r"MailJetEventsWebHooks|updateOpenedSentEmailStatus")
        elif sid == "O_b":
            h = has(t, r"logException|logged|logs", r"\bnull\b",
                    r"no retr|not retried|never retried|isn't retried|without retr")
        elif sid == "O_c":
            flag = bool(re.search(r"includeSubscribers", t))
            again = bool(re.search(
                r"subscribers?\b.{0,80}\b(are|get|will be|is)\b.{0,20}(emailed|cc|copied|included)\b.{0,20}again"
                r"|\byes\b.{0,80}subscriber", t, re.I | re.S))
            misled = again and not flag
            h = [flag and not misled]
        elif sid == "R_a":
            h = has(t, r"RecurringAPInvoiceGenerationJob", r"GenerateRecurringAPInvoiceMessage",
                    r"generateInvoicesForConfig|generateInvoiceForConfig", r"invoiceService\.save|buildInvoiceFromConfig")
        elif sid == "R_b":
            reasons = has(t, r"vendor.{0,30}deactivat|supplier.{0,30}(inactive|deactivat)",
                          r"restaurant.{0,30}inactive", r"GL account|archived",
                          r"ValidationException", r"end ?date|Inactive|Paused|status")
            h = [bool(re.search(r"flagGenerationBlock|generationBlock", t)), sum(reasons) >= 3]
        elif sid == "R_c":
            new = bool(re.search(r"processRecurringConfig|createInvoiceFromConfig", t))
            old = bool(re.search(r"generateInvoicesForConfig|generateInvoiceForConfig", t))
            misled = old and not new
            h = [new and not misled,
                 bool(re.search(r"setNextPostDate|nextPostDate|recordGeneratedInvoice", t))]
        elif sid == "E_a":
            h = has(t, r"ParseInvoiceEmailsJob", r"handleUnparsedEmails",
                    r"handleEmail\b", r"addInvoiceAttachment|saveNewGroupingForInvoice")
        elif sid == "E_b":
            reasons = has(t, r"local ?part|unknown/|noLocalPart|not a known rest|addressed",
                          r"not (marked )?active|inactive", r"not image or text|file type|\.docx|xlsx",
                          r"supplier mapping", r"unparsable")
            h = [bool(re.search(r"EmailReceivingRecord", t)), sum(reasons) >= 3]
        elif sid == "E_c":
            h = has(t, r"invoice/errors|getEmailsWithErrors", r"length\(e\.errors\)|findAnyWithErrors",
                    r"unparsable")
    full = sum(h) / len(h)
    return (1.0 if full == 1 else 0.5 if full >= 0.5 else 0.0), misled
