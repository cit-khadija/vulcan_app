# Copyright (c) 2023, Crafrt and contributors
# For license information, please see license.txt

import frappe
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
