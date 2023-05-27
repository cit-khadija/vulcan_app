// Copyright (c) 2023, Crafrt and contributors
// For license information, please see license.txt

frappe.ui.form.on('Order Processing', {
	setup: function(frm){
		frm.custom_make_buttons = {
			'Delivery Note': 'Delivery Note'
		}
	},
	refresh: function(frm){
		var per_delivered = get_percentage_delivered(frm)
		if(frm.doc.docstatus==1){
			//TODO Add status to close and reopen
			if(flt(per_delivered, 6) < 100) {
				frm.add_custom_button(__('Delivery Note'), () => make_delivery_note(frm), __('Create'));
				frm.add_custom_button(__('Partial Delivery'), () => make_partial_delivery_note(frm), __('Create'));
			}
		}
	},
	validate: function(frm){
	}
});

//TODO HIGH: on_save validation whether an OP already exists on the same sales order with docstatus 1
//TODO: add sales order items when selecting sales order
//TODO: Check if non-stock items can cause issues

var get_percentage_delivered = function(frm){
	var per_delivered = 0;
	//TODO: get percentage delivered
	return per_delivered
}

var make_delivery_note = function(frm){
	frm.call({
		method: "vulcan_app.vulcan_app.doctype.order_processing.order_processing.get_items_to_deliver",
		args: {
			order_processing: frm.doc.name
		},
		freeze:true,
		callback: function(r){
			if(!r.message) {
				frappe.msgprint({
					title: __('Delivery Order not created'),
					message: __('No Items with deliverable quantity'),
					indicator: 'orange'
				});
				return;
			}
			else {
				const fields = [{
					label: 'Items',
					fieldtype: 'Table',
					fieldname: 'items',
					description: __('Select Qty to Deliver'),
					fields: [{
						fieldtype: 'Read Only',
						fieldname: 'item_code',
						label: __('Item Code'),
						in_list_view: 1
					}, {
						fieldtype: 'Read Only',
						fieldname: 'door_no',
						label:__('Door No'),
						in_list_view: 1
					}, {
						fieldtype: 'Float',
						fieldname: 'qty',
						reqd: 1,
						label: __('Qty'),
						in_list_view: 1
					}, {
						fieldtype: 'Data',
						fieldname: 'sales_order_item',
						reqd: 1,
						label: __('Sales Order Item'),
						hidden: 1
					}],
					//TODO: check other fields that should be passed?
					data: r.message,
					get_data: () => {
						return r.message
					}
				}]

				var d = new frappe.ui.Dialog({
					title: __('Select Items to Deliver'),
					fields: fields,
					primary_action: function() {
						var data = {items: d.fields_dict.items.grid.get_selected_children()};
						d.hide();
						frappe.model.open_mapped_doc({
							method: 'vulcan_app.vulcan_app.doctype.order_processing.order_processing.make_delivery_note',
							frm:frm,
							args: {
								dn_items: data,
								is_partial_delivery: 0
							},
							freeze_message: __("Creating Delivery Note ...")
						});
					},
					primary_action_label: __('Create')
				});
				d.show();
			}
		}
	})
}

var make_partial_delivery_note = function(frm){
	frm.call({
		method: "vulcan_app.vulcan_app.doctype.order_processing.order_processing.get_item_parts_to_deliver",
		args: {
			order_processing: frm.doc.name
		},
		freeze:true,
		callback: function(r){
			if(!r.message) {
				frappe.msgprint({
					title: __('Delivery Order not created'),
					message: __('No Items with deliverable parts'),
					indicator: 'orange'
				});
				return;
			}
			else {
				const fields = [{
					label: 'Items',
					fieldtype: 'Table',
					fieldname: 'items',
					description: __('Select Qty and Part to Deliver'),
					fields: [{
						fieldtype: 'Read Only',
						fieldname: 'item_code',
						label: __('Item Code'),
						in_list_view: 1
					}, {
						fieldtype: 'Read Only',
						fieldname: 'door_no',
						label:__('Door No'),
						in_list_view: 1
					}, {
						fieldtype: 'Float',
						fieldname: 'qty',
						reqd: 1,
						label: __('Qty'),
						in_list_view: 1
					}, {
						fieldtype: 'Link',
						options: 'Item',
						fieldname: 'delivery_part_item',
						reqd: 1,	
						label: __('Select Item to Deliver'),
						in_list_view: 1,
						get_query: function(doc){
							return {
								//TODO SETUP: Add this item group
								filters: {item_group: "Partial Delivery Items"}
							}
						}
					}],
					data: r.message,
					get_data: () => {
						return r.message
					}
				}]

				var d = new frappe.ui.Dialog({
					title: __('Select Items to Deliver'),
					fields: fields,
					primary_action: function() {
						var data = {items: d.fields_dict.items.grid.get_selected_children()};
						// d.hide();
						// console.log(data)
						frappe.model.open_mapped_doc({
							method: 'vulcan_app.vulcan_app.doctype.order_processing.order_processing.make_delivery_note',
							frm:frm,
							args: {
								dn_items: data,
								is_partial_delivery: 1
							},
							freeze_message: __("Creating Delivery Note ..."),
							callback: function(r){
								d.hide();
							}
						});
					},
					primary_action_label: __('Create')
				});
				d.show();
			}
		}
	})
}