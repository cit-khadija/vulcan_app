# Copyright (c) 2023, Crafrt and contributors
# For license information, please see license.txt

import frappe

import json
from frappe.model.document import Document
from frappe.model.naming import getseries
from frappe import _, qb
from erpnext.stock.get_item_details import get_default_bom
from frappe.utils import flt
from frappe.query_builder.functions import Sum
from frappe.model.mapper import get_mapped_doc

class OrderProcessing(Document):
	def autoname(self):
		#naming based on sales order
		so_number = self.sales_order[8:]
		prefix = 'OP-{}-'.format(so_number)
		self.name = prefix + getseries(prefix, 3)

@frappe.whitelist()
def get_items_to_deliver(order_processing):
	if order_processing:
		op = frappe.get_doc("Order Processing", order_processing)
		items = []
		for item in op.items:
			delivered_via_dn = frappe.db.sql(f"""select sum(qty) from `tabDelivery Note Item`
				where so_detail = "{item.sales_order_item}" and docstatus = 1
				and against_sales_order = "{item.sales_order}" """
			)

			delivered_via_si = frappe.db.sql(
				f"""select sum(si_item.qty)
				from `tabSales Invoice Item` si_item, `tabSales Invoice` si
				where si_item.parent = si.name and si.update_stock = 1
				and si_item.so_detail = "{item.sales_order_item}" and si.docstatus = 1
				and si_item.sales_order = "{item.sales_order}" """,
			)

			total_delivered_qty = (flt(delivered_via_dn[0][0]) if delivered_via_dn else 0) + (
			flt(delivered_via_si[0][0]) if delivered_via_si else 0
			)

			if item.delivered_qty != total_delivered_qty:
				item.db_set("delivered_qty", total_delivered_qty)

			if item.delivered_qty < item.manufactured_qty:
				pending_qty = item.manufactured_qty - item.delivered_qty
				if pending_qty:
					items.append(
						dict(
							item_code=item.item_code,
							item_name = item.item_name,
							description=item.description,
							# warehouse=item.warehouse,
							qty=pending_qty,
							stock_uom = item.uom,
							uom = item.uom,
							so_detail=item.sales_order_item,
							door_no = item.door_no,
							item_details = item.item_details,
							against_sales_order = item.sales_order,
							against_order_processing = item.parent,
							ordered_item = item.name
						)
					)

		return items
	
@frappe.whitelist()
def get_item_parts_to_deliver(order_processing):
	if order_processing:
		op = frappe.get_doc("Order Processing", order_processing)
		items = []
		for item in op.items:
			if item.delivered_parts < (item.qty-item.delivered_qty):
				items.append(
					dict(
						item_code = item.item_code,
						item_name = item.item_name,
						description = item.description,
						delivered_parts = item.delivered_parts,
						qty = (item.qty-item.delivered_qty) - item.delivered_parts,
						stock_uom = item.uom,
						uom = item.uom,
						door_no = item.door_no,
						ordered_item = item.name,
						against_order_processing=item.parent,
						delivery_part_item = None,
					)
				)
		return items

@frappe.whitelist()
def make_delivery_note(source_name, target_doc=None):
	from erpnext.stock.doctype.packed_item.packed_item import make_packing_list
	dn_items = frappe.flags.args.dn_items
	is_partial_delivery = frappe.flags.args.is_partial_delivery
	items = []

	if not len(dn_items.get("items")):
		frappe.throw(_("Please select the items to be delivered"))

	for item in dn_items.get("items"):
		if is_partial_delivery:      
			if not item.get("delivery_part_item"):
				frappe.throw(_("Please select partial delivery item against item at Row#{0}").format(item.get("idx")))
			else:
				items.append(
					dict(
						item_code = item["delivery_part_item"],
						qty = item["qty"],
						door_no = item["door_no"],
						ordered_item = item["ordered_item"],
						against_order_processing = item["against_order_processing"],
					)
				)
		else:
			items.append(item)

	def set_missing_values(source, target):
		source_doc = frappe.get_doc("Order Processing", source_name)
		for item in items:
			target.append("items", item)
		target.order_processing = source_name

		target.run_method("set_missing_values")
		target.run_method("set_po_nos")
		target.run_method("calculate_taxes_and_totals")

		#TODO: Handle below
		# if source.company_address:
		# 	target.update({"company_address": source.company_address})
		# else:
		# 	# set company address
		# 	target.update(get_company_address(target.company))

		# if target.company_address:
		# 	target.update(get_fetch_values("Delivery Note", "company_address", target.company_address))

		make_packing_list(target)

	doclist = get_mapped_doc(
		"Order Processing",
		source_name,
		{
			"Order Processing": {
				"doctype": "Delivery Note",
				"validation": {
					"docstatus": ["=", 1],
				},
			},
		},
		target_doc,
		set_missing_values,
		ignore_child_tables = True
	)

	doclist.set_onload("ignore_price_list", True)

	return doclist