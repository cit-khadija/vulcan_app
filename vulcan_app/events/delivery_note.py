import frappe


# TODO: check if this really works
def override_status_updater(doc, event):
    # from erpnext.stock.doctype.delivery_note.delivery_note import DeliveryNote
    doc.status_updater.extend([
        {
				"source_dt": "Delivery Note Item",
				"target_dt": "Ordered Item",
				"join_field": "ordered_item",
				"target_field": "delivered_qty",
				"target_parent_dt": "Order Processing",
				"target_parent_field": "per_delivered",
				"target_ref_field": "qty",
				"source_field": "qty",
				"percent_join_field": "order_processing",
				"status_field": "delivery_status",
				"keyword": "Delivered",
				"second_source_dt": "Sales Invoice Item",
				"second_source_field": "qty",
				"second_join_field": "so_detail",
				"overflow_type": "delivery",
				"second_source_extra_cond": """ and exists(select name from `tabSales Invoice`
				where name=`tabSales Invoice Item`.parent and update_stock = 1)""",
        },
    ])
    print(doc.status_updater)