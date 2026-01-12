from __future__ import annotations

from app.application.declaraciones.dto import DeclaracionListItem
from app.application.facturas.dto import FacturaListItem
from app.application.retenciones.dto import RetencionListItem
from app.adapters.outbound.db import models


def factura_to_list_item(row: models.FacturaModel) -> FacturaListItem:
    return FacturaListItem(
        id=row.id,
        uuid=row.uuid,
        fecha_emision=row.fecha_emision,
        tipo_comprobante=row.tipo_comprobante,
        year_emision=row.year_emision,
        month_emision=row.month_emision,
        emisor_rfc=row.emisor_rfc,
        emisor_nombre=row.emisor_nombre,
        receptor_rfc=row.receptor_rfc,
        receptor_nombre=row.receptor_nombre,
        uso_cfdi=row.uso_cfdi,
        moneda=row.moneda,
        subtotal=float(row.subtotal) if row.subtotal is not None else None,
        descuento=float(row.descuento) if row.descuento is not None else None,
        total=float(row.total) if row.total is not None else None,
        total_trasladados=float(row.total_trasladados) if row.total_trasladados is not None else None,
        total_retenidos=float(row.total_retenidos) if row.total_retenidos is not None else None,
        naturaleza=row.naturaleza,
    )


def retencion_to_list_item(row: models.RetencionModel) -> RetencionListItem:
    return RetencionListItem(
        id=row.id,
        uuid=row.uuid,
        fecha_exp=row.fecha_exp,
        ejercicio=row.ejercicio,
        mes_ini=row.mes_ini,
        mes_fin=row.mes_fin,
        emisor_rfc=row.emisor_rfc,
        emisor_nombre=row.emisor_nombre,
        receptor_rfc=row.receptor_rfc,
        mon_tot_serv_siva=float(row.mon_tot_serv_siva)
        if row.mon_tot_serv_siva is not None
        else None,
        total_iva_trasladado=float(row.total_iva_trasladado)
        if row.total_iva_trasladado is not None
        else None,
        total_iva_retenido=float(row.total_iva_retenido)
        if row.total_iva_retenido is not None
        else None,
        total_isr_retenido=float(row.total_isr_retenido)
        if row.total_isr_retenido is not None
        else None,
    )


def declaracion_to_list_item(row: models.DeclaracionModel) -> DeclaracionListItem:
    return DeclaracionListItem(
        id=row.id,
        year=row.year,
        month=row.month,
        rfc=row.rfc,
        folio=row.folio,
        fecha_presentacion=row.fecha_presentacion,
        filename=row.filename,
        original_name=row.original_name,
        num_pages=row.num_pages,
        sha256=row.sha256,
    )
