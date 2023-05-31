# TODO: update_work_order_produced_qty and order_processing manufactured qty without cache reload

import frappe
from frappe import _
from frappe.utils import flt

def on_submit(doc, method=None):
    if doc.custom_work_order:
        update_work_order(doc)

def on_cancel(doc, method=None):
    if doc.custom_work_order:
        update_work_order(doc)

def before_submit(doc, method=None):
    if doc.custom_work_order and doc.stock_entry_type == "Bulk Manufacture":
        validate_quantities(doc)

def update_work_order(doc):
    def _validate_work_order(pro_doc):
        msg, title = "", ""
        if flt(pro_doc.docstatus) != 1:
            msg = f"Custom Work Order {doc.custom_work_order} must be submitted"

        if pro_doc.status == "Stopped":
            msg = f"Transaction not allowed against stopped Work Order {doc.custom_work_order}"

        if doc.is_return and pro_doc.status not in ["Completed", "Closed"]:
            title = _("Stock Return")
            msg = f"Work Order {doc.custom_work_order} must be completed or closed"

        if msg:
            frappe.throw(_(msg), title=title)

    if doc.custom_work_order:
        pro_doc = frappe.get_doc("Custom Work Order", doc.custom_work_order)
        _validate_work_order(pro_doc)
        if doc.stock_entry_type == "Bulk Manufacture":
            pro_doc.run_method("update_work_order_qty")
            pro_doc.run_method("set_status")


        # if doc.fg_completed_qty:
        #     pro_doc.run_method("update_work_order_qty")
        #     if doc.purpose == "Manufacture":
        #         #TODO: check if this is required...update_planned_qty might be required
        #         pro_doc.run_method("update_planned_qty")
        #         pro_doc.update_batch_produced_qty(doc) #only for batch items

        # pro_doc.run_method("update_status")
        # if not pro_doc.operations:
        #     pro_doc.set_actual_dates()


def validate_quantities(doc):
    check_rm_list = frappe.db.sql(f"""
        select sed.idx, sed.qty as s_qty, rm.qty as c_qty from `tabStock Entry Detail` sed, `tabCustom Work Order Raw Material Item` rm
        where sed.cwo_item = rm.name and sed.parent = "{doc.name}" order by sed.idx
    """, as_dict=1)

    check_po_list = frappe.db.sql(f"""
        select sed.idx, sed.qty as s_qty, po.planned_qty as c_qty from `tabStock Entry Detail` sed, `tabCustom Work Order Item` po
        where sed.cwo_item = po.name and sed.parent = "{doc.name}" order by sed.idx
    """, as_dict=1)

    for list_ in [check_rm_list, check_po_list]:
        for i in list_:
            if i.s_qty != i.c_qty:
                message = f'Quantity does not match custom work order qty at Row#{i.idx}'
                frappe.throw(message)



