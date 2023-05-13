# Copyright (c) 2023, Crafrt and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document

class Workorder(Document):
	pass


#TODO: stock entry when workorder is submitted

#Stock entry fields

# workorder name 
# wip_warehouse
# company
# from_bom ?
# bom_no ?
# use_multi_level_bom ?
# qty
# produced_qty
# inspection_required ??
# project
# fg_warehouse
#TODO: delete this doctype and workorder item doctype