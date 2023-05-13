import frappe
from frappe.model.mapper import get_mapped_doc
from frappe import _

@frappe.whitelist()
def make_order_processing(source_name, target_doc=None):

    op = frappe.db.exists("Order Processing", {"sales_order":source_name})

    if op:
        frappe.msgprint(
		_("Order Processing Document {0} already created")
		.format("<a href='/app/order-processing/{0}'>{0}</a>")
		.format(op)
	    )
        #TODO error showing up in console. resolve
    else:
        doc = get_mapped_doc(
            "Sales Order",
            source_name,
            {
                "Sales Order":{
                    "doctype": "Order Processing",
                    "validation": {"docstatus": ["=",1]},
                    "field_map":{
                        "name": "sales_order",
                        "items": "items",
                        "sales_order":"sales_order",
                        "transaction_date":"transaction_date"
                    }
                }
            },
            target_doc,
        )

        return doc