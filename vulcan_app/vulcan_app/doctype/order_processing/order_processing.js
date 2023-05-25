// Copyright (c) 2023, Crafrt and contributors
// For license information, please see license.txt

frappe.ui.form.on('Order Processing', {
	setup: function(frm){
		frm.custom_make_buttons = {
			// 'Workorder': 'Workorder',
			'Delivery Note': 'Delivery Note'
		}
	},
	refresh: function(frm){
		if(frm.doc.docstatus==1){

			//TODO Add status to close and reopen

			// delivery note
			//TODO Check if below condition is required
			// if(flt(doc.per_delivered, 6) < 100 && (order_is_a_sale || order_is_a_custom_sale) && allow_delivery) {
				frm.add_custom_button(__('Delivery Note'), () => make_delivery_note(), __('Create'));
				// frm.add_custom_button(__('Work Order'), () => make_workorder(frm), __('Create'));
			// }
		}
	},
	validate: function(frm){
		// op1 = frappe.db.exists("Order Processing", {"sales_order":frm.doc.sales_order, "docstatus":1})
		// op2 = frappe.db.exists("Order Processing", {"sales_order":frm.doc.sales_order, "docstatus":0})
		// if(op1 || op2){
		// 	frappe.msgprint(
		// 	_("Order Processing Document {0} already created")
		// 	.format("<a href='/app/order-processing/{0}'>{0}</a>")
		// 	.format(op)
		// 	)
		// }
	}
});

//TODO HIGH: on_save validation whether an OP already exists on the same sales order with docstatus 1
//TODO: add sales order items when selecting sales order
//TODO LOW: check if adding controller like in sales order is required

// var make_workorder = function(frm){
// 	// console.log("Make Workorder")
// 	frm.call({
// 		method: "vulcan_app.vulcan_app.doctype.order_processing.order_processing.get_work_order_items",
// 		args: {
// 			sales_order: frm.doc.sales_order
// 		},
// 		freeze:true,
// 		callback: function(r){
// 			if(!r.message) {
// 				frappe.msgprint({
// 					title: __('Work Order not created'),
// 					message: __('No Items with Bill of Materials to Manufacture'),
// 					indicator: 'orange'
// 				});
// 				return;
// 			}
// 			else {
// 				const fields = [{
// 					label: 'Items',
// 					fieldtype: 'Table',
// 					fieldname: 'items',
// 					description: __('Select BOM and Qty for Production'),
// 					fields: [{
// 						fieldtype: 'Read Only',
// 						fieldname: 'item_code',
// 						label: __('Item Code'),
// 						in_list_view: 1
// 					}, {
// 						fieldtype: 'Read Only',
// 						fieldname: 'door_no',
// 						label:__('Door No'),
// 						in_list_view: 1
// 					}, {
// 						fieldtype: 'Link',
// 						fieldname: 'bom',
// 						options: 'BOM',
// 						reqd: 1,
// 						label: __('Select BOM'),
// 						in_list_view: 1,
// 						get_query: function (doc) {
// 							return { filters: { item: doc.item_code } };
// 						}
// 					}, {
// 						fieldtype: 'Float',
// 						fieldname: 'pending_qty',
// 						reqd: 1,
// 						label: __('Qty'),
// 						in_list_view: 1
// 					}, {
// 						fieldtype: 'Data',
// 						fieldname: 'sales_order_item',
// 						reqd: 1,
// 						label: __('Sales Order Item'),
// 						hidden: 1
// 					}],
// 					data: r.message,
// 					get_data: () => {
// 						return r.message
// 					}
// 				}]

// 				var d = new frappe.ui.Dialog({
// 					title: __('Select Items to Manufacture'),
// 					fields: fields,
// 					primary_action: function() {
// 						var data = {items: d.fields_dict.items.grid.get_selected_children()};
// 						// console.log(data)
// 						frm.call({
// 							method: 'vulcan_app.vulcan_app.doctype.order_processing.order_processing.make_workorders',
// 							args: {
// 								items: data,
// 								company: frm.doc.company,
// 								sales_order: frm.doc.sales_order,
// 								// project: frm.project TODO:add project field too
// 							},
// 							freeze: true,
// 							callback: function(r) {
// 								if(r.message) {
// 									frappe.msgprint({
// 										message: __('Work Orders Created: {0}', [r.message.map(function(d) {
// 												return repl('<a href="/app/workorder/%(name)s">%(name)s</a>', {name:d})
// 											}).join(', ')]),
// 										indicator: 'green'
// 									})
// 								}
// 								d.hide();
// 							}
// 						});
// 					},
// 					primary_action_label: __('Create')
// 				});
// 				d.show();
// 			}
// 		}
// 	})
// }

var make_delivery_note = function(frm){
	console.log("Delivery Note")
	//TODO: Create function
}