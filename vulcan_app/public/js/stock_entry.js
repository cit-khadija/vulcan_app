frappe.ui.form.on("Stock Entry", {
    setup: function(frm){
        if (frm.doc.stock_entry_type == "Bulk Manufacture") {
            frm.trigger("bulk_manufacture")
        }
    },

    stock_entry_type: function(frm){
        if (frm.doc.stock_entry_type == "Bulk Manufacture") {
            frm.trigger("bulk_manufacture")
        }
    },

    bulk_manufacture: function(frm){
        var total_amount = get_total_raw_material_amount(frm)
        var total_qty = get_total_produced_item_qty(frm)
        set_basic_rate_for_finished_item(frm, total_amount, total_qty)
    },
})


var get_total_raw_material_amount = function(frm){
    var items = frm.doc.items
    var total_amount = 0
    if(items && items.length>0){
        $.each(items, (k,item)=>{
            if(!item.is_finished_item){
                total_amount = total_amount + (item.basic_rate * item.qty)
            }
        })
    }
    return total_amount
}

var get_total_produced_item_qty = function(frm){
    var items = frm.doc.items
    var total_qty = 0
    if(items && items.length>0){
        $.each(items, (k,item)=>{
            if(item.is_finished_item){
                total_qty = total_qty + item.qty
            }
        })
    }
    return total_qty
}

var set_basic_rate_for_finished_item = function(frm, total_amount, total_qty){
    var rate = 0
    if(total_qty > 0){
        rate = total_amount/total_qty
    }
    var items = frm.doc.items

    if(items && items.length>0){
        $.each(items, (k,item)=>{
            if(item.is_finished_item){
                item.basic_rate = rate
                item.basic_amount = item.basic_rate * item.qty
            }
        })
    }
    frm.refresh_field("items")
}