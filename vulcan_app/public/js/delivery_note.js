frappe.ui.form.on('Delivery Note', {
    validate: function(frm){
        update_items(frm)
        //TODO: validate that all item hardware sets are added
    },
})

var get_selected_children = function(frm) {
    return (frm.fields_dict['items'].grid.grid_rows || []).map(row => {
        return row.doc.is_hw_set_item ? null : row.doc;
    }).filter(d => {
        return d;
    });
}

var update_items = function(frm){
    var item_list = get_selected_children(frm) //TODO Rename this function 
    frm.clear_table("items")

    $.each(item_list, (k, item)=>{
        let child = frm.add_child("items", item)
    })
    frm.refresh_fields("items")
    add_hardware_set_items(frm)
}

var add_hardware_set_items = function(frm){
    frappe.call({
        method:"vulcan_app.vulcan_app.doctype.item_details.item_details.get_hardware_set_items",
        args: {
            items:frm.doc.items,
            docname: frm.doc.name,
            doctype: frm.doc.doctype
        },
        freeze:true,
        callback: function(r){
            var hw_items = r.message
            if(hw_items.length > 0){
                $.each(hw_items, (k, hw_item)=>{
                    let child = frm.add_child("items", hw_item);
                    frm.trigger('item_code', child.doctype, child.name);
                })
                frm.refresh_fields("items")
            }
        }
    })
}