// // Copyright (c) 2023, Crafrt and contributors
// // For license information, please see license.txt

// Copyright (c) 2017, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt
//This document is based on Production Plan doctype from ERPnext

//TODO: combine_items

frappe.ui.form.on('Custom Work Order', {

	before_save(frm) {
		// preserve temporary names on production plan item to re-link sub-assembly items
		frm.doc.po_items.forEach(item => {
			item.temporary_name = item.name;
		});
	},
	setup(frm) {
		frm.fields_dict['po_items'].grid.get_field('warehouse').get_query = function(doc) {
			return {
				filters: {
					company: doc.company
				}
			}
		}

		frm.fields_dict['rm_items'].grid.get_field('warehouse').get_query = function(doc) {
			return {
				filters: {
					company: doc.company,
					is_group: 0
				}
			}
		}

		frm.set_query('default_source_warehouse', function(doc) {
			return {
				filters: {
					company: doc.company,
					is_group: 0
				}
			}
		});

		frm.set_query('wip_warehouse', function(doc) {
			return {
				filters: {
					company: doc.company,
					is_group: 0
				}
			}
		});

		frm.fields_dict['po_items'].grid.get_field('item_code').get_query = function(doc) {
			return {
				query: "erpnext.controllers.queries.item_query",
				filters:{
					'is_stock_item': 1,
				}
			}
		}

		frm.fields_dict['po_items'].grid.get_field('bom_no').get_query = function(doc, cdt, cdn) {
			var d = locals[cdt][cdn];
			if (d.item_code) {
				return {
					query: "erpnext.controllers.queries.bom",
					filters:{'item': cstr(d.item_code), 'docstatus': 1}
				}
			} else frappe.msgprint(__("Please enter Item first"));
		}

	},

	refresh(frm) {
		// TODO:find out how to make this work
		frm.set_indicator_formatter('item_code', function(doc) {
			if (!doc.warehouse) {
				return 'blue';
			} else {
				return (doc.qty>40) ? 'green' : 'orange';
			}
		});

		frm.set_df_property('rm_items', 'cannot_add_rows', true);
		frm.set_df_property('rm_items', 'cannot_delete_rows', true);

		if (frm.doc.docstatus === 1) {
			if (frm.doc.status !== "Completed") {
				if  (frm.doc.status === "Closed") {
					frm.add_custom_button(__("Re-open"), function() {
						frm.events.close_open_custom_work_order(frm, false);
					}, __("Status"));
				} else {
					frm.add_custom_button(__("Close"), function() {
						frm.events.close_open_custom_work_order(frm, true);
					}, __("Status"));
				}

				// TODO:conditions to check if transfer and manufacture is required should be defined
				if (frm.doc.total_planned_qty != frm.doc.total_produced_qty){
					// *************************************************************************************
					// START BUTTON
					if(!frm.doc.skip_transfer){
					var start_btn = frm.add_custom_button(__('Start'), function() { make_stock_entry(frm, "Material Transfer for Manufacture") });
					start_btn.addClass('btn-primary');
					}
					// *************************************************************************************
					// FINISH BUTTON

					// TODO: Not working properly
					var finish_btn = frm.add_custom_button(__('Finish'), function() { make_stock_entry(frm, "Bulk Manufacture") });
					finish_btn.addClass('btn-primary');
				}

			}
		}
		//CHECK: what is this trigger for?
		frm.trigger("material_requirement");
	},

	get_order_processings(frm) {
		frappe.call({
			method: "get_open_order_processings",
			doc: frm.doc,
			callback: function(r){
				refresh_field("order_processings")
			}
		})
	},

	get_items(frm) {
		frappe.call({
			method: "get_items",
			freeze: true,
			doc: frm.doc,
			callback: function () {
				refresh_field('po_items');
			}
		});
	},

	transfer_materials: function(frm){
		frappe.model.open_mapped_doc({
			method:"vulcan_app.vulcan_app.doctype.custom_work_order.custom_work_order.make_material_transfer_stock_entry",
			frm: frm
		})
	},

	make_manufacturing_stock_entry(frm){
		frappe.model.open_mapped_doc({
			method:"vulcan_app.vulcan_app.doctype.custom_work_order.custom_work_order.make_manufacturing_stock_entry",
			frm: frm
		})
	},

	close_open_custom_work_order(frm, close=false) {
		frappe.call({
			method: "set_status",
			freeze: true,
			doc: frm.doc,
			args: {close : close},
			callback: function() {
				frm.reload_doc();
			}
		});
	},

	default_source_warehouse(frm){
		frappe.call({
			method:"set_from_warehouse",
			freeze:true,
			doc:frm.doc,
			callback: function(){
				refresh_field('rm_items')
			}
		})
	},
});

frappe.ui.form.on("Custom Work Order Item", {
	item_code(frm, cdt, cdn) {
		const row = locals[cdt][cdn];
		if (row.item_code) {
			frappe.call({
				method: "erpnext.manufacturing.doctype.custom_work_order.custom_work_order.get_item_data",
				args: {
					item_code: row.item_code
				},
				callback: function(r) {
					for (let key in r.message) {
						frappe.model.set_value(cdt, cdn, key, r.message[key]);
					}
				}
			});
		}
	}
});

frappe.tour['Custom Work Order'] = [
	{
		fieldname: "get_order_processings",
		title: "Get Orders",
		description: __("Click on Get Order Processings to fetch sales orders based on the above filters.")
	},
	{
		fieldname: "get_items",
		title: "Get Finished Goods for Manufacture",
		description: __("Click on 'Get Finished Goods for Manufacture' to fetch the items from the above Order Processings. Items only for which a BOM is present will be fetched.")
	},
	{
		fieldname: "po_items",
		title: "Finished Goods",
		description: __("TODO: check if anything needs to be mentioned here")
	},
];

var make_stock_entry = function(frm, purpose){
	if(purpose=="Material Transfer for Manufacture"){
		validate_warehouses(frm)
		if(!frm.doc.wip_warehouse && !frm.doc.skip_transfer){
			frappe.throw("Please select the Work In Progress Warehouse")
		}
		frm.trigger("transfer_materials")
	}

	if(purpose=="Bulk Manufacture"){
		validate_warehouses(frm)
		if(!frm.doc.wip_warehouse && !frm.doc.skip_transfer){
			frappe.throw("Please select the Work In Progress Warehouse")
		}
		validate_quantity(frm)
		frm.trigger("make_manufacturing_stock_entry")
	}
}

var validate_warehouses = function(frm){
	$.each(frm.doc.po_items, (k,item)=>{
		if(!item.warehouse){
			var message = "Please select FG warehouse for Finished Good item at Row #"+item.idx
			frappe.throw(message)
		}
	})
	$.each(frm.doc.rm_items, (k,item)=>{
		if(!item.warehouse && !frm.doc.default_source_warehouse){
			var message = "Please select warehouse for RM item at Row #"+item.idx+" or set default source warehouse"
			frappe.throw(message)
		}
	})
}

var validate_quantity = function(frm){
	frappe.call({
		method:"get_stock_and_rate",
		doc:frm.doc,
		args: {validate_for_stock_entry: true},
		freeze:true,
		callback: function(r){
			console.log(r)
		}
	})
}

var check_for_manufacturing_entry = function(frm){
	frappe.call({
		method:"check_for_manufacturing_entry",
		doc:frm.doc,
		callback: function(r){
			return r.message
		}
	})
}

//TODO: remove cwo stock entry item table instead put a consolidated items table for summary