"""Code changes applied to a scratch copy between the b- and c-sessions.

They simulate teammates' commits landing after memories were saved.
Every edit must match exactly once (or, for renames, at least once).
"""
import re
import sys
from pathlib import Path


def once(path, old, new):
    t = path.read_text()
    assert t.count(old) == 1, f"{path}: {t.count(old)} matches"
    path.write_text(t.replace(old, new))


def rename(root, old, new, exts):
    n = 0
    for p in root.rglob("*"):
        if p.is_file() and p.suffix in exts:
            t = p.read_text(errors="ignore")
            if re.search(rf"\b{old}\b", t):
                p.write_text(re.sub(rf"\b{old}\b", new, t))
                n += 1
    assert n, f"{old} not found"
    return n


def project_a(root):
    src = root / "src"
    # Rename (topic M): the restore method used by the cron job and appeals.
    rename(src, "restoreSuspendedUserByPhoneNumber", "liftSuspensionByPhoneNumber",
           {".ts"})
    # Logic (topic P): webhook retries no longer credit twice.
    once(src / "payment/pay-in/pay-in.service.ts",
         "      `Process checkout completed with data: ${JSON.stringify(checkoutCompletedDto)}`,\n"
         "    );\n",
         "      `Process checkout completed with data: ${JSON.stringify(checkoutCompletedDto)}`,\n"
         "    );\n"
         "    const existingTransaction = await this.transactionsService.findByPaymentId(\n"
         "      checkoutCompletedDto.externalPaymentId,\n"
         "    );\n"
         "    if (existingTransaction) {\n"
         "      this.logger.warn(\n"
         "        `Duplicate checkout event ignored for payment ${checkoutCompletedDto.externalPaymentId}`,\n"
         "      );\n"
         "      return;\n"
         "    }\n")
    once(src / "transactions/transactions.service.ts",
         "  async updateMany(ids: string[], data: Partial<Transaction>): Promise<void> {\n",
         "  async findByPaymentId(paymentId: string): Promise<Transaction | null> {\n"
         "    if (!paymentId) {\n"
         "      return null;\n"
         "    }\n"
         "    return this.transactionsRepository.findOne({ where: { paymentId } });\n"
         "  }\n\n"
         "  async updateMany(ids: string[], data: Partial<Transaction>): Promise<void> {\n")


def project_b(root):
    java = root / "SiftOrder/src"
    # Rename (topic R): the per-config generation methods.
    rename(java, "generateInvoicesForConfig", "processRecurringConfig", {".java"})
    rename(java, "generateInvoiceForConfig", "createInvoiceFromConfig", {".java"})
    # Logic (topic O): a re-send no longer emails the order subscribers.
    svc = java / "main/java/com/siftit/domain/ordering/RestaurantOrderService.java"
    once(svc, "        if (isResend) {\n            sendOrderEmail(order);\n",
              "        if (isResend) {\n            sendOrderEmail(order, false);\n")
    once(svc, "        sendOrderEmail(existingOrder);\n        syncEventService.fire",
              "        sendOrderEmail(existingOrder, true);\n        syncEventService.fire")
    once(svc, "    private void sendOrderEmail(SimpleOrder existingOrder) {\n",
              "    private void sendOrderEmail(SimpleOrder existingOrder, boolean includeSubscribers) {\n")
    once(svc, "        if (existingOrder.hasFoodCategories()) {\n",
              "        if (includeSubscribers && existingOrder.hasFoodCategories()) {\n")
    once(svc, "        if (existingOrder.hasBarCategories()) {\n",
              "        if (includeSubscribers && existingOrder.hasBarCategories()) {\n")


if __name__ == "__main__":
    {"project-a": project_a, "project-b": project_b}[sys.argv[1]](Path(sys.argv[2]))
    print("changes applied:", sys.argv[1], sys.argv[2])
