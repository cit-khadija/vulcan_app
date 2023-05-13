// Copyright (c) 2023, Crafrt and contributors
// For license information, please see license.txt

frappe.ui.form.on('Item Details', {
	// setup: function(frm){
	// 	frm.set_query("bom", function(){
	// 		return {
	// 			filters:{
	// 				"item":frm.doc.item_code,
	// 				"is_active":1,
	// 				"docstatus": 1
	// 			}
	// 		}
	// 	})
	// },
	// get_raw_materials: function(frm){
	// 	//Function to get raw materials from BOM and push to table
	// 	if (!frm.doc.bom){
	// 		frappe.msgprint({message:"Please enter BOM first.", indicator:"red"})
	// 	} else {
	// 		frappe.db.get_doc("BOM", frm.doc.bom).then((bom)=>{
	// 			if (bom.items && bom.items.length > 0){
	// 				//check if raw material table is empty, if yes push raw material details otherwise prompt to ask if they are sure and clear the table
	// 				if (frm.doc.raw_materials_tab && frm.doc.raw_materials_tab.length > 0){
	// 					//TODO: test this part
	// 					//TODO: check why this function is being triggered on clicking enter
	// 					frappe.confirm("Are you sure you want to proceed?. Raw materials will be re-entered", 
	// 					()=>{
	// 						add_raw_materials_to_table(frm, bom.items)
	// 					}, ()=>{
	// 						frappe.show_alert({message:"No changes made to raw materials", indicator:"green"})
	// 					})
	// 				} else {
	// 					add_raw_materials_to_table(frm, bom.items)
	// 				}
	// 			}
	// 		})
	// 	}
	// }
});

// var add_raw_materials_to_table = function(frm, items){
// 	frm.clear_table("raw_materials_tab");
// 	$.each(items, (k,item)=>{
// 		let rm_item = {
// 			item_code: item.item_code,
// 			item_name: item.item_name,
// 			uom: item.uom,
// 			qty: item.qty,
// 			qty_consumed_per_unit: item.qty_consumed_per_unit,
// 			rate: item.rate
// 		}
// 		let child = frm.add_child("raw_materials_tab", rm_item)
// 	})
// 	frm.refresh_fields("raw_materials_tab");
// 	frm.save()
// }

//TODO: add raw material details if BOM exists
//TODO: automatically populate or fetch item description, uom, rate, amount etc. for raw materials
//TODO: find the possibility of just using BOM Item doctype here

// frappe.ui.form.on("Raw Material Item", "item_code", function(frm, cdt, cdn){
// 	var d = locals[cdt][cdn];
// 	frappe.db.get_value("Item", {name: d.item_code}, ["item_name", "stock_uom", "description"], (r)=>{
// 		d.item_name = r.item_name;
// 		d.uom = r.stock_uom;
// 		d.description = r.description
// 		d.stock_uom = r.stock_uom
// 		refresh_field("item_name")
// 		refresh_field("uom")
// 		refresh_field("description")
// 		refresh_field("stock_uom")
// 	})
// })

// frappe.ui.form.on("Raw Material Item", "rate", function(frm, cdt, cdn){
// 	var d = locals[cdt][cdn];
// 	d.amount = flt(d.rate * d.qty);
// })

// frappe.ui.form.on("Raw Material Item", "qty", function(frm, cdt, cdn){
// 	var d = locals[cdt][cdn];
// 	d.amount = flt(d.rate * d.qty);
// })