# Copyright (c) 2023, Crafrt and contributors
# For license information, please see license.txt

import frappe
import json
from frappe.model.document import Document

class ItemDetails(Document):
	def validate(self):
		if self.hw_set_data:
			# Render Summary Table
			summary_html='''
				<div class="col-md-12">
					{%- if hw_set_data -%}
						{% set data = json.loads(hw_set_data) %}
						{% for hw_set in data %}
							{% set items = data[hw_set] %}
							<p>Hardware Set Ref: <b>{{hw_set}}</b></p>
							<table class="table table-condensed" style="width:100%; height:5px; font-size:10px">
								<thead style="display:table-header-group;">
									<tr style="height:5px;">
										<th class="text-center" style="width:5%; border:1px solid;border-color:#C6C6C6;">Item</th>
										<th class="text-center" style="width:10%; border:1px solid;border-color:#C6C6C6;">Item Name</th>
										<th class="text-center" style="border:1px solid;border-color:#C6C6C6;">Description</th>
										<th class="text-center" style="width:7%; border:1px solid;border-color:#C6C6C6;">Quantity</th>
										<th class="text-center" style="width:7%; border:1px solid;border-color:#C6C6C6;">UOM</th>
									</tr>
								</thead>
								{% for item in items %}
									<tr class="items">
										<td align="left" style="border:1px solid;border-color:#C6C6C6;">{{ item["item_code"] or ""}}</td>
										<td align="left" style="border:1px solid;border-color:#C6C6C6;">{{ item["item_name"] or ""}}</td>
										<td align="left" style="border:1px solid;border-color:#C6C6C6;">{{ item["description"] or ""}}</td>
										<td align="center" style="border:1px solid;border-color:#C6C6C6;">{{ item["qty"] or ""}}</td>
										<td align="center" style="border:1px solid;border-color:#C6C6C6;">{{ item["uom"] or ""}}</td>
									</tr>
								{% endfor %}
							</table>
						{% endfor %}
					{% endif %} 
				</div>'''

			self.db_set('hardware_set_summary', frappe.render_template(summary_html, dict(hw_set_data=self.hw_set_data)))

@frappe.whitelist()
def get_hardware_set_items(items, docname, doctype):
	# doc = frappe.get_doc(doctype, docname)
	# reset_hadware_set_list(doc)
	# print("HHAPPPENNIGGG")
	items = json.loads(items)
	hardware_set_items = []
	for item in items:
		if item.get("item_details"):
			doc = frappe.get_doc("Item Details", item["item_details"])
			hw_set_data = json.loads(doc.hw_set_data)
			if doc.hardware_set and hw_set_data.get(doc.hardware_set):
				for hw_set_item in hw_set_data[doc.hardware_set]:
					hw_set_item["qty"] = item["qty"] * hw_set_item["qty"]
					hw_set_item["is_hw_set_item"] = 1
					hw_set_item["for_item"] = item["name"]
					hardware_set_items.append(hw_set_item)
	return hardware_set_items


# def reset_hadware_set_list(doc):
# 	"Conditionally reset the table and return if it was reset or not."
# 	reset_table = False
# 	doc_before_save = doc.get_doc_before_save()

# 	if doc_before_save:
# 		# reset table if:
# 		# 1. items were deleted
# 		# 2. if bundle item replaced by another item (same no. of items but different items)
# 		# we maintain list to track recurring item rows as well
# 		items_before_save = [(item.name, item.item_code) for item in doc_before_save.get("items")]
# 		items_after_save = [(item.name, item.item_code) for item in doc.get("items")]
# 		reset_table = items_before_save != items_after_save
# 	else:
# 		# reset: if via Update Items OR
# 		# if new mapped doc with packed items set (SO -> DN)
# 		# (cannot determine action)
# 		reset_table = True
# 	print("**************************************")
# 	print(reset_table)
# 	# if reset_table:
# 	# 	doc.set("packed_items", [])
# 	# return reset_table