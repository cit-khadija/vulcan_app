# Copyright (c) 2023, Crafrt and contributors
# For license information, please see license.txt

# Copyright (c) 2017, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt
import json

import frappe
from frappe import _, msgprint
from frappe.model.document import Document
from frappe.utils import (
	comma_and,
	flt,
	get_link_to_form,
	now_datetime,
	format_time,
	formatdate
)
from pypika.terms import ExistsCriterion
from erpnext.stock.stock_balance import get_planned_qty, update_bin_qty
from erpnext.stock.stock_ledger import is_negative_stock_allowed
from erpnext.stock.stock_ledger import NegativeStockError, get_previous_sle, get_valuation_rate
from erpnext.manufacturing.doctype.bom.bom import validate_bom_no
from erpnext.manufacturing.doctype.work_order.work_order import get_item_details
from erpnext.utilities.transaction_base import validate_uom_is_integer
from frappe.model.mapper import get_mapped_doc
from erpnext.stock.utils import get_bin, get_latest_stock_qty, validate_warehouse_company

class StockOverProductionError(frappe.ValidationError):
	pass


class CustomWorkOrder(Document):
	def validate(self):
		self.set_pending_qty_in_row_without_reference()
		self.calculate_total_planned_qty()
		validate_uom_is_integer(self, "stock_uom", "planned_qty")
		from vulcan_app.vulcan_app.doctype.custom_work_order_raw_material_item.custom_work_order_raw_material_item import make_raw_material_list
		make_raw_material_list(self)
		self.set_available_qty()
		self.set_status()

	def on_submit(self):
		self.update_work_order_qty_in_op()

	def on_cancel(self):
		self.update_work_order_qty_in_op()

	#TODO: Handle work order qty so that only order processing without work order already will be fetched
	def update_work_order_qty_in_op(self):
		for item in self.po_items:
			order_processing = item.order_processing
			ordered_item = item.ordered_item
			qty = frappe.db.sql(
				f""" select sum(planned_qty) from `tabCustom Work Order Item` 
				where order_processing = "{order_processing}" and docstatus = 1 and ordered_item = "{ordered_item}"
				""", as_list=1,
			)

			work_order_qty = qty[0][0] if qty and qty[0][0] else 0
			frappe.db.set_value("Ordered Item",	ordered_item, "work_order_qty", flt(work_order_qty, 2))

	#TODO: thiss
	def set_available_qty(self):
		for d in self.get("rm_items"):
			if d.warehouse:
				d.available_qty_at_source_warehouse = get_latest_stock_qty(d.item_code, d.warehouse)

			if self.wip_warehouse:
				d.available_qty_at_wip_warehouse = get_latest_stock_qty(d.item_code, self.wip_warehouse)

	def set_pending_qty_in_row_without_reference(self):
		"Set Pending Qty in independent rows (not from SO or MR)."
		if self.docstatus > 0:  # set only to initialise value before submit
			return

		for item in self.po_items:
			if not item.get("sales_order") or not item.get("material_request"):
				item.pending_qty = item.planned_qty

	def calculate_total_planned_qty(self):
		self.total_planned_qty = 0
		for d in self.po_items:
			self.total_planned_qty += flt(d.planned_qty)

	def validate_data(self):
		for d in self.get("po_items"):
			if not d.bom_no:
				frappe.throw(_("Please select BOM for Item in Row {0}").format(d.idx))
			else:
				validate_bom_no(d.item_code, d.bom_no)

			if not flt(d.planned_qty):
				frappe.throw(_("Please enter Planned Qty for Item {0} at row {1}").format(d.item_code, d.idx))

	#TODO: set status not working
	@frappe.whitelist()
	def set_status(self, close=None):
		self.status = {0: "Draft", 1: "Submitted", 2: "Cancelled"}.get(self.docstatus)

		if close:
			self.db_set("status", "Closed")
			return
		
		print("*************set_status*****************")
		print(self.total_produced_qty)

		if self.total_produced_qty > 0:
			self.status = "In Process"
			if self.all_items_completed():
				self.status = "Completed"

		# if self.status != "Completed":
		# 	self.update_ordered_status()
		# 	self.update_requested_status()

		if close is not None:
			frappe.db.set_value("Custom Work Order",self.name,"status", self.status)

	def all_items_completed(self):
		all_items_produced = all(
			flt(d.planned_qty) - flt(d.produced_qty) < 0.000001 for d in self.po_items
		)
		if not all_items_produced:
			return False
		return True

	@frappe.whitelist()
	def set_from_warehouse(self):
		if self.default_source_warehouse and self.rm_items:
			for item in self.rm_items:
				if not item.warehouse:
					item.warehouse = self.default_source_warehouse

	@frappe.whitelist()
	def get_stock_and_rate(self, validate_for_stock_entry = False):
		"""
		Updates rate and availability of all the items.
		Called from Update Rate and Availability button.
		"""
		# self.set_work_order_details()
		# self.set_transfer_qty()
		self.set_actual_qty(validate_for_stock_entry)
		# self.calculate_rate_and_amount()

	def set_actual_qty(self, validate_for_stock_entry = False):
		for d in self.get("rm_items"):
			allow_negative_stock = is_negative_stock_allowed(item_code=d.item_code)
			previous_sle = get_previous_sle(
				{
					"item_code": d.item_code,
					"warehouse": d.warehouse,
					"posting_date": self.posting_date,
					"posting_time": self.posting_time,
				}
			)

			# get actual stock at source warehouse
			d.actual_qty = previous_sle.get("qty_after_transaction") or 0
			

			# validate qty during submit
			if (
				d.docstatus == 1
				and validate_for_stock_entry
				and d.warehouse
				and not allow_negative_stock
				and flt(d.actual_qty, d.precision("actual_qty"))
				< flt(d.qty, d.precision("actual_qty"))
			):
				frappe.throw(
					_(
						"Row {0}: Quantity not available for {4} in warehouse {1} at posting time of the entry ({2} {3})"
					).format(
						d.idx,
						frappe.bold(d.warehouse),
						formatdate(self.posting_date),
						format_time(self.posting_time),
						frappe.bold(d.item_code),
					)
					+ "<br><br>"
					+ _("Available quantity is {0}, you need {1}").format(
						frappe.bold(flt(d.actual_qty, d.precision("actual_qty"))), frappe.bold(d.qty)
					),
					NegativeStockError,
					title=_("Insufficient Stock"),
				)

	###############################################################################################
	#ORDER PROCESSING

	@frappe.whitelist()
	def get_open_order_processings(self):
		"""Pull order processings  which are pending to deliver based on criteria selected"""
		open_op = get_order_processings(self)

		if open_op:
			self.add_op_in_table(open_op)
		else:
			frappe.msgprint(_("Order Processings are not available for production"))

	def add_op_in_table(self, open_op):
		"""Add order processings in the table"""
		self.set("order_processings", [])

		for data in open_op:
			self.append(
				"order_processings",
				{
					"order_processing": data.name,
					"sales_order": data.sales_order,
					"sales_order_date": data.transaction_date,
					"customer": data.customer,
				},
			)

	@frappe.whitelist()
	def get_items(self):
		self.set("po_items", [])
		self.get_op_items()

	def get_op_items(self):
		# Check for empty table or empty rows
		if not self.get("order_processings") or not self.get_docfield_value_list_from_table("order_processing", "order_processings"):
			frappe.throw(_("Please fill the Order Processings table"), title=_("Order Processings Required"))

		op_list = self.get_docfield_value_list_from_table("order_processing", "order_processings")

		bom = frappe.qb.DocType("BOM")
		op_item = frappe.qb.DocType("Ordered Item")

		items_subquery = frappe.qb.from_(bom).select(bom.name).where(bom.is_active == 1)
		items_query = (
			frappe.qb.from_(op_item)
			.select(
				op_item.parent,
				op_item.item_code,
				op_item.warehouse,
				(
					(op_item.qty - op_item.work_order_qty - op_item.delivered_qty) * op_item.conversion_factor
				).as_("pending_qty"),
				op_item.description,
				op_item.name,
				op_item.item_details,
				op_item.sales_order,
				op_item.sales_order_item
			)
			.distinct()
			.where(
				(op_item.parent.isin(op_list))
				& (op_item.docstatus == 1)
				& (op_item.qty > op_item.work_order_qty)
			)
		)

		if self.item_code and frappe.db.exists("Item", self.item_code):
			items_query = items_query.where(op_item.item_code == self.item_code)
			items_subquery = items_subquery.where(
				self.get_bom_item_condition() or bom.item == op_item.item_code
			)

		items_query = items_query.where(ExistsCriterion(items_subquery))

		items = items_query.run(as_dict=True)

		pi = frappe.qb.DocType("Packed Item")

		packed_items_query = (
			frappe.qb.from_(op_item)
			.from_(pi)
			.select(
				pi.parent,
				pi.item_code,
				pi.warehouse.as_("warehouse"),
				(((op_item.qty - op_item.work_order_qty) * pi.qty) / op_item.qty).as_("pending_qty"),
				pi.parent_item,
				pi.description,
				op_item.name,
			)
			.distinct()
			.where(
				(op_item.parent == pi.parent)
				& (op_item.docstatus == 1)
				& (pi.parent_item == op_item.item_code)
				& (op_item.parent.isin(op_list))
				& (op_item.qty > op_item.work_order_qty)
				& (
					ExistsCriterion(
						frappe.qb.from_(bom)
						.select(bom.name)
						.where((bom.item == pi.item_code) & (bom.is_active == 1))
					)
				)
			)
		)

		if self.item_code:
			packed_items_query = packed_items_query.where(op_item.item_code == self.item_code)

		packed_items = packed_items_query.run(as_dict=True)

		self.add_items(items + packed_items)
		self.calculate_total_planned_qty()

	###############################################################################################

	@frappe.whitelist()
	def check_for_manufacturing_entry(self):
		se_exists = frappe.db.exists("Stock Entry",  {'custom_work_order':self.name, 'stock_entry_type':'Bulk Manufacture', 'docstatus':['<',2]})
		return se_exists
	

	###############################################################################################

	def get_docfield_value_list_from_table(self, field, table):
		#original function name get_so_mr_list
		"""Returns a list of Docfield values from the respective tables"""
		docfield_value_list = [d.get(field) for d in self.get(table) if d.get(field)]
		return docfield_value_list

	def get_bom_item_condition(self):
		"""Check if Item or if its Template has a BOM."""
		bom_item_condition = None
		has_bom = frappe.db.exists({"doctype": "BOM", "item": self.item_code, "docstatus": 1})

		if not has_bom:
			bom = frappe.qb.DocType("BOM")
			template_item = frappe.db.get_value("Item", self.item_code, ["variant_of"])
			bom_item_condition = bom.item == template_item or None

		return bom_item_condition

	def add_items(self, items):
		for data in items:
			if not data.pending_qty:
				continue

			item_details = get_item_details(data.item_code)
			pi = self.append(
				"po_items",
				{
					"warehouse": data.warehouse,
					"item_code": data.item_code,
					"description": data.description or item_details.description,
					"stock_uom": item_details and item_details.stock_uom or "",
					"bom_no": item_details and item_details.bom_no or "",
					"planned_qty": data.pending_qty,
					"pending_qty": data.pending_qty,
					"planned_start_date": now_datetime(),
					"product_bundle_item": data.parent_item,
				},
			)
			pi._set_defaults()
			pi.order_processing = data.parent
			pi.ordered_item = data.name
			pi.sales_order = data.sales_order
			pi.sales_order_item = data.sales_order_item
			pi.description = data.description
			pi.item_details = data.item_details

###############################################################################################


	#TODO: Check how to update qty
	#TODO: set status
	def update_work_order_qty(self):
		finished_good_qty = get_finished_good_qty(self.name)
		# print(finished_good_qty)
		for item in self.po_items:
			produced_qty = 0
			if finished_good_qty.get(item.name):
				produced_qty = finished_good_qty[item.name]
			# frappe.db.set_value("Custom Work Order Item", item.name ,"produced_qty", produced_qty)
			item.db_set("produced_qty", produced_qty)
			
		self.calculate_total_produced_qty()

		for item in self.po_items:
			update_produced_qty_in_op_item(item.order_processing, item.ordered_item)
			update_produced_qty_in_so_item(item.sales_order, item.sales_order_item)

		# self.set_status()
		print("**********************************reloading**************************")
		self.reload()


	def update_planned_qty(self):
		update_bin_qty(
			self.production_item,
			self.fg_warehouse,
			{"planned_qty": get_planned_qty(self.production_item, self.fg_warehouse)},
		)

		if self.material_request:
			mr_obj = frappe.get_doc("Material Request", self.material_request)
			mr_obj.update_requested_qty([self.material_request_item])

	def calculate_total_produced_qty(self):
		# print("&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&")
		self.total_produced_qty = 0
		# print(self.total_produced_qty)
		for d in self.po_items:
			# print("************************")
			# print(d.produced_qty)
			self.total_produced_qty += flt(d.produced_qty)
		# print(self.total_produced_qty)
		frappe.db.set_value("Custom Work Order",self.name,"total_produced_qty", self.total_produced_qty, update_modified=False)
	
###############################################################################################
	def show_list_created_message(self, doctype, doc_list=None):
		if not doc_list:
			return

		frappe.flags.mute_messages = False
		if doc_list:
			doc_list = [get_link_to_form(doctype, p) for p in doc_list]
			msgprint(_("{0} created").format(comma_and(doc_list)))
###############################################################################################

def get_uom_conversion_factor(item_code, uom):
	return frappe.db.get_value(
		"UOM Conversion Detail", {"parent": item_code, "uom": uom}, "conversion_factor"
	)

@frappe.whitelist()
def get_item_data(item_code):
	item_details = get_item_details(item_code)

	return {
		"bom_no": item_details.get("bom_no"),
		"stock_uom": item_details.get("stock_uom")
		# 		"description": item_details.get("description")
	}

def set_default_warehouses(row, default_warehouses):
	for field in ["wip_warehouse", "fg_warehouse"]:
		if not row.get(field):
			row[field] = default_warehouses.get(field)


###############################################################################################
#ORDER PROCESSING FUNCTIONS

def get_order_processings(self):
	bom = frappe.qb.DocType("BOM")
	pi = frappe.qb.DocType("Packed Item")
	op = frappe.qb.DocType("Order Processing")
	op_item = frappe.qb.DocType("Ordered Item")

	open_op_subquery1 = frappe.qb.from_(bom).select(bom.name).where(bom.is_active == 1)

	open_op_subquery2 = (
		frappe.qb.from_(pi)
		.select(pi.name)
		.where(
			(pi.parent == op.name)
			& (pi.parent_item == op_item.item_code)
			& (
				ExistsCriterion(
					frappe.qb.from_(bom).select(bom.name).where((bom.item == pi.item_code) & (bom.is_active == 1))
				)
			)
		)
	)

	#TODO: check the commented out parts in following query
	open_op_query = (
		frappe.qb.from_(op)
		.from_(op_item)
		.select(op.name, op.sales_order, op.transaction_date, op.customer)
		.distinct()
		.where(
			(op_item.parent == op.name)
			& (op.docstatus == 1)
			# & (op.status.notin(["Stopped", "Closed"]))
			& (op.company == self.company)
			& (op_item.qty > op_item.work_order_qty)
		)
	)
	# TODO: Check filters...why is it wrong logic even in actual version?
	date_field_mapper = {
		"from_date": self.from_date <= op.transaction_date,
		"to_date": self.to_date >= op.transaction_date,
		"from_delivery_date": self.from_delivery_date <= op_item.delivery_date,
		"to_delivery_date": self.to_delivery_date >= op_item.delivery_date,
	}

	for field, value in date_field_mapper.items():
		if self.get(field):
			open_op_query = open_op_query.where(value)

	for field in ("customer", "project", "sales_order_status"):
		if self.get(field):
			op_field = "status" if field == "sales_order_status" else field
			open_op_query = open_op_query.where(op[op_field] == self.get(field))

	if self.item_code and frappe.db.exists("Item", self.item_code):
		open_op_query = open_op_query.where(op_item.item_code == self.item_code)
		open_op_subquery1 = open_op_subquery1.where(
			self.get_bom_item_condition() or bom.item == op_item.item_code
		)

	open_op_query = open_op_query.where(
		(ExistsCriterion(open_op_subquery1) | ExistsCriterion(open_op_subquery2))
	)
	
	if self.sales_order:
		open_op_query = open_op_query.where(op.sales_order == self.sales_order)

	open_op = open_op_query.run(as_dict=True)

	return open_op

###############################################################################################



#TODO: DISPLAY consolidated items
#TODO: check for non-stock item functionality
# TODO: actual_qty indicator

###############################################################################################
# STOCK ENTRY FUNCTIONS

def get_stock_entry_item_list(doc, purpose = "Bulk Manufacture"):
		se_items = []
		if doc.rm_items:
			for item in doc.rm_items:
				se_item = {
					"item_code" : item.item_code,
					"qty": item.qty,
					"conversion_factor": item.conversion_factor or 1.0,
					"transfer_qty": flt(item.qty) * (flt(item.conversion_factor) or 1.0),
					"uom": item.uom,
					"stock_uom":item.uom,
					"s_warehouse": item.warehouse,
					"cwo_item":item.name
				}
				if purpose=="Material Transfer for Manufacture":
					se_item["t_warehouse"] = doc.wip_warehouse
				elif not doc.skip_transfer and purpose == "Bulk Manufacture":
					se_item["s_warehouse"] = doc.wip_warehouse
				se_items.append(se_item)

		if purpose == "Bulk Manufacture" and doc.po_items:
			for item in doc.po_items:
				se_item = {
					"item_code" : item.item_code,
					"qty": item.planned_qty,
					"conversion_factor": 1.0,
					"transfer_qty": flt(item.planned_qty),
					"uom": item.stock_uom,
					"stock_uom":item.stock_uom,
					"t_warehouse":item.warehouse,
					"is_finished_item": 1,
					"allow_zero_valuation_rate":1,
					"set_basic_rate_manually":1,
					"cwo_item":item.name
				}
				se_items.append(se_item)
		return se_items

@frappe.whitelist()
def make_material_transfer_stock_entry(source_name, target_doc=None):
	def set_missing_values(source, target):
		source_doc = frappe.get_doc("Custom Work Order", source_name)
		se_items = get_stock_entry_item_list(source_doc, "Material Transfer for Manufacture")
		for se_item in se_items:
			target.append("items", se_item)
		target.stock_entry_type = "Material Transfer for Manufacture"
		target.purpose = "Material Transfer for Manufacture"
		target.custom_work_order = source_name
		target.set_transfer_qty()
		target.set_actual_qty()
		target.calculate_rate_and_amount(raise_error_if_no_rate=False)
		target.set_job_card_data()

	doclist = get_mapped_doc(
		"Custom Work Order",
		source_name,
		{
			"Custom Work Order": {
				"doctype": "Stock Entry",
				"validation": {
					"docstatus": ["=", 1],
				},
			}
		},
		target_doc,
		set_missing_values,
		ignore_child_tables = True
	)

	return doclist

@frappe.whitelist()
def make_manufacturing_stock_entry(source_name, target_doc=None):
	def set_missing_values(source, target):
		source_doc = frappe.get_doc("Custom Work Order", source_name)
		se_items = get_stock_entry_item_list(source_doc, "Bulk Manufacture")
		for se_item in se_items:
			target.append("items", se_item)
		target.stock_entry_type = "Bulk Manufacture"
		target.purpose = "Repack"
		target.custom_work_order = source_name
		target.set_transfer_qty()
		target.set_actual_qty()
		target.calculate_rate_and_amount(raise_error_if_no_rate=False)
		target.set_job_card_data()

	doclist = get_mapped_doc(
		"Custom Work Order",
		source_name,
		{
			"Custom Work Order": {
				"doctype": "Stock Entry",
				"validation": {
					"docstatus": ["=", 1],
				},
			},
		},
		target_doc,
		set_missing_values,
		ignore_child_tables = True
	)

	return doclist

def get_finished_good_qty(docname):
		se = frappe.qb.DocType("Stock Entry")
		sed = frappe.qb.DocType("Stock Entry Detail")

		fg_qty_query = (
			frappe.qb.from_(se)
			.from_(sed)
			.select(sed.item_code, sed.qty, sed.cwo_item)
			.distinct()
			.where(
				(sed.parent==se.name) 
				& (se.docstatus == 1) 
				& (se.custom_work_order == docname)
				& (sed.is_finished_item == 1)
				)
			)

		query_result = fg_qty_query.run(as_dict=True)

		fg_qty_dict = {}

		for item in query_result:
			fg_qty_dict[item.cwo_item] = item.qty

		return fg_qty_dict

def update_produced_qty_in_so_item(sales_order, sales_order_item):
	# for multiple work orders against same sales order item
	linked_wo_with_so_item = frappe.db.get_all(
		"Custom Work Order Item",
		["produced_qty"],
		{"sales_order_item": sales_order_item, "sales_order": sales_order, "docstatus": 1},
	)

	total_produced_qty = 0
	for wo in linked_wo_with_so_item:
		total_produced_qty += flt(wo.get("produced_qty"))

	if not total_produced_qty and frappe.flags.in_patch:
		return

	frappe.db.set_value("Sales Order Item", sales_order_item, "produced_qty", total_produced_qty)

def update_produced_qty_in_op_item(order_processing, ordered_item):
	# for multiple work orders against same sales order item
	linked_wo_with_so_item = frappe.db.get_all(
		"Custom Work Order Item",
		["produced_qty"],
		{"ordered_item": ordered_item, "order_processing": order_processing, "docstatus": 1},
	)

	total_produced_qty = 0
	for wo in linked_wo_with_so_item:
		total_produced_qty += flt(wo.get("produced_qty"))

	if not total_produced_qty and frappe.flags.in_patch:
		return

	frappe.db.set_value("Ordered Item", ordered_item, "manufactured_qty", total_produced_qty)

