frappe.ui.form.on('Sales Order', {
    refresh: function(frm) {
        if(frm.doc.docstatus==1){
            let allow_delivery = false
            if(frm.doc.status !== 'Closed') {
                if(frm.doc.status !== 'On Hold') {
                    //Removing Work Order and Delivery Note creation
                    setTimeout(()=>{
                        frm.remove_custom_button('Work Order', 'Create');
                        frm.remove_custom_button('Delivery Note', 'Create');
                    },1000)
                    


                    // allow_delivery = frm.doc.items.some(item => item.delivered_by_supplier === 0 && item.qty > flt(item.delivered_qty))
                    //     && !frm.doc.skip_delivery_note

                    //TODO check if following conditions are required
                    // Adding button to create order_processing
                    // const order_is_a_sale = ["Sales", "Shopping Cart"].indexOf(frm.doc.order_type) !== -1;
                    // // order type has been customised then show all the action buttons
                    // const order_is_a_custom_sale = ["Sales", "Shopping Cart", "Maintenance"].indexOf(frm.doc.order_type) === -1;
    
                    // delivery note
                    // if(flt(frm.doc.per_delivered, 6) < 100 && (order_is_a_sale || order_is_a_custom_sale) && allow_delivery) {
                    //     frm.add_custom_button(__('Order Processing'), () => make_order_processing(frm), __('Create'));
                    // }
                    
                    frm.add_custom_button(__('Order Processing'), () => make_order_processing(frm), __('Create'));
                }
            }
        }
    },
})


var make_order_processing = function(frm){
    frappe.model.open_mapped_doc({
        method: "vulcan_app.events.sales_order.make_order_processing",
        frm: frm
    })
}