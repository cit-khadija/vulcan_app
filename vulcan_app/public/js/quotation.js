frappe.ui.form.on("Quotation", {
    refresh: function(frm){
        if(frm.doc.docstatus===0 && !frm.doc.__islocal){
            // frm.fields_dict.items.grid.add_custom_button(__('Assign Item Details'), ()=>{
            //     add_item_details_dialog(frm)
            // })
            //TODO: disable creating new item details in Link field of child table. Should use above button always to create one.
            set_hardware_set_details_in_item_details(frm)
        }
    },
    assign_item_details:function(frm){
        add_item_details_dialog(frm)
    },
    validate: function(frm){
        validate_door_no(frm)
    }

})

var validate_door_no = function(frm){
    var door_no_list = []
    if(frm.doc.items && frm.doc.items.length>0){
        $.each(frm.doc.items, (k, item)=>{
            if (door_no_list.includes(item.door_no)){
                var message="Please ensure there are no duplicate Door Nos"
                frappe.throw(message)
            } else {
                door_no_list.push(item.door_no)
            }
        })

    }
}


var add_item_details_dialog = function(frm){
    frm.call({
		method: "vulcan_app.events.quotation.get_items",
		args: {
			quotation: frm.doc.name
		},
		freeze:true,
		callback: function(r){
			if(!r.message) {
				frappe.msgprint("No items in table")
			}
			else {
                const fields = [{
                    label: 'Items',
                    fieldtype: 'Table',
                    fieldname: 'items',
                    description: __('Create or assign Item Detail pages. You can assign item detail page for every Item with Door No'),
                    fields: [{
                        fieldtype: 'Read Only',
                        fieldname: 'item_code',
                        label: __('Item Code'),
                        in_list_view: 1,
                        read_only:1
                    }, {
                        fieldtype: 'Data',
                        fieldname: 'door_no',
                        label:__('Door No'),
                        in_list_view: 1,
                        read_only:1
                    }, {
                        fieldtype: 'Link',
                        fieldname: 'item_details',
                        options: 'Item Details',
                        reqd: 1,
                        label: __('Item Details'),
                        in_list_view: 1,
                        get_query: function (doc) {
                            return { filters: { item_code: doc.item_code, door_no: doc.door_no, quotation: doc.quotation } };
                        }
                    }, {
                        fieldtype: 'Data',
                        fieldname: 'quotation_item',
                        reqd: 1,
                        label: __('Quotation Item'),
                        hidden: 1
                    }, {
                        fieldtype:'Data',
                        fieldname: 'quotation',
                        reqd:1,
                        label: __('Quotation'),
                        hidden:1
                    } 
                    ],
                    data: r.message,
                    get_data: () => {
                        return r.message
                    }
                }
                ]

                var d = new frappe.ui.Dialog({
					title: __('Assign Item Detail Page to Item'),
					fields: fields,
					primary_action: function() {
                        const items = d.get_values()["items"];
                        items.forEach(item => {
                            frappe.model.set_value("Quotation Item", item.name,
                                "item_details", item.item_details);
                        });
                        d.hide();
					},
					primary_action_label: __('Assign')
				});
                d.set_secondary_action(()=>{create_item_details_pages(d, frm)});
                d.set_secondary_action_label(__('Create Pages'))
				d.show();
            }
        }
    })
}

var create_item_details_pages = function(d, frm){
    var data = d.get_values();
    frm.call({
        method: 'vulcan_app.events.quotation.create_item_details_pages',
        freeze: true,
        args: {items:data.items},
        callback: function(r){
            console.log(r.message)
            console.log(r.message.length)
            if(r.message && r.message.length) {
                frappe.msgprint({
                    message: __('Item Detail Pages Created: {0}', [r.message.map(function(doc) {
                            return repl('<a href="/app/item-details/%(name)s">%(name)s</a>', {name:doc.item_details})
                        }).join(', ')]),
                    indicator: 'green'
                })
            } else {
                frappe.msgprint({
                    message: "Item Detail Pages already assigned."
                })
            }
            //TODO: add function to assign it directly after creating
        }
    })
}


var set_hardware_set_details_in_item_details = function(frm){
    var hw_set_data = {}
    if(frm.doc.hw_set_data){
        hw_set_data = JSON.parse(frm.doc.hw_set_data)
    }
    if (frm.doc.items && frm.doc.items.length > 0){
        $.each(frm.doc.items, function(k, item){

            var item_hw_set = {}
            if(hw_set_data[item.hardware_set]){
                item_hw_set[item.hardware_set] = hw_set_data[item.hardware_set]
            }

            if (item.item_details){
                frappe.db.set_value("Item Details", item.item_details, {"hardware_set":item.hardware_set, "hw_set_data":JSON.stringify(item_hw_set)})
            }
        })
    }
}

//TODO: check functionality of hw_items and remove it if not needed