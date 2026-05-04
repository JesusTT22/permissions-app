// Copyright (c) 2026, Jesus T. and contributors
// For license information, please see license.txt

frappe.ui.form.on('Administrar Permisos', {

    rol_principal: function(frm) {
        frm.clear_table('lista_de_permisos');
        frm.clear_table('enlace_documento');
        frm.refresh_field('lista_de_permisos');
        frm.refresh_field('enlace_documento');

        const role = frm.doc.rol_principal;
        if (!role) return;

        // Cargar DocTypes del rol con sus permisos en la tabla superior
        frappe.call({
            method: 'permissions_app.permissions_app.doctype.administrar_permisos.administrar_permisos.get_permisos_por_documento',
            args: { role },
            callback: (r) => {
                if (!r.message || !r.message.length) {
                    frappe.msgprint(__('No se encontraron permisos para el rol seleccionado.'));
                    return;
                }

                r.message.forEach(item => {
                    let row = frm.add_child('lista_de_permisos');
                    row.tipo_de_documento  = item.tipo_documento;
                    row.leer               = item.leer;
                    row.escribir           = item.escribir;
                    row.crear              = item.crear;
                    row.eliminar           = item.eliminar;
                    row.seleccionar        = item.seleccionar;
                    row.impresion          = item.impresion;
                    row.correo_electronico = item.correo;
                });

                frm.refresh_field('lista_de_permisos');

                // Detectar doctypes faltantes basados en los que ya tiene el rol
                detectar_faltantes(frm);
            }
        });
    }
});

// Escuchar cambios en la tabla hija lista_de_permisos
frappe.ui.form.on('Permiso Rol Detalle', {

    // Al cambiar/agregar un tipo_de_documento manualmente
    tipo_de_documento: function(frm) {
        detectar_faltantes(frm);
    },

    // Al eliminar una fila de la tabla superior
    lista_de_permisos_remove: function(frm) {
        detectar_faltantes(frm);
    }
});

/**
 * Detecta los DocTypes que los doctypes del rol necesitan
 * (via campos Link) pero que el rol AÚN NO TIENE permiso.
 *
 * Estos son exactamente los que causan errores de permisos:
 * el usuario intenta acceder a un campo Link de un doctype
 * pero no tiene permiso sobre el doctype destino.
 *
 * La tabla "enlace_documento" muestra estos faltantes
 * para que el administrador pueda decidir cuáles agregar.
 */
function detectar_faltantes(frm) {
    // Recolectar todos los doctypes actuales de la tabla superior
    const doctypes = (frm.doc.lista_de_permisos || [])
        .map(row => row.tipo_de_documento)
        .filter(d => d && d.trim() !== '');

    // Limpiar tabla inferior siempre
    frm.clear_table('enlace_documento');
    frm.refresh_field('enlace_documento');

    if (!doctypes.length) return;

    frappe.call({
        method: 'permissions_app.permissions_app.doctype.administrar_permisos.administrar_permisos.get_doctypes_faltantes',
        args: { doctypes: JSON.stringify(doctypes) },
        callback: (r) => {
            if (!r.message || !r.message.length) {
                // No hay faltantes: todos los doctypes necesarios ya tienen permiso
                frappe.show_alert({
                    message: __('No se detectaron conflictos de permisos.'),
                    indicator: 'green'
                });
                return;
            }

            r.message.forEach(item => {
                let row = frm.add_child('enlace_documento');
                // Mostrar: "QuienLoNecesita -> DocTypeFaltante (via campo)"
                row.tipo_de_permiso = __(item.doctype_origen)
                    + " → " + __(item.doctype_destino)
                    + " (" + item.campo + ")";
            });

            frm.refresh_field('enlace_documento');

            // Informar cuántos conflictos se detectaron
            frappe.show_alert({
                message: r.message.length + __(' conflicto(s) de permisos detectado(s).'),
                indicator: 'orange'
            });
        }
    });
}