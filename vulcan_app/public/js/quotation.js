frappe.ui.form.on("Quotation", {
    refresh: function(frm){

        frm.set_query("item_details", "items", function(doc, cdt, cdn){
            return {
                "filters": {
                    "quotation": frm.doc.name
                }
            }
        })

        if(frm.doc.docstatus===0 && !frm.doc.__islocal){
            //TODO: disable creating new item details in Link field of child table. Should use above button always to create one.
            //Check if it is possible by restricting create access.
            set_hardware_set_details_in_item_details(frm)
        }
    },
    assign_item_details:function(frm){
        add_item_details_dialog(frm)
    },
    validate: function(frm){
        validate_door_no(frm);
        validate_hw_sets(frm);
        set_door_price(frm);
    },
    before_submit: function(frm){
        validate_item_details(frm)
    },
    add_hardware_set: function(frm){
        add_item_dialog(frm);
    }
})


var set_door_price = function(frm){
    if(frm.doc.items && frm.doc.items.length>0){
        $.each(frm.doc.items, (k, item)=>{
            var unit_price = item.door_price + item.hardware_price + item.installation_price
            frappe.model.set_value("Quotation Item", item.name, "rate", unit_price)
        })
    }
}


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

var validate_item_details = function(frm){
    $.each(frm.doc.items, (k,item)=>{
        if(item.door_no && !item.item_details){
            //TODO: Add validation for quotation no.
            var message="Please assign Item Details to all door items"
            frappe.throw(message)
        }
    })
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


var set_hardware_set_details_in_item_details  = function(frm){
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

//HARDWARE SET CUSTOMIZATION

var add_item_dialog = function(frm){
    let d = new frappe.ui.Dialog({
        title: "Add Hardware Set",
        fields: [
            {
                label:"Hardware Set",
                fieldname:"hardware_set",
                fieldtype:"Link",
                options:"Hardware Set",
                reqd:1,
                get_query: ()=>{
                    var set_list = [];
                    if(frm.doc.items && frm.doc.items.length > 0){
                        $.each(frm.doc.items, (k,item)=>{
                            if(item.hardware_set){
                                set_list.push(item.hardware_set);
                            }
                        });
                    }
                    set_list = [...new Set(set_list)];
                    return {
                        filters: {'hardware_set': ['in',set_list]}
                    };
                }
            },
            {
                label:"Fetch Items",
                fieldname:"fetch_items",
                fieldtype:"Button",
                click: ()=>{ fetch_items(frm, d)}
            },
            {
                label:"Add Items for Hardware Set", 
                fieldname:"items",
                fieldtype: "Table",
                cannot_add_rows: false,
                is_editable_grid: true,
                data: [],
                in_place_edit: true,
                fields: [
                    {
                        label:"Item",
                        fieldname: "item_code",
                        fieldtype: "Link",
                        options:"Item",
                        reqd:1,
                        in_list_view: true,
                        onchange: ()=>{
                            d.fields_dict.items.df.data.some(item => {
                                frappe.db.get_value("Item", item.item_code, ['item_name', 'description','stock_uom']).then(r => {
                                    if (r.message){
                                        item.description = r.message.description;
                                        item.uom = r.message.stock_uom;
                                        if (item.item_name != r.message.item_name){
                                            item.item_name = r.message.item_name;
                                        }
                                        if(!item.qty){
                                            item.qty = 1;
                                        }
                                        d.fields_dict.items.grid.refresh();
                                        return true;
                                    }
                                });
                            });
                        }
                    },
                    {
                        label:"Item Name",
                        fieldname:"item_name",
                        fieldtype:"Data",
                        in_list_view: true
                    },  
                    {
                        label:"Description",
                        fieldname:"description",
                        fieldtype:"Text Editor",
                        in_list_view:true
                    },
                    {
                        label:"Quantity",
                        fieldname:"qty",
                        fieldtype:"Float",
                        in_list_view:true
                    },
                    {
                        label:"UOM",
                        fieldname:"uom",
                        fieldtype:"Link",
                        options:"UOM",
                        in_list_view:true
                    }
                ]
            }
        ],
        primary_action_label: "Add",
        primary_action(values){
            d.hide();
            add_hardware_set(values, frm);
        }
    });
    d.show();
    d.$wrapper.find('.modal-content').css("width", "800px");
};

var add_hardware_set = function(values, frm){
    //Function to add hardware set data entered in dialog.
    
    //validate if same item codes have been added more than once
    var items_list = [];
    $.each(values.items, (k,item)=>{
        if(items_list.includes(item.item_code)){
            frappe.throw("Duplicate Items cannot be added to same Hardware Set. Please try again.");
        } else {
            items_list.push(item.item_code);
        }
    });

    //Get and update hw_set_data    
    var hw_set_data = {};
    if(frm.doc.hw_set_data){
        hw_set_data = JSON.parse(frm.doc.hw_set_data);
    }

    if(values.items && values.items.length > 0){
        hw_set_data[values.hardware_set]=[];
        $.each(values.items, function(k, item){
            let x={
                'item_code': item.item_code,
                'item_name': item.item_name,
                'qty': item.qty,
                'uom': item.uom,
                'description':item.description
            };
            hw_set_data[values.hardware_set].push(x);
        });
    }
    frm.set_value("hw_set_data", JSON.stringify(hw_set_data));
};

var validate_hw_sets = function(frm){
    //Validate if all hardware_sets are defined.
    var hw_set_data = {};
    if(frm.doc.hw_set_data){
        hw_set_data = JSON.parse(frm.doc.hw_set_data);
    }

    if(frm.doc.items && frm.doc.items.length>0){
        $.each(frm.doc.items, (k, item)=>{
            if(item.hardware_set){
                if(!hw_set_data[item.hardware_set]){
                    let message = "Please add details for Hardware Set "+item.hardware_set;
                    frappe.throw(message);
                }
            }
        });
    }
};

var fetch_items = function(frm, d){
    //Fetch hw_set data defined for hardware set
    if(frm.doc.hw_set_data){
        var hardware_set = d.fields_dict.hardware_set.value;
        var hw_set_data = JSON.parse(frm.doc.hw_set_data);

        $.each(hw_set_data[hardware_set], function(k, item){
            d.fields_dict.items.df.data.push(item);
        });
        d.fields_dict.items.grid.refresh();
    }
};