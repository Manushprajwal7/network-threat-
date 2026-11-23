import os
import docx
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import qn

def set_cell_border(cell, **kwargs):
    """Booktabs style borders for docx table cells."""
    tcPr = cell._tc.get_or_add_tcPr()
    tcBorders = tcPr.first_child_found_in("w:tcBorders")
    if tcBorders is None:
        tcBorders = OxmlElement('w:tcBorders')
        tcPr.append(tcBorders)
    for edge in ('top', 'left', 'bottom', 'right', 'insideH', 'insideV'):
        edge_data = kwargs.get(edge)
        if edge_data:
            tag = 'w:{}'.format(edge)
            element = tcBorders.find(qn(tag))
            if element is None:
                element = OxmlElement(tag)
                tcBorders.append(element)
            for key in ["sz", "val", "color", "space", "shadow"]:
                if key in edge_data:
                    element.set(qn('w:{}'.format(key)), str(edge_data[key]))
        else:
            tag = 'w:{}'.format(edge)
            element = tcBorders.find(qn(tag))
            if element is not None:
                element.set(qn('w:val'), 'none')

doc = docx.Document()

def add_algorithm_box(doc, algo_num, title, inputs, outputs, lines, complexity, footnote):
    table = doc.add_table(rows=4, cols=1)
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.autofit = False
    table.columns[0].width = Inches(7.0)

    # CantSplit on all rows
    for r in table.rows:
        trPr = r._tr.get_or_add_trPr()
        trPr.append(parse_xml(r'<w:cantSplit xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"/>'))

    # Row 0: Title
    cell_0 = table.cell(0, 0)
    set_cell_border(cell_0,
                    top={"sz": 14, "val": "single", "color": "000000"},
                    bottom={"sz": 8, "val": "single", "color": "000000"})
    p_title = cell_0.paragraphs[0]
    p_title.paragraph_format.space_before = Pt(3)
    p_title.paragraph_format.space_after = Pt(3)
    p_title.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.LEFT
    r_tag = p_title.add_run(f"Algorithm {algo_num}: ")
    r_tag.font.name = 'Times New Roman'
    r_tag.font.size = Pt(10)
    r_tag.font.bold = True
    r_title = p_title.add_run(title)
    r_title.font.name = 'Times New Roman'
    r_title.font.size = Pt(10)
    r_title.font.bold = True

    # Row 1: Inputs & Outputs
    cell_1 = table.cell(1, 0)
    set_cell_border(cell_1,
                    bottom={"sz": 6, "val": "single", "color": "000000"})
    
    # Input block
    for idx, inp in enumerate(inputs):
        p_inp = cell_1.paragraphs[0] if idx == 0 else cell_1.add_paragraph()
        p_inp.paragraph_format.space_before = Pt(1)
        p_inp.paragraph_format.space_after = Pt(1)
        p_inp.paragraph_format.line_spacing = 1.05
        p_inp.paragraph_format.left_indent = Inches(0.2)
        if idx == 0:
            r_req = p_inp.add_run("Require: ")
            r_req.font.name = 'Times New Roman'
            r_req.font.size = Pt(9)
            r_req.font.bold = True
        else:
            p_inp.paragraph_format.left_indent = Inches(0.7)
        r_txt = p_inp.add_run(inp)
        r_txt.font.name = 'Times New Roman'
        r_txt.font.size = Pt(9)

    # Output block
    for idx, out in enumerate(outputs):
        p_out = cell_1.add_paragraph()
        p_out.paragraph_format.space_before = Pt(1)
        p_out.paragraph_format.space_after = Pt(1)
        p_out.paragraph_format.line_spacing = 1.05
        p_out.paragraph_format.left_indent = Inches(0.2)
        if idx == 0:
            r_ens = p_out.add_run("Ensure: ")
            r_ens.font.name = 'Times New Roman'
            r_ens.font.size = Pt(9)
            r_ens.font.bold = True
        else:
            p_out.paragraph_format.left_indent = Inches(0.7)
        r_txt = p_out.add_run(out)
        r_txt.font.name = 'Times New Roman'
        r_txt.font.size = Pt(9)

    # Row 2: Algorithm Body
    cell_2 = table.cell(2, 0)
    set_cell_border(cell_2,
                    bottom={"sz": 6, "val": "single", "color": "000000"})
    
    # Format lines
    keywords = {
        "IF", "THEN", "ELSE", "RETURN", "FOR", "DO", "REQUIRE", "ENSURE",
        "AND", "OR", "NOT", "CONTINUE", "RAISE", "IS", "NULL", "CLIP",
        "MATCH_CLASS_LABEL", "FIT_ISOLATION_FOREST", "FIT_CALIBRATION",
        "SCORE", "COMBINATIONS_WITH_REPLACEMENT", "IS_SEVERITY_MONOTONIC",
        "BENIGN_BLOCK_RATE", "COMPUTE_EXPECTED_COST", "ARGMIN", "COMPUTE_RANK"
    }
    
    for l_idx, line in enumerate(lines):
        p_line = cell_2.paragraphs[0] if l_idx == 0 else cell_2.add_paragraph()
        p_line.paragraph_format.space_before = Pt(0.5)
        p_line.paragraph_format.space_after = Pt(0.5)
        p_line.paragraph_format.line_spacing = 1.05
        p_line.paragraph_format.left_indent = Inches(0.2)
        
        # Split line number e.g. " 1:  "
        parts = line.split(":", 1)
        if len(parts) == 2:
            num_part = parts[0].strip() + ": "
            code_part = parts[1]
            r_num = p_line.add_run(f"{num_part:>4s}")
            r_num.font.name = 'Consolas'
            r_num.font.size = Pt(8.5)
            r_num.font.bold = True
            r_num.font.color.rgb = RGBColor(60, 60, 60)
            
            # Tokenize code_part
            # Match tokens: words or symbols
            tokens = re.split(r'(\b\w+\b)', code_part)
            for tok in tokens:
                if not tok:
                    continue
                r_tok = p_line.add_run(tok)
                r_tok.font.name = 'Consolas'
                r_tok.font.size = Pt(8.5)
                if tok in keywords:
                    r_tok.font.bold = True
                    r_tok.font.color.rgb = RGBColor(0, 0, 130)
                else:
                    r_tok.font.color.rgb = RGBColor(20, 20, 20)
        else:
            r = p_line.add_run(line)
            r.font.name = 'Consolas'
            r.font.size = Pt(8.5)

    # Row 3: Complexity & Footnote
    cell_3 = table.cell(3, 0)
    set_cell_border(cell_3,
                    bottom={"sz": 14, "val": "single", "color": "000000"})
    p_comp = cell_3.paragraphs[0]
    p_comp.paragraph_format.space_before = Pt(2)
    p_comp.paragraph_format.space_after = Pt(1)
    p_comp.paragraph_format.line_spacing = 1.05
    p_comp.paragraph_format.left_indent = Inches(0.2)
    
    r_cb = p_comp.add_run("Complexity: ")
    r_cb.font.name = 'Times New Roman'
    r_cb.font.size = Pt(8.5)
    r_cb.font.bold = True
    r_cbody = p_comp.add_run(f"Time: {complexity['time']}; Space: {complexity['space']}")
    r_cbody.font.name = 'Times New Roman'
    r_cbody.font.size = Pt(8.5)
    r_cbody.font.italic = True
    
    p_fn = cell_3.add_paragraph()
    p_fn.paragraph_format.space_before = Pt(1)
    p_fn.paragraph_format.space_after = Pt(2)
    p_fn.paragraph_format.line_spacing = 1.05
    p_fn.paragraph_format.left_indent = Inches(0.2)
    
    r_fb = p_fn.add_run("Source: ")
    r_fb.font.name = 'Times New Roman'
    r_fb.font.size = Pt(8.0)
    r_fb.font.bold = True
    r_fbody = p_fn.add_run(footnote)
    r_fbody.font.name = 'Times New Roman'
    r_fbody.font.size = Pt(8.0)
    r_fbody.font.color.rgb = RGBColor(70, 70, 70)
    
    p_post = doc.add_paragraph()
    p_post.paragraph_format.space_after = Pt(4)

lines1 = [
    " 1:  S <- 0",
    " 2:  IF a >= tau_a THEN S <- S + 1",
    " 3:  IF T <= tau_T THEN S <- S + 1",
    " 4:  IF c >= tau_c AND y_hat != 1 THEN S <- S + 1",
    " 5:  IF R >= tau_R THEN S <- S + 1",
    " 6:  IF S = 0 THEN RETURN L_0",
    " 7:  IF S = 1 THEN RETURN L_1",
    " 8:  IF S = 2 THEN RETURN L_2",
    " 9:  IF S >= 3 AND T > 20.0 THEN RETURN L_3",
    "10:  IF S >= 3 AND T <= 20.0 AND F >= 2 AND R < 0.75 THEN RETURN L_4",
    "11:  IF S >= 3 AND T <= 20.0 AND F >= 2 AND R >= 0.75 THEN RETURN L_5",
    "12:  RETURN L_3"
]

import re
add_algorithm_box(
    doc,
    algo_num=1,
    title="Cumulative-Evidence Security Posture Assignment",
    inputs=[
        "a ∈ [0, 1]: calibrated anomaly score; c ∈ [0, 1]: classification confidence",
        "y_hat ∈ Y: predicted traffic class (y_hat ≠ 1 denotes attack)",
        "T ∈ [0, 100]: dynamic trust score; R ∈ [0, 1]: topological risk score (τ_e)",
        "F ∈ N: distinct non-benign attack families detected in entity window",
        "θ = {τ_a, τ_T, τ_c, τ_R}: operational thresholds (0.90, 60.0, 0.95, 0.42)"
    ],
    outputs=[
        "ℓ ∈ {L_0, L_1, L_2, L_3, L_4, L_5}: assigned operational security posture level"
    ],
    lines=lines1,
    complexity={
        "time": "O(1) per flow observation",
        "space": "O(1) auxiliary state storage"
    },
    footnote="backend/api/security_level_manager.py, lines 40–120. Snapshot at paper2_baseline_if_contaminated/."
)

doc.save("scratch/test_algo.docx")
print("Saved scratch/test_algo.docx successfully")
