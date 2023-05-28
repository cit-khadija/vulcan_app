import frappe

# TODO: check if this really works
def override_status_updater(doc, event):
    pass
    # from erpnext.stock.doctype.delivery_note.delivery_note import DeliveryNote
    # doc.status_updater.extend([
    #     {
	# 			"source_dt": "Delivery Note Item",
	# 			"target_dt": "Ordered Item",
	# 			"join_field": "ordered_item",
	# 			"target_field": "delivered_qty",
	# 			"target_parent_dt": "Order Processing",
	# 			"target_parent_field": "per_delivered",
	# 			"target_ref_field": "qty",
	# 			"source_field": "qty",
	# 			"percent_join_field": "against_order_processing",
	# 			"status_field": "delivery_status",
	# 			"keyword": "Delivered",
	# 			"second_source_dt": "Sales Invoice Item",
	# 			"second_source_field": "qty",
	# 			"second_join_field": "so_detail",
	# 			"overflow_type": "delivery",
	# 			"second_source_extra_cond": """ and exists(select name from `tabSales Invoice`
	# 			where name=`tabSales Invoice Item`.parent and update_stock = 1)""",
    #     },
    # ])
    # print(doc.status_updater)

def validate(doc, event):
    for item in doc.items:
        if item.against_order_processing and item.ordered_item:
            if item.item_group == "Partial Delivery Item":
                oi = frappe.get_doc("Ordered Item", item.ordered_item)
                total_deliverable = (oi.qty - oi.delivered_qty) - oi.delivered_parts
                if item.qty > total_deliverable:
                    frappe.throw("Please recheck the quantity.")


def after_submit(doc, event):
    print("*****************************************")
    for item in doc.items:
        if item.against_order_processing and item.ordered_item:
            if item.item_group == "Partial Delivery Item":
                print("*****************************************")
                print("This is happening")
                oi_delivered_parts = frappe.db.get_value("Ordered Item", item.ordered_item, "delivered_parts")
                frappe.db.set_value("Ordered Item", item.ordered_item, "delivered_parts", oi_delivered_parts+item.qty)