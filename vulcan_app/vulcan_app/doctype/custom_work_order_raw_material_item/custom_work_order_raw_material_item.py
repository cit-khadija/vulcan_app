# Copyright (c) 2023, Crafrt and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
import json
from frappe.utils import flt

from erpnext.stock.get_item_details import get_item_details, get_price_list_rate

class CustomWorkOrderRawMaterialItem(Document):
	pass

# def make_packing_list(doc):
def make_raw_material_list(doc):
	# "Make/Update packing list for Product Bundle Item."
	if doc.get("_action") and doc._action == "update_after_submit":
		return

	stale_raw_material_table = get_indexed_raw_material_table(doc)

	reset = reset_raw_material_list(doc)

	for item_row in doc.get("po_items"):
		for rm_item in get_raw_materials(item_row.bom_no):
			rm_item_row = add_raw_material_item_row(
				doc=doc,
				raw_material_item=rm_item,
				main_item_row=item_row,
				raw_material_table=stale_raw_material_table,
				reset=reset,
			)
			item_data = get__item_details(rm_item.item_code, doc.company)
			update_raw_material_item_basic_data(item_row, rm_item_row, rm_item, item_data)
			# TODO: decide what to do about warehouse
			# update_raw_material_item_stock_data(item_row, rm_item_row, rm_item, item_data, doc)
			update_raw_material_item_from_cancelled_doc(item_row, rm_item, rm_item_row, doc)

def get_indexed_raw_material_table(doc):
	"""
	Create dict from stale packed items table like:
	{(Parent Item 1, Bundle Item 1, ae4b5678): {...}, (key): {value}}

	Use: to quickly retrieve/check if row existed in table instead of looping n times
	"""
	indexed_table = {}
	for raw_material_item in doc.get("rm_items"):
		key = (raw_material_item.parent_item, raw_material_item.item_code, raw_material_item.parent_detail_docname)
		indexed_table[key] = raw_material_item

	return indexed_table

def reset_raw_material_list(doc):
	"Conditionally reset the table and return if it was reset or not."
	reset_table = False
	doc_before_save = doc.get_doc_before_save()

	if doc_before_save:
		# reset table if:
		# 1. items were deleted
		# 2. if bundle item replaced by another item (same no. of items but different items)
		# we maintain list to track recurring item rows as well
		items_before_save = [(item.name, item.item_code) for item in doc_before_save.get("po_items")]
		items_after_save = [(item.name, item.item_code) for item in doc.get("po_items")]
		reset_table = items_before_save != items_after_save
	else:
		# reset: if via Update Items OR
		# if new mapped doc with packed items set (SO -> DN)
		# (cannot determine action)
		reset_table = True

	if reset_table:
		doc.set("rm_items", [])
	return reset_table

def get_raw_materials(bom_no):
	bom = frappe.qb.DocType("BOM")
	rm_item = frappe.qb.DocType("BOM Item")

	query = (frappe.qb.from_(rm_item).select(rm_item.item_code, rm_item.qty, rm_item.uom, rm_item.description).where(rm_item.parent == bom_no).orderby(rm_item.idx))
	
	rm_list = query.run(as_dict=True)
	
	print("&&&&&&&&&&&&&&&&&&&")
	print(rm_list)
	return rm_list

def add_raw_material_item_row(doc, raw_material_item, main_item_row, raw_material_table, reset):
	"""Add and return raw material item row.
	doc: Transaction document
	raw_material_item (dict): Raw Material Item Details
	main_item_row (dict): Items table row corresponding to packed item
	raw_material_table (dict): Raw Material table before save (indexed)
	reset (bool): State if table is reset or preserved as is
	"""
	exists, rm_item_row = False, {}

	# check if row already exists in packed items table
	key = (main_item_row.item_code, raw_material_item.item_code, main_item_row.name)
	if raw_material_table.get(key):
		rm_item_row, exists = raw_material_table.get(key), True

	if not exists:
		rm_item_row = doc.append("rm_items", {})
	elif reset:  # add row if row exists but table is reset
		rm_item_row.idx, rm_item_row.name = None, None
		rm_item_row = doc.append("rm_items", rm_item_row)

	return rm_item_row

def get__item_details(item_code, company):
	item = frappe.qb.DocType("Item")
	item_default = frappe.qb.DocType("Item Default")
	query = (
		frappe.qb.from_(item)
		.left_join(item_default)
		.on((item_default.parent == item.name) & (item_default.company == company))
		.select(
			item.item_name,
			item.is_stock_item,
			item.description,
			item.stock_uom,
			item.valuation_rate,
			item_default.default_warehouse,
		)
		.where(item.name == item_code)
	)
	return query.run(as_dict=True)[0]

def update_raw_material_item_basic_data(main_item_row, rm_item_row, rm_item, item_data):
	rm_item_row.parent_item = main_item_row.item_code
	rm_item_row.parent_detail_docname = main_item_row.name
	rm_item_row.item_code = rm_item.item_code
	rm_item_row.item_name = item_data.item_name
	rm_item_row.uom = item_data.stock_uom
	rm_item_row.qty = flt(rm_item.qty) * flt(main_item_row.planned_qty)
	# TODO: Check if planned qty is the correct qty to use
	# rm_item_row.conversion_factor = main_item_row.conversion_factor

	if not rm_item_row.description:
		rm_item_row.description = rm_item.get("description")

def update_raw_material_item_stock_data(main_item_row, rm_item_row, rm_item, item_data, doc):
	# TODO batch_no, actual_batch_qty, incoming_rate
	if not rm_item_row.warehouse and not doc.amended_from:
		fetch_warehouse = item_data.is_stock_item or not item_data.default_warehouse
		rm_item_row.warehouse = (
			main_item_row.warehouse
			if (fetch_warehouse and main_item_row.warehouse)
			else item_data.default_warehouse
		)

	if not rm_item_row.target_warehouse:
		rm_item_row.target_warehouse = main_item_row.get("target_warehouse")

	bin = get_raw_material_item_bin_qty(rm_item.item_code, rm_item_row.warehouse)
	rm_item_row.actual_qty = flt(bin.get("actual_qty"))
	rm_item_row.projected_qty = flt(bin.get("projected_qty"))



def update_raw_material_item_from_cancelled_doc(main_item_row, rm_item, rm_item_row, doc):
	"Update packed item row details from cancelled doc into amended doc."
	prev_doc_rm_items_map = None
	if doc.amended_from:
		prev_doc_rm_items_map = get_cancelled_doc_raw_material_item_details(doc.rm_items)

	if prev_doc_rm_items_map and prev_doc_rm_items_map.get(
		(rm_item.item_code, main_item_row.item_code)
	):
		prev_doc_row = prev_doc_rm_items_map.get((rm_item.item_code, main_item_row.item_code))
		rm_item_row.batch_no = prev_doc_row[0].batch_no
		rm_item_row.serial_no = prev_doc_row[0].serial_no
		rm_item_row.warehouse = prev_doc_row[0].warehouse


def get_raw_material_item_bin_qty(item, warehouse):
	bin_data = frappe.db.get_values(
		"Bin",
		fieldname=["actual_qty", "projected_qty"],
		filters={"item_code": item, "warehouse": warehouse},
		as_dict=True,
	)

	return bin_data[0] if bin_data else {}


def get_cancelled_doc_raw_material_item_details(old_rm_items):
	prev_doc_rm_items_map = {}
	for items in old_rm_items:
		prev_doc_rm_items_map.setdefault((items.item_code, items.parent_item), []).append(
			items.as_dict()
		)
	return prev_doc_rm_items_map


# @frappe.whitelist()
# def get_items_from_product_bundle(row):
# 	row, items = json.loads(row), []

# 	bundled_items = get_product_bundle_items(row["item_code"])
# 	for item in bundled_items:
# 		row.update({"item_code": item.item_code, "qty": flt(row["quantity"]) * flt(item.qty)})
# 		items.append(get_item_details(row))

# 	return items
