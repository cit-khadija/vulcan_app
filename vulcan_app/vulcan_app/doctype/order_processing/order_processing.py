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
				where so_detail = "{item.so_detail}" and docstatus = 1
				and against_sales_order = "{item.sales_order}" """
			)

			delivered_via_si = frappe.db.sql(
				f"""select sum(si_item.qty)
				from `tabSales Invoice Item` si_item, `tabSales Invoice` si
				where si_item.parent = si.name and si.update_stock = 1
				and si_item.so_detail = "{item.so_detail}" and si.docstatus = 1
				and si_item.sales_order = "{item.sales_order}" """,
			)

			total_delivered_qty = (flt(delivered_via_dn[0][0]) if delivered_via_dn else 0) + (
			flt(delivered_via_si[0][0]) if delivered_via_si else 0
			)

			#TODO: set up automatic update for delivered qty
			#TODO: set up deliver parts
			if item.delivered_qty != total_delivered_qty:
				item.db_set("delivered_qty", total_delivered_qty)

			if item.delivered_qty < item.manufactured_qty:
				pending_qty = item.manufactured_qty - item.delivered_qty
				
				if pending_qty:
					items.append(
						dict(
							name = item.name,
							item_code=item.item_code,
							description=item.description,
							# warehouse=item.warehouse,
							pending_qty=pending_qty,
							sales_order_item=item.name,
							door_no = item.door_no,
							item_details = item.item_details,
							sales_order = item.sales_order,
							order_processing = item.parent
						)
					)
				


# @frappe.whitelist()
# def get_work_order_items(sales_order, for_raw_material_request=0):
# 	#TODO Redefine this function
# 	"""Returns items with BOM that already do not have a linked work order"""
# 	if sales_order:
# 		so = frappe.get_doc("Sales Order", sales_order)

# 		wo = qb.DocType("Work Order")

# 		items = []
# 		item_codes = [i.item_code for i in so.items]
# 		product_bundle_parents = [
# 			pb.new_item_code
# 			for pb in frappe.get_all(
# 				"Product Bundle", {"new_item_code": ["in", item_codes]}, ["new_item_code"]
# 			)
# 		]

# 		for table in [so.items, so.packed_items]:
# 			for i in table:
# 				bom = get_default_bom(i.item_code)
# 				stock_qty = i.qty if i.doctype == "Packed Item" else i.stock_qty

# 				if not for_raw_material_request:
# 					total_work_order_qty = flt(
# 						qb.from_(wo)
# 						.select(Sum(wo.qty))
# 						.where(
# 							(wo.production_item == i.item_code)
# 							& (wo.sales_order == so.name)
# 							& (wo.sales_order_item == i.name)
# 							& (wo.docstatus.lt(2))
# 						)
# 						.run()[0][0]
# 					)
# 					pending_qty = stock_qty - total_work_order_qty
# 				else:
# 					pending_qty = stock_qty

# 				if pending_qty and i.item_code not in product_bundle_parents:
# 					items.append(
# 						dict(
# 							name=i.name,
# 							item_code=i.item_code,
# 							description=i.description,
# 							bom=bom or "",
# 							warehouse=i.warehouse,
# 							pending_qty=pending_qty,
# 							required_qty=pending_qty if for_raw_material_request else 0,
# 							sales_order_item=i.name,
# 							door_no = i.door_no,
# 							item_details = i.item_details
# 						)
# 					)

# 		return items
	

# @frappe.whitelist()
# def make_workorders(items, sales_order, company, project=None):
# 	"""Make Work Orders against the given Sales Order for the given `items`"""
# 	items = json.loads(items).get("items")
# 	out = []

# 	for i in items:
# 		if not i.get("bom"):
# 			frappe.throw(_("Please select BOM against item {0}").format(i.get("item_code")))
# 		if not i.get("pending_qty"):
# 			frappe.throw(_("Please select Qty against item {0}").format(i.get("item_code")))
		

# 		work_order = frappe.get_doc(
# 			dict(
# 				doctype="Workorder",
# 				production_item=i["item_code"],
# 				bom_no=i.get("bom"),
# 				qty=i["pending_qty"],
# 				company=company,
# 				sales_order=sales_order,
# 				sales_order_item=i["sales_order_item"],
# 				project=project,
# 				fg_warehouse=i["warehouse"],
# 				description=i["description"],
# 				required_items = all_raw_materials
# 			)
# 		).insert()
# 		work_order.flags.ignore_mandatory = True
# 		work_order.save()
# 		out.append(work_order)

# 	return [p.name for p in out]