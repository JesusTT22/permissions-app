frappe.ui.form.on('Role', {
    // El evento 'refresh' ocurre cada vez que abres el documento o lo recargas
    refresh: function(frm) {
        
        // Verificación: 
        // !frm.doc.__islocal -> ¿El documento ya está guardado en la DB?
        // frm.doc.parent_role -> ¿Tiene un Rol Padre seleccionado?
        if (!frm.doc.__islocal && frm.doc.parent_role) {
            
            // Preguntar al servidor cuántos permisos tiene ya este Rol.
            // Esto evita sobreescribir o duplicar si el usuario solo entró a ver el Rol.
            frappe.call({
                method: 'frappe.client.get_count',
                args: {
                    doctype: 'Custom DocPerm',
                    filters: { role: frm.doc.name }
                },
                callback: function(r) {
                    // Si la cuenta es 0 (no tiene permisos), procedemos a pedir la herencia
                    if (r.message === 0) {
                        
                        // Llamar a nuestra función de api.py
                        frappe.call({
                            method: 'permissions_app.api.heredar_permisos_rol',
                            args: {
                                role_name: frm.doc.name,
                                role_parent: frm.doc.parent_role
                            },
                            callback: function(res) {
                                // Si el servidor responde con un mensaje, lo mostramos
                                if (res.message) {
                                    frappe.msgprint(res.message);
                                    // Recargar el formulario para que el usuario vea los permisos nuevos abajo
                                    frm.reload_doc(); 
                                }
                            }
                        });
                    }
                }
            });
        }
    }
});