"""
Enrollment Application PDF — layout mirrors studentData.html + familyData.html.
"""
from django.http import HttpResponse
from ..models import Student
from datetime import datetime, date
import io

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, mm
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle,
    Paragraph, Spacer, HRFlowable, KeepTogether
)
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT

# ── Palette ───────────────────────────────────────────────────────────────────
RED_900  = colors.HexColor('#7f1d1d')
RED_MID  = colors.HexColor('#991b1b')
BLUE_600 = colors.HexColor('#2563eb')
BLUE_50  = colors.HexColor('#eff6ff')
BLUE_300 = colors.HexColor('#93c5fd')
GRAY_800 = colors.HexColor('#1f2937')
GRAY_700 = colors.HexColor('#374151')
GRAY_600 = colors.HexColor('#4b5563')
GRAY_500 = colors.HexColor('#6b7280')
GRAY_300 = colors.HexColor('#d1d5db')
GRAY_200 = colors.HexColor('#e5e7eb')
GRAY_100 = colors.HexColor('#f3f4f6')
GRAY_50  = colors.HexColor('#f9fafb')
WHITE    = colors.white
GREEN    = colors.HexColor('#15803d')


# ── Tiny helpers ──────────────────────────────────────────────────────────────
def _v(val, fallback='—'):
    if val is None or str(val).strip() in ('', 'None', 'none'):
        return fallback
    return str(val).strip()

def _fmt_date(val):
    if not val:
        return '—'
    return val.strftime('%B %d, %Y') if hasattr(val, 'strftime') else str(val)

def _age(dob):
    if not dob:
        return '—'
    today = date.today()
    return str(today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day)))

def _p(text, style):
    return Paragraph(text, style)


# ── Shared paragraph styles ───────────────────────────────────────────────────
def _styles():
    s = {}
    s['label'] = ParagraphStyle('lbl', fontSize=7, fontName='Helvetica-Bold',
                                 textColor=GRAY_500, leading=9)
    s['value'] = ParagraphStyle('val', fontSize=9, fontName='Helvetica',
                                 textColor=GRAY_800, leading=12, spaceBefore=1)
    s['sec_title'] = ParagraphStyle('st', fontSize=13, fontName='Helvetica-Bold',
                                     textColor=RED_MID, leading=17, spaceAfter=4)
    s['sec_sub']   = ParagraphStyle('ss', fontSize=8, fontName='Helvetica',
                                     textColor=GRAY_600, leading=11)
    s['card_title']= ParagraphStyle('ct', fontSize=10, fontName='Helvetica-Bold',
                                     textColor=RED_MID, leading=14, spaceAfter=6)
    s['sub_label'] = ParagraphStyle('sl', fontSize=8, fontName='Helvetica-Bold',
                                     textColor=GRAY_700, leading=11, spaceAfter=4)
    s['normal']    = ParagraphStyle('nm', fontSize=9, fontName='Helvetica',
                                     textColor=GRAY_700, leading=12)
    return s


# ── One labeled field (label on top, value below with underline) ──────────────
# Mirrors: <label class="text-xs text-gray-500"> + <input>
def _field(label, value, w, S):
    inner = Table(
        [[_p(label, S['label'])],
         [_p(_v(value), S['value'])]],
        colWidths=[w]
    )
    inner.setStyle(TableStyle([
        ('TOPPADDING',    (0, 0), (-1, -1), 1),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 1),
        ('LEFTPADDING',   (0, 0), (-1, -1), 0),
        ('RIGHTPADDING',  (0, 0), (-1, -1), 0),
        ('LINEBELOW',     (0, 1), (0, 1),   0.5, GRAY_300),
    ]))
    return inner


# ── N-column grid of labeled fields ──────────────────────────────────────────
# Mirrors: <div class="grid grid-cols-2 gap-4">
def _grid(fields, pw, cols=2, S=None):
    """fields = [(label, value), ...]"""
    if S is None:
        S = _styles()
    col_w = pw / cols
    # pad to full rows
    while len(fields) % cols:
        fields.append(('', ''))

    data = []
    for i in range(0, len(fields), cols):
        row = [_field(lbl, val, col_w - 10, S) for lbl, val in fields[i:i+cols]]
        data.append(row)

    t = Table(data, colWidths=[col_w] * cols)
    t.setStyle(TableStyle([
        ('VALIGN',        (0, 0), (-1, -1), 'TOP'),
        ('TOPPADDING',    (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('LEFTPADDING',   (0, 0), (-1, -1), 5),
        ('RIGHTPADDING',  (0, 0), (-1, -1), 5),
    ]))
    return t


# ── White sub-card with border ────────────────────────────────────────────────
# Mirrors: <div class="bg-gray-50 rounded-lg border border-gray-200 p-4">
def _white_card(title, content_rows, pw, S):
    """content_rows = list of flowable-like tables or paragraphs"""
    rows = []
    if title:
        rows.append([_p(f'<b>{title}</b>', S['sub_label'])])
    for c in content_rows:
        rows.append([c])

    inner = Table(rows, colWidths=[pw - 24])
    inner.setStyle(TableStyle([
        ('TOPPADDING',    (0, 0), (-1, -1), 0),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
        ('LEFTPADDING',   (0, 0), (-1, -1), 0),
        ('RIGHTPADDING',  (0, 0), (-1, -1), 0),
    ]))
    outer = Table([[inner]], colWidths=[pw])
    outer.setStyle(TableStyle([
        ('BACKGROUND',    (0, 0), (-1, -1), GRAY_50),
        ('BOX',           (0, 0), (-1, -1), 0.75, GRAY_200),
        ('TOPPADDING',    (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
        ('LEFTPADDING',   (0, 0), (-1, -1), 12),
        ('RIGHTPADDING',  (0, 0), (-1, -1), 12),
    ]))
    return outer


# ── Section card: red left border + bg-gray-50 ────────────────────────────────
# Mirrors: <div class="bg-gray-50 border-l-4 border-primary rounded-lg p-6">
def _section_card(title, subtitle, body_rows, pw, S):
    rows = []
    rows.append([_p(f'<font color="#991b1b"><b>{title}</b></font>', S['sec_title'])])
    if subtitle:
        rows.append([_p(subtitle, S['sec_sub'])])
        rows.append([Spacer(1, 6)])
    for r in body_rows:
        rows.append([r])

    inner = Table(rows, colWidths=[pw - 22])
    inner.setStyle(TableStyle([
        ('TOPPADDING',    (0, 0), (-1, -1), 0),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('LEFTPADDING',   (0, 0), (-1, -1), 0),
        ('RIGHTPADDING',  (0, 0), (-1, -1), 0),
    ]))
    outer = Table([[inner]], colWidths=[pw])
    outer.setStyle(TableStyle([
        ('BACKGROUND',    (0, 0), (-1, -1), GRAY_50),
        ('LINEBEFORE',    (0, 0), (0, -1),  4, RED_MID),
        ('TOPPADDING',    (0, 0), (-1, -1), 12),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
        ('LEFTPADDING',   (0, 0), (-1, -1), 16),
        ('RIGHTPADDING',  (0, 0), (-1, -1), 12),
    ]))
    return outer


# ── Blue guardian highlight box ───────────────────────────────────────────────
# Mirrors: <div class="bg-blue-50 border-2 border-blue-300 rounded-lg p-6">
def _guardian_box(label_text, pw, S):
    t = Table([[
        _p('<font color="#1d4ed8"><b>👤  WHO IS THE STUDENT\'S OFFICIAL GUARDIAN?</b></font>',
           ParagraphStyle('gb', fontSize=9, fontName='Helvetica-Bold',
                          textColor=BLUE_600, leading=13)),
        _p(f'<b>{label_text}</b>',
           ParagraphStyle('gbv', fontSize=10, fontName='Helvetica-Bold',
                          textColor=GRAY_800, leading=13, alignment=TA_RIGHT)),
    ]], colWidths=[pw * 0.65, pw * 0.35])
    t.setStyle(TableStyle([
        ('BACKGROUND',    (0, 0), (-1, -1), BLUE_50),
        ('BOX',           (0, 0), (-1, -1), 1.5, BLUE_300),
        ('VALIGN',        (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING',    (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
        ('LEFTPADDING',   (0, 0), (-1, -1), 12),
        ('RIGHTPADDING',  (0, 0), (-1, -1), 12),
    ]))
    return t


# ── Main view ─────────────────────────────────────────────────────────────────
def generate_application_pdf(request):
    lrn = request.GET.get('lrn') or request.session.get('download_lrn', '')
    if not lrn:
        return HttpResponse("Student LRN not found. Please contact the school registrar.",
                            status=400, content_type='text/plain')
    try:
        student = Student.objects.select_related(
            'school_year', 'student_data',
            'family_data', 'family_data__father',
            'family_data__mother', 'family_data__other_guardian',
            'program_selection',
        ).get(lrn=lrn)
    except Student.DoesNotExist:
        return HttpResponse(f"No enrollment record found for LRN {lrn}.",
                            status=404, content_type='text/plain')

    sd = getattr(student, 'student_data', None)
    fd = getattr(student, 'family_data', None)
    ps = getattr(student, 'program_selection', None)
    sy = student.school_year
    sy_label = sy.year_label if sy else 'N/A'

    buf = io.BytesIO()
    PW  = A4[0] - 1.2 * inch   # usable page width  ≈ 467 pt
    S   = _styles()

    doc = SimpleDocTemplate(
        buf, pagesize=A4,
        rightMargin=0.6*inch, leftMargin=0.6*inch,
        topMargin=0.6*inch,   bottomMargin=0.6*inch,
        title=f"Enrollment Application — {lrn}",
    )
    elems = []

    # ══════════════════════════════════════════════════════════════════════════
    # PAGE HEADER  (matches the sticky <header> in both HTML pages)
    # ══════════════════════════════════════════════════════════════════════════
    school_row = Table([[
        _p('<b><font size="14">Zamboanga National High School West</font></b><br/>'
           '<font size="7.5" color="#4b5563">R.T. Lim Boulevard Zamboanga City, Philippines'
           '&nbsp;&nbsp;|&nbsp;&nbsp;School I.D: 303942</font>',
           ParagraphStyle('sh', alignment=TA_LEFT, leading=17)),
        _p(f'<font size="8" color="#4b5563">School Year {sy_label}</font>',
           ParagraphStyle('shr', alignment=TA_RIGHT, leading=12)),
    ]], colWidths=[PW * 0.65, PW * 0.35])
    school_row.setStyle(TableStyle([
        ('VALIGN',        (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING',    (0, 0), (-1, -1), 0),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('LINEBELOW',     (0, 0), (-1, 0),  1.5, GRAY_300),
    ]))
    elems.append(school_row)
    elems.append(Spacer(1, 8))

    # ── Title card  (border-t-4 border-red-900, centered, shadow) ─────────────
    # Mirrors: <div class="bg-white rounded-lg shadow-md p-6 border-t-4 border-red-900 text-center">
    title_card = Table([[
        _p('<font color="#7f1d1d" size="20"><b>ENROLLMENT APPLICATION FORM</b></font>',
           ParagraphStyle('tc', alignment=TA_CENTER, leading=26)),
    ], [
        _p(f'<font size="9" color="#374151">School Year {sy_label}</font>',
           ParagraphStyle('tcsub', alignment=TA_CENTER, leading=12)),
    ], [
        _p(f'<font size="7.5" color="#15803d"><b>✓ Enrollment Submitted</b></font>'
           f'<font size="7.5" color="#6b7280">'
           f'&nbsp;&nbsp;|&nbsp;&nbsp;Generated: {datetime.now().strftime("%B %d, %Y  %I:%M %p")}'
           f'</font>',
           ParagraphStyle('tcgen', alignment=TA_CENTER, leading=11)),
    ]], colWidths=[PW])
    title_card.setStyle(TableStyle([
        ('BACKGROUND',    (0, 0), (-1, -1), WHITE),
        ('LINEABOVE',     (0, 0), (-1, 0),  4, RED_900),
        ('BOX',           (0, 0), (-1, -1), 0.5, GRAY_200),
        ('TOPPADDING',    (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('LEFTPADDING',   (0, 0), (-1, -1), 12),
        ('RIGHTPADDING',  (0, 0), (-1, -1), 12),
    ]))
    elems.append(title_card)
    elems.append(Spacer(1, 12))

    # ══════════════════════════════════════════════════════════════════════════
    # A. STUDENT DATA FORM  (mirrors studentData.html)
    # ══════════════════════════════════════════════════════════════════════════
    if sd:
        mn        = f' {sd.middle_name}' if sd.middle_name else ''
        enroll    = sd.enrolling_as or []
        enroll_str = ', '.join(e.replace('_', ' ').title() for e in enroll) if enroll else '—'
        pwd_txt   = f"Yes — {_v(sd.sped_details)}"    if sd.is_sped            else 'No'
        work_txt  = f"Yes — {_v(sd.working_details)}" if sd.is_working_student else 'No'
        inner_pw  = PW - 22   # inside the section card

        # Top 4-field row: LRN, Enrolling As, PWD, Working Student
        top_grid = _grid([
            ('LRN Number',      _v(lrn)),
            ('Enrolling As',    enroll_str),
            ('PWD / SPED',      pwd_txt),
            ('Working Student', work_txt),
        ], inner_pw, cols=2, S=S)

        # NAME sub-card (3-column: Last / First / Middle)
        name_grid = _grid([
            ('Last Name',   _v(sd.last_name)),
            ('First Name',  _v(sd.first_name)),
            ('Middle Name', _v(sd.middle_name)),
        ], inner_pw - 24, cols=3, S=S)
        name_card = _white_card('NAME', [name_grid], inner_pw, S)

        # Personal details 3-column grid
        detail_grid = _grid([
            ('Gender',         _v(sd.gender).title() if sd.gender else '—'),
            ('Date of Birth',  _fmt_date(sd.date_of_birth)),
            ('Age',            _age(sd.date_of_birth)),
            ('Place of Birth', _v(sd.place_of_birth)),
            ('Religion',       _v(sd.religion)),
            ('Mother Tongue',  _v(sd.dialect_spoken)),
            ('Ethnic Tribe',   _v(sd.ethnic_tribe)),
            ('Address',        _v(sd.address)),
        ], inner_pw, cols=2, S=S)

        # Previous School sub-card
        school_grid = _grid([
            ('Name of Last School Attended',  _v(sd.last_school_attended)),
            ('Previous Grade and Section',    _v(sd.previous_grade_section)),
            ('School Year Last Attended',     _v(sd.last_school_year)),
        ], inner_pw - 24, cols=2, S=S)
        school_card = _white_card('Previous School Information', [school_grid], inner_pw, S)

        body_rows = [
            top_grid,
            Spacer(1, 8),
            name_card,
            Spacer(1, 8),
            detail_grid,
            Spacer(1, 8),
            school_card,
        ]
        elems.append(_section_card(
            "A. Student's Information Data",
            "* Please fill in the complete and correct details",
            body_rows, PW, S
        ))
    else:
        elems.append(_p('<i>Student data not available.</i>',
                        ParagraphStyle('na', fontSize=9)))

    elems.append(Spacer(1, 12))

    # ══════════════════════════════════════════════════════════════════════════
    # B. FAMILY DATA FORM  (mirrors familyData.html)
    # ══════════════════════════════════════════════════════════════════════════
    if fd:
        inner_pw = PW - 22

        def _parent_card(title, p):
            if p:
                g = _grid([
                    ('Last Name',      _v(p.family_name)),
                    ('First Name',     _v(p.first_name)),
                    ('Middle Name',    _v(p.middle_name)),
                    ('Date of Birth',  _fmt_date(p.date_of_birth)),
                    ('Occupation',     _v(p.occupation)),
                    ('Contact Number', _v(p.contact_number)),
                    ('Complete Home Address', _v(p.address)),
                    ('Email Address',  _v(p.email)),
                ], inner_pw - 24, cols=2, S=S)
            else:
                g = _p('<i>(No information provided)</i>',
                       ParagraphStyle('npi', fontSize=8, textColor=GRAY_500))
            return _white_card(title, [g], inner_pw, S)

        guardian_label = fd.get_official_guardian_type_display() or '—'
        guardian_box   = _guardian_box(guardian_label, inner_pw, S)

        body_rows = [
            _parent_card("FATHER'S INFORMATION:", fd.father),
            Spacer(1, 8),
            _parent_card("MOTHER'S INFORMATION:", fd.mother),
            Spacer(1, 8),
            guardian_box,
        ]

        # Other guardian block
        if fd.official_guardian_type == 'other' and fd.other_guardian:
            og = fd.other_guardian
            og_grid = _grid([
                ('Last Name',                   _v(og.family_name)),
                ('First Name',                  _v(og.first_name)),
                ('Middle Name',                 _v(og.middle_name)),
                ('Date of Birth',               _fmt_date(og.date_of_birth)),
                ('Occupation',                  _v(og.occupation)),
                ('Relationship with the student', _v(og.relationship_to_student)),
                ('Contact Number',              _v(og.contact_number)),
                ('Email Address',               _v(og.email)),
                ('Complete Home Address',       _v(og.address)),
            ], inner_pw - 24, cols=2, S=S)
            og_card = _white_card('OTHER GUARDIAN INFORMATION:', [og_grid], inner_pw, S)
            body_rows += [Spacer(1, 8), og_card]

        elems.append(_section_card(
            "B. Family Information Data",
            "(Please fill in the complete and correct details)",
            body_rows, PW, S
        ))
    else:
        elems.append(_p('<i>Family data not available.</i>',
                        ParagraphStyle('na2', fontSize=9)))

    elems.append(Spacer(1, 12))

    # ══════════════════════════════════════════════════════════════════════════
    # C. PROGRAM SELECTION
    # ══════════════════════════════════════════════════════════════════════════
    if ps and ps.selected_program_code:
        track = _v(ps.regular_track)
        prog  = ps.selected_program_code + (f' ({track})' if track != '—' else '')
        inner_pw = PW - 22
        prog_grid = _grid([
            ('Selected Program', prog),
            ('School Year',      sy_label),
            ('Confirmed On',     _fmt_date(ps.created_at)),
            ('Status',           'Submitted — Pending Review'),
        ], inner_pw, cols=2, S=S)
        elems.append(_section_card("C. Program Selection", None, [prog_grid], PW, S))

    # ══════════════════════════════════════════════════════════════════════════
    # SIGNATURE STRIP
    # ══════════════════════════════════════════════════════════════════════════
    elems += [
        Spacer(1, 20),
        HRFlowable(width='100%', thickness=0.6, color=GRAY_300, spaceAfter=14),
    ]
    sig = ParagraphStyle('sig', alignment=TA_CENTER, fontSize=8, leading=12,
                          textColor=GRAY_700)
    sig_tbl = Table([[
        _p('<br/><br/><br/>________________________________<br/>'
           f"<b>Student's Signature over Printed Name</b><br/>"
           f'<font size="7" color="#6b7280">LRN: {lrn}</font>', sig),
        _p('<br/><br/><br/>________________________________<br/>'
           "<b>Parent / Guardian's Signature</b><br/>"
           '<font size="7" color="#6b7280">Relationship to student</font>', sig),
        _p('<br/><br/><br/>________________________________<br/>'
           '<b>Received by (Registrar)</b><br/>'
           '<font size="7" color="#6b7280">Date received: ______________</font>', sig),
    ]], colWidths=[PW / 3] * 3)
    sig_tbl.setStyle(TableStyle([
        ('ALIGN',         (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN',        (0, 0), (-1, -1), 'BOTTOM'),
        ('TOPPADDING',    (0, 0), (-1, -1), 0),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
    ]))
    elems.append(sig_tbl)
    elems.append(Spacer(1, 10))
    elems.append(_p(
        f'<font size="6.5" color="#9ca3af">Auto-generated by the ZNHS West Enrollment System. '
        f'For inquiries, contact the school registrar.&nbsp;|&nbsp;LRN: {lrn}</font>',
        ParagraphStyle('ftr', alignment=TA_CENTER)
    ))

    doc.build(elems)
    pdf_bytes = buf.getvalue()
    buf.close()

    response = HttpResponse(pdf_bytes, content_type='application/pdf')
    response['Content-Disposition'] = (
        f'attachment; filename="Enrollment_Application_{lrn}_{datetime.now().strftime("%Y%m%d")}.pdf"'
    )
    return response


def download_application_form(request):
    return generate_application_pdf(request)