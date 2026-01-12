from __future__ import annotations

from app.domain.facturas.entities import Concepto, Factura, Pago
from app.domain.retenciones.entities import RetencionPlataforma


def create_factura_from_parsed(parsed: dict) -> Factura:
    factura = Factura(
        uuid=parsed.get("uuid"),
        version=parsed.get("version"),
        tipo_comprobante=parsed.get("tipo_comprobante"),
        fecha_emision=parsed.get("fecha_emision"),
        year_emision=parsed.get("year_emision"),
        month_emision=parsed.get("month_emision"),
        naturaleza=parsed.get("naturaleza"),
        emisor_rfc=parsed.get("emisor_rfc"),
        emisor_nombre=parsed.get("emisor_nombre"),
        receptor_rfc=parsed.get("receptor_rfc"),
        receptor_nombre=parsed.get("receptor_nombre"),
        uso_cfdi=parsed.get("uso_cfdi"),
        moneda=parsed.get("moneda"),
        metodo_pago=parsed.get("metodo_pago"),
        forma_pago=parsed.get("forma_pago"),
        subtotal=parsed.get("subtotal"),
        descuento=parsed.get("descuento"),
        total=parsed.get("total"),
        total_trasladados=parsed.get("total_trasladados"),
        total_retenidos=parsed.get("total_retenidos"),
        xml_text=parsed.get("xml_text", ""),
    )

    for c in parsed.get("conceptos", []):
        factura.conceptos.append(
            Concepto(
                clave_prod_serv=c.get("clave_prod_serv"),
                cantidad=c.get("cantidad"),
                clave_unidad=c.get("clave_unidad"),
                descripcion=c.get("descripcion"),
                valor_unitario=c.get("valor_unitario"),
                importe=c.get("importe"),
                objeto_imp=c.get("objeto_imp"),
            )
        )

    for p in parsed.get("pagos", []):
        factura.pagos.append(
            Pago(
                fecha_pago=p.get("fecha_pago"),
                year_pago=p.get("year_pago"),
                month_pago=p.get("month_pago"),
                monto=p.get("monto"),
                moneda_p=p.get("moneda_p"),
                forma_pago_p=p.get("forma_pago_p"),
            )
        )

    return factura


def create_retencion_from_parsed(parsed: dict) -> RetencionPlataforma:
    return RetencionPlataforma(
        uuid=parsed.get("uuid"),
        version=parsed.get("version"),
        fecha_exp=parsed.get("fecha_exp"),
        ejercicio=parsed.get("ejercicio"),
        mes_ini=parsed.get("mes_ini"),
        mes_fin=parsed.get("mes_fin"),
        emisor_rfc=parsed.get("emisor_rfc"),
        emisor_nombre=parsed.get("emisor_nombre"),
        receptor_rfc=parsed.get("receptor_rfc"),
        receptor_nombre=parsed.get("receptor_nombre"),
        monto_tot_operacion=parsed.get("monto_tot_operacion"),
        monto_tot_grav=parsed.get("monto_tot_grav"),
        monto_tot_exent=parsed.get("monto_tot_exent"),
        monto_tot_ret=parsed.get("monto_tot_ret"),
        periodicidad=parsed.get("periodicidad"),
        num_serv=parsed.get("num_serv"),
        mon_tot_serv_siva=parsed.get("mon_tot_serv_siva"),
        total_iva_trasladado=parsed.get("total_iva_trasladado"),
        total_iva_retenido=parsed.get("total_iva_retenido"),
        total_isr_retenido=parsed.get("total_isr_retenido"),
        dif_iva_entregado_prest_serv=parsed.get("dif_iva_entregado_prest_serv"),
        mon_total_por_uso_plataforma=parsed.get("mon_total_por_uso_plataforma"),
        xml_text=parsed.get("xml_text", ""),
    )
