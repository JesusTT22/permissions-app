frappe.ui.form.on('Administrar Permisos', {
    refresh: function(frm) {
        // Botón opcional para forzar el escaneo de dependencias manualmente
        frm.add_custom_button(__('Escanear Dependencias'), () => {
            detectar_faltantes(frm);
        });
    },
    rol_principal: function(frm) {
        if (!frm.doc.rol_principal) return;
        obtener_permisos_existentes(frm);
    }
});

// Detectar cuando se agrega o cambia un Doctype en la tabla principal
frappe.ui.form.on('Permisos por Documento', { // Reemplaza con el nombre real de tu Child Table
    tipo_de_documento: function(frm, cdt, cdn) {
        detectar_faltantes(frm);
    },
    lista_de_permisos_remove: function(frm) {
        detectar_faltantes(frm);
    }
});

function obtener_permisos_existentes(frm) {
    frappe.call({
        method: 'permissions_app.permissions_app.doctype.administrar_permisos.administrar_permisos.get_permisos_por_documento',
        args: { role: frm.doc.rol_principal },
        callback: (r) => {
            frm.clear_table('lista_de_permisos');
            if (r.message) {
                r.message.forEach(item => {
                    let row = frm.add_child('lista_de_permisos');
                    Object.assign(row, item);
                });
            }
            frm.refresh_field('lista_de_permisos');
            detectar_faltantes(frm);
        }
    });
}

function detectar_faltantes(frm) {
    const doctypes = (frm.doc.lista_de_permisos || [])
        .map(row => row.tipo_de_documento).filter(d => d);

    if (!doctypes.length) {
        frm.clear_table('enlace_documento');
        frm.refresh_field('enlace_documento');
        return;
    }

    frappe.call({
        method: 'permissions_app.permissions_app.doctype.administrar_permisos.administrar_permisos.get_doctypes_faltantes',
        args: { doctypes: JSON.stringify(doctypes) },
        callback: (r) => {
            frm.clear_table('enlace_documento');
            if (r.message && r.message.length > 0) {
                r.message.forEach(item => {
                    let row = frm.add_child('enlace_documento');
                    // Formateamos para que sea legible: "Origen -> Destino (Campo)"
                    row.tipo_de_permiso = `${item.doctype_origen} → ${item.tipo_documento}`;
                    row.base_de_datos = item.campo; // Asumiendo que tienes este campo en la tabla de enlaces
                });
                frappe.show_alert({
                    message: __("Se detectaron dependencias faltantes"),
                    indicator: 'orange'
                });
            }
            frm.refresh_field('enlace_documento');
        }
    });
}