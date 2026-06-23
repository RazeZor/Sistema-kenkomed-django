"""Generación de PDF del registro de auditoría clínica."""
from io import BytesIO

from django.utils import timezone
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle


def _celda(texto, max_len=120):
    if not texto:
        return '—'
    texto = str(texto).replace('\n', ' ').strip()
    if len(texto) > max_len:
        return texto[: max_len - 1] + '…'
    return texto


def generar_auditoria_pdf(clinica, registros, dias, generado_por=''):
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=landscape(A4),
        leftMargin=1.2 * cm,
        rightMargin=1.2 * cm,
        topMargin=1.5 * cm,
        bottomMargin=1.5 * cm,
        title='Registro de auditoría clínica',
    )

    styles = getSampleStyleSheet()
    titulo_style = ParagraphStyle(
        'TituloAuditoria',
        parent=styles['Heading1'],
        fontSize=16,
        spaceAfter=6,
        textColor=colors.HexColor('#1e3a5f'),
    )
    subtitulo_style = ParagraphStyle(
        'SubtituloAuditoria',
        parent=styles['Normal'],
        fontSize=9,
        textColor=colors.HexColor('#4b5563'),
        spaceAfter=12,
    )

    ahora = timezone.localtime(timezone.now())
    nombre_centro = clinica.nombre if clinica else 'Centro no identificado'
    elementos = [
        Paragraph('KenkoMed — Registro de auditoría clínica', titulo_style),
        Paragraph(
            f'<b>Centro:</b> {_celda(nombre_centro, 80)} &nbsp;|&nbsp; '
            f'<b>Período:</b> últimos {dias} días &nbsp;|&nbsp; '
            f'<b>Generado:</b> {ahora.strftime("%d/%m/%Y %H:%M")}'
            + (f' &nbsp;|&nbsp; <b>Por:</b> {_celda(generado_por, 60)}' if generado_por else ''),
            subtitulo_style,
        ),
        Paragraph(
            'Documento de trazabilidad de accesos y modificaciones sobre fichas clínicas '
            '(Ley 21.719 — protección de datos personales).',
            subtitulo_style,
        ),
        Spacer(1, 0.3 * cm),
    ]

    encabezados = ['Fecha / Hora', 'Acción', 'Detalle', 'Paciente', 'Profesional', 'IP']
    filas = [encabezados]

    for r in registros:
        fecha_local = timezone.localtime(r.fecha)
        filas.append([
            fecha_local.strftime('%d/%m/%Y %H:%M'),
            r.get_accion_display(),
            _celda(r.detalle, 80),
            _celda(r.paciente_display(), 50),
            _celda(r.profesional_display(), 45),
            r.ip_address or '—',
        ])

    if len(filas) == 1:
        filas.append(['—', 'Sin registros en el período', '—', '—', '—', '—'])

    tabla = Table(
        filas,
        colWidths=[3.2 * cm, 5.5 * cm, 5.5 * cm, 5.5 * cm, 5.5 * cm, 2.8 * cm],
        repeatRows=1,
    )
    tabla.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1e40af')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 8),
        ('FONTSIZE', (0, 1), (-1, -1), 7),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('GRID', (0, 0), (-1, -1), 0.25, colors.HexColor('#d1d5db')),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f9fafb')]),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('LEFTPADDING', (0, 0), (-1, -1), 4),
        ('RIGHTPADDING', (0, 0), (-1, -1), 4),
    ]))
    elementos.append(tabla)

    elementos.append(Spacer(1, 0.4 * cm))
    elementos.append(Paragraph(
        f'Total de registros: {len(registros)} — Página generada automáticamente por KenkoMed.',
        subtitulo_style,
    ))

    doc.build(elementos)
    buffer.seek(0)
    return buffer.getvalue()
