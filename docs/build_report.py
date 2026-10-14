#!/usr/bin/env python3
"""生成《液体表面张力系数的测定》实验报告第一至第四部分。"""

import re

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_LINE_SPACING
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt


def set_run_font(run, size=12, bold=False, cn="宋体", en="Times New Roman"):
    run.bold = bold
    run.font.size = Pt(size)
    run.font.name = en
    rPr = run._element.get_or_add_rPr()
    rFonts = rPr.find(qn("w:rFonts"))
    if rFonts is None:
        rFonts = OxmlElement("w:rFonts")
        rPr.append(rFonts)
    rFonts.set(qn("w:ascii"), en)
    rFonts.set(qn("w:hAnsi"), en)
    rFonts.set(qn("w:cs"), en)
    rFonts.set(qn("w:eastAsia"), cn)


def set_paragraph_format(paragraph, before=0, after=0, line=1.5, indent=True, align="left"):
    fmt = paragraph.paragraph_format
    fmt.space_before = Pt(before)
    fmt.space_after = Pt(after)
    fmt.line_spacing = line
    fmt.line_spacing_rule = WD_LINE_SPACING.MULTIPLE
    if indent:
        fmt.first_line_indent = Pt(24)
    else:
        fmt.first_line_indent = Pt(0)
    if align == "center":
        paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
    elif align == "right":
        paragraph.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    else:
        paragraph.alignment = WD_ALIGN_PARAGRAPH.LEFT


_SUB = re.compile(r"_\{([^}]+)\}")


def write_marked(paragraph, text, size=12, bold=False, cn="宋体"):
    """把 F_{T}、U_{max} 这类标记写成 Word 下标。"""
    pos = 0
    for match in _SUB.finditer(text):
        if match.start() > pos:
            run = paragraph.add_run(text[pos:match.start()])
            set_run_font(run, size=size, bold=bold, cn=cn)
        sub = paragraph.add_run(match.group(1))
        set_run_font(sub, size=size, bold=bold, cn=cn)
        sub.font.subscript = True
        pos = match.end()
    if pos < len(text):
        run = paragraph.add_run(text[pos:])
        set_run_font(run, size=size, bold=bold, cn=cn)


def add_text(doc, text, size=12, bold=False, cn="宋体", before=0, after=0, indent=True, align="left"):
    p = doc.add_paragraph()
    set_paragraph_format(p, before=before, after=after, indent=indent, align=align)
    write_marked(p, text, size=size, bold=bold, cn=cn)
    return p


def add_mixed(doc, parts, before=0, after=0, indent=True, align="left", line=1.5):
    """parts: list of (text, size, bold, cn)."""
    p = doc.add_paragraph()
    set_paragraph_format(p, before=before, after=after, indent=indent, align=align, line=line)
    for text, size, bold, cn in parts:
        run = p.add_run(text)
        set_run_font(run, size=size, bold=bold, cn=cn)
    return p


def add_formula(doc, expr, number):
    p = doc.add_paragraph()
    set_paragraph_format(p, before=3, after=3, indent=False, align="center")
    write_marked(p, expr + "      " + number, size=12)
    return p


def main():
    doc = Document()
    section = doc.sections[0]
    section.page_width = Cm(21.0)
    section.page_height = Cm(29.7)
    section.top_margin = Cm(2.54)
    section.bottom_margin = Cm(2.54)
    section.left_margin = Cm(2.8)
    section.right_margin = Cm(2.8)

    normal = doc.styles["Normal"]
    normal.font.name = "Times New Roman"
    normal.font.size = Pt(12)
    rPr = normal.element.get_or_add_rPr()
    rFonts = rPr.find(qn("w:rFonts"))
    if rFonts is None:
        rFonts = OxmlElement("w:rFonts")
        rPr.append(rFonts)
    rFonts.set(qn("w:ascii"), "Times New Roman")
    rFonts.set(qn("w:hAnsi"), "Times New Roman")
    rFonts.set(qn("w:eastAsia"), "宋体")

    add_text(doc, "北京师范大学文理学院物理系", size=16, bold=True, cn="黑体", indent=False, align="center", before=18, after=6)
    add_text(doc, "物理实验报告", size=22, bold=True, cn="黑体", indent=False, align="center", before=6, after=18)

    cover_lines = [
        "课程名称：大学物理实验 B",
        "实验项目：液体表面张力系数的测定",
        "学生年级：                    专业：",
        "学生姓名：                    学号：",
        "指导教师：                    实验教师：",
        "实验日期：        年      月      日",
    ]
    for line in cover_lines:
        add_text(doc, line, size=14, indent=False, align="center", before=6, after=6)

    add_text(
        doc,
        "第一至第四部分",
        size=12,
        indent=False,
        align="center",
        before=18,
        after=6,
    )

    # ---------- 一 ----------
    add_text(doc, "一、实验目的", size=14, bold=True, cn="黑体", indent=False, before=16, after=6)
    purposes = [
        "1. 学习并掌握用拉脱法测量液体表面张力系数的实验原理和测量方法。",
        "2. 学习并掌握硅压阻力敏传感器的定标方法，确定输出电压与所受拉力之间的对应关系。",
        "3. 测量蒸馏水在室温和不同温度下的表面张力系数，以及肥皂水的表面张力系数，了解温度和液体种类对表面张力系数的影响。",
    ]
    for item in purposes:
        add_text(doc, item, before=2, after=2)

    # ---------- 二 ----------
    add_text(doc, "二、实验原理", size=14, bold=True, cn="黑体", indent=False, before=14, after=6)
    add_text(doc, "1. 原理简述", size=12, bold=True, cn="黑体", indent=False, before=6, after=4)

    add_text(
        doc,
        "液体分子之间存在相互吸引力。在液体内部，一个分子受到周围分子的吸引力来自各个方向，平均合力为零。位于表面层的分子，其外侧是气体，吸引力主要来自液体内部，所受合力指向液体内侧，因此液面有向内收缩的趋势。这种沿着液面、使液面收缩的力称为表面张力。",
    )
    add_text(
        doc,
        "表面张力的大小与液面分界线的长度成正比，比例系数 α 称为液体的表面张力系数，单位为 N/m。它表示作用在单位长度分界线上的表面张力。",
    )
    add_text(
        doc,
        "用一个已知周长的金属环从待测液面拉脱，由拉脱时所需要的力求出表面张力系数，这种方法称为拉脱法。环在脱离液面时，液膜同时附着在环的外沿和内沿，接触线长度等于外圆周与内圆周之和。在一级近似下，脱离力 F 满足",
    )
    add_formula(doc, "F = α π (D₁ + D₂)", "(1)")
    add_text(doc, "式中 D₁、D₂ 分别为金属环的外径和内径，α 为待测液体的表面张力系数。")
    add_text(
        doc,
        "实际上，拉脱过程中表面张力的大小和方向都在变化。液膜被拉断以前，金属环受到四个力的作用：竖直向上的拉力 F_{T}、金属环的重力 F_{G}、液体的表面张力 F，以及被拉出液膜的重力 F_{W}。受力平衡可以写成",
    )
    add_formula(doc, "F_{T} = F_{G} + F cosθ + F_{W}", "(2)")
    add_text(doc, "式中 θ 为表面张力 F 与竖直方向的夹角。液膜重力近似为")
    add_formula(doc, "F_{W} = π (D₁² − D₂²) h ρ g / 4", "(3)")
    add_text(
        doc,
        "其中 h 为液膜相对液面被拉出的高度，ρ 为液体密度，g 为重力加速度。h < 0 表示金属环仍处于液面以下，这一项此时表现为浮力。",
    )
    add_text(
        doc,
        "实验中用硅压阻力敏传感器测量微小拉力。传感器由弹性梁和贴在梁上的传感芯片组成，芯片是由四个硅扩散力敏电阻集成的非平衡电桥。悬臂梁受力发生形变时，电桥失去平衡并输出电压。输出电压与横梁所受拉力成正比：",
    )
    add_formula(doc, "U = K · F_{T}", "(4)")
    add_text(doc, "式中 K 为力敏传感器的灵敏度，单位取 mV/N；U 为数字电压表读数。")
    add_text(
        doc,
        "当拉力达到最大时，F_{T} = F_{T,max}，表面张力沿竖直方向，θ = 0，传感器输出电压也达到最大值 U = U_{max}。由式 (2) 得",
    )
    add_formula(doc, "F_{T,max} = F_{G} + F + F_{W}", "(5)")
    add_text(
        doc,
        "液膜拉断以后，表面张力和液膜重力都消失，电压读数记为 U₂，此时金属环所受的力 F₂ = F_{G}。因此",
    )
    add_formula(doc, "F_{T,max} − F₂ = F + F_{W}", "(6)")
    add_text(
        doc,
        "把式 (4) 代入，得到 F_{T,max} − F₂ = (U_{max} − U₂) / K。再联立式 (1)、(3) 和式 (6)，并记电压为 U_{max} 时液膜高度为 h_{max}，可得",
    )
    add_formula(
        doc,
        "α = [(U_{max} − U₂)/K − π(D₁² − D₂²)h_{max} ρg/4] / [π(D₁ + D₂)]",
        "(7)",
    )
    add_text(
        doc,
        "式 (7) 中 π (D₁² − D₂²) h_{max} ρ g / 4 是液膜重力带来的修正项。讲义指出，经过多次实验检验，这一项可以忽略。本实验计算表面张力系数时采用",
    )
    add_formula(doc, "α = (U_{max} − U₂) / [ π K (D₁ + D₂) ]", "(8)")
    add_text(
        doc,
        "因此需要先测定灵敏度 K 和金属环的内外径，再在拉膜过程中读出液膜拉断前的电压极大值 U_{max} 和拉断后的电压 U₂。",
    )
    add_text(
        doc,
        "定标时，在砝码盘上依次加上质量已知的砝码。砝码产生的拉力为 F = mg，其中取 g = 9.8 m/s²。测出各拉力对应的输出电压，用最小二乘法对 U–F 数据作直线拟合，直线斜率就是灵敏度 K。拟合关系为",
    )
    add_formula(doc, "U = K F + b", "(9)")
    add_text(
        doc,
        "式中 b 为截距。若传感器线性良好且定标前已将空盘拉力置零，截距应接近零，输出电压与拉力成正比。",
    )

    add_text(doc, "2. 预习思考题", size=12, bold=True, cn="黑体", indent=False, before=10, after=4)

    add_text(doc, "（1）简述液体表面张力产生的原因。", bold=True, before=4, after=2)
    add_text(
        doc,
        "液体分子之间距离较近，存在短程吸引力。液体内部的分子四周都被同类分子包围，各个方向的分子力互相抵消，合力为零。表面层分子的外侧是蒸气或空气，分子数密度远小于液体内部，所以表面层分子受到的吸引力主要来自液面以内，合力指向液体内部。",
    )
    add_text(
        doc,
        "把一个分子从液体内部移到表面，需要克服内部分子的吸引做功，因此表面层具有额外的表面自由能。在一定温度下，系统趋向于使表面自由能最小，液面面积也就趋向于缩小。宏观上，这种使液面收缩的切向力就是表面张力。对气液界面，表面张力系数在数值上等于单位面积的表面自由能。",
    )

    add_text(doc, "（2）液体表面张力系数与哪些因素有关？", bold=True, before=6, after=2)
    add_text(doc, "表面张力系数 α 是液体的表面性质，主要与下列因素有关。")
    add_text(
        doc,
        "① 液体种类。分子间作用力越强，把分子留在表面所需要的能量越高，α 越大。室温下蒸馏水的 α 约为 7×10⁻² N/m，酒精、乙醚、丙酮等有机液体的 α 明显更小。",
    )
    add_text(
        doc,
        "② 温度。温度升高时，分子热运动加剧，分子间平均距离增大，同时气液两相的密度差减小，α 随之减小。附表给出，纯水从 10 ℃ 升到 45 ℃ 时，α 约从 0.07422 N/m 降到 0.06874 N/m。温度达到临界温度时，气液界面消失，α 趋于零。",
    )
    add_text(
        doc,
        "③ 杂质和溶质。肥皂、洗涤剂等表面活性物质容易富集在液面，会显著降低 α；某些无机盐则可能使 α 略有升高。液体被污染后，测得的表面张力系数会偏离纯液体的数值，所以实验要用洁净蒸馏水，并保持吊环清洁。",
    )
    add_text(
        doc,
        "④ 溶液浓度。肥皂水等溶液的 α 还随溶质浓度变化，浓度不同，表面层的组成也不同。",
    )
    add_text(
        doc,
        "在本实验的大气压条件下，液面上方气体的种类和压强对 α 也有影响，但远小于温度和液体成分的影响。α 本身与吊环尺寸无关。D₁ 和 D₂ 只决定接触线的长度，从而影响力的大小，不应算作影响表面张力系数的因素。",
    )

    add_text(doc, "（3）如果吊环的水平程度差，会对测量结果产生怎样的影响？", bold=True, before=6, after=2)
    add_text(
        doc,
        "式 (1) 和式 (8) 有两个前提：吊环整圈同时脱离液面，接触线长度等于 π(D₁ + D₂)；拉力最大时表面张力沿竖直方向，即 θ = 0。这两个前提都要求吊环保持水平。",
    )
    add_text(
        doc,
        "吊环倾斜时，较低的一侧先离开液面，液膜不能沿整个圆周同时形成，并会在这一侧提前破裂。实际参与拉脱的接触线长度小于 π(D₁ + D₂)。环上各处的液膜高度和接触角也不一致，电压达到最大时并不是处处都满足 θ = 0，表面张力的竖直分力 F cosθ 小于 F。因此测得的 U_{max} 偏小，代入式 (8) 后得到的 α 系统性偏小。",
    )
    add_text(
        doc,
        "环面倾斜还会使左右受力不相等，吊环在拉膜过程中发生晃动，电压曲线出现波动，U_{max} 和 U₂ 都不稳定，测量的重复性变差。实验前必须用水平仪调节底座，使吊环平整；吊环如果变形，也不能继续使用。",
    )

    add_text(doc, "（4）定性分析一下传感器的电压值在拉膜过程中应如何变化？", bold=True, before=6, after=2)
    add_text(
        doc,
        "由式 (4)，传感器输出电压与它所受的拉力成正比。吊环挂到小钩上并把拉力置零以后，随着液面下降，电压应按下面的顺序变化。",
    )
    add_text(
        doc,
        "① 吊环下沿浸入液体时，液体对环有向上的浮力。传感器受到的向下拉力减小，输出电压下降，甚至出现负值。",
    )
    add_text(
        doc,
        "② 升降台下降，液面逐渐低于吊环，环排开的液体减少，浮力减小，电压从负值回升。",
    )
    add_text(
        doc,
        "③ 吊环与液面之间形成环形液膜后，表面张力沿液膜切向把吊环拉向液体。液膜被拉长时，表面张力与竖直方向的夹角 θ 逐渐减小，竖直分力 F cosθ 增大；同时被拉出液面的液膜具有一定重量。这两部分都使向下的拉力增大，所以电压持续上升。",
    )
    add_text(
        doc,
        "④ 液膜即将拉断时 θ ≈ 0，竖直分力达到最大，电压出现极大值 U_{max}。讲义中的式 (5) 对应的就是这个状态。",
    )
    add_text(
        doc,
        "⑤ 液膜破裂的瞬间，表面张力和液膜重力突然消失，拉力只剩下吊环自身的重力。由于挂环时已经置零，电压会骤降到接近零的 U₂，随后基本保持不变。若置零不彻底或环上残留液滴，U₂ 会略微偏离零。式 (8) 使用的是 U_{max} 与 U₂ 的差值，可以减去这一残余。",
    )
    add_text(
        doc,
        "因此，电压随液面下降位移的变化特征是：浸没时下降，开始拉膜后上升并达到一个峰值，液膜破裂后突然跌落。实验记录要取峰值作为 U_{max}，取跌落并稳定后的读数作为 U₂。",
    )

    # ---------- 三 ----------
    add_text(doc, "三、实验仪器", size=14, bold=True, cn="黑体", indent=False, before=14, after=6)
    instruments = [
        "1. DH4607J 型液体表面张力系数测定仪。主机采用 7 英寸电容触摸屏，面板有压力传感器接口、24 V 加热电源输出、光电门接口和 RS232 接口。",
        "2. 测试架，包括压力传感器及其固定座、均质金属吊环、加热器皿、升降台、光电门、三个水平调节螺丝和底座。",
        "3. 0.5 g 砝码 7 个、砝码盘、镊子、水平泡。定标时只能用镊子夹取砝码。",
        "4. 游标卡尺，用于测量吊环外径 D₁ 和内径 D₂；超声波清洗机，用于清洗吊环。",
        "5. 待测液体：蒸馏水、肥皂水。注射器可用于向加热器皿注液。",
    ]
    for item in instruments:
        add_text(doc, item, before=2, after=2)
    add_text(
        doc,
        "各部分的作用是：硅压阻力敏传感器把微小拉力转换成电压；光电门测量升降过程中的位移；加热器皿和温控表用来设定并稳定待测液体的温度。",
    )

    # ---------- 四 ----------
    add_text(doc, "四、实验步骤", size=14, bold=True, cn="黑体", indent=False, before=14, after=6)

    add_text(doc, "1. 开机与调平", bold=True, before=4, after=2)
    add_text(
        doc,
        "打开测定仪，预热不少于 10 分钟。把水平泡放在底座上，调节底座上的三个水平调节螺丝，直到气泡位于中心。吊环和吊绳出厂时已经调好，不要用力拉扯或折弯。",
    )

    add_text(doc, "2. 测量并清洁金属环", bold=True, before=6, after=2)
    add_text(
        doc,
        "用游标卡尺在不同方位测量金属环的外径 D₁ 和内径 D₂，取平均值，以减小圆环不圆带来的误差。然后用超声波清洗机清洗吊环，取出后晾干。环的表面要保持光洁，不能划伤或使其变形，否则液膜不易完整，拉脱力会偏小。",
    )

    add_text(doc, "3. 对硅压阻力敏传感器定标", bold=True, before=6, after=2)
    add_text(doc, "（1）在首页进入“传感器灵敏度测量实验”界面。把砝码盘挂在传感器悬臂梁端头的小钩上，按“置零”，将拉力值置零。")
    add_text(doc, "（2）打开参数设置，确认单个砝码质量为 0.5 g，重力系数取 g = 9.8 m/s²，保存后返回。")
    add_text(
        doc,
        "（3）用镊子向砝码盘依次加载 0.5 g、1.0 g、1.5 g、2.0 g、2.5 g、3.0 g 和 3.5 g 砝码。每增加一次，都要等砝码盘静止、电压示数稳定后，再按“录入”。同时把砝码质量、拉力 F = mg 和电压 U 记入表 1。不要用手取放砝码，以免砝码盘晃动，引入额外误差。录入错误时可用“撤销”去掉最近一次数据。",
    )
    add_text(
        doc,
        "（4）按“灵敏度”。仪器根据录入数据用一元线性回归计算灵敏度。报告中还要自行用最小二乘法对电压–拉力数据作直线拟合，斜率即为 K，单位 mV/N，并给出 K 的不确定度。",
    )

    add_text(doc, "4. 测量室温下蒸馏水的表面张力系数", bold=True, before=6, after=2)
    add_text(
        doc,
        "（1）回到首页，进入“液体表面张力系数测量实验”界面。把清洁、干燥的金属吊环挂在传感器小钩上，将拉力置零。按“阈值设置”，把阈值电压设为 0.01 mV。只有电压变化超过该阈值时，仪器才记录当前的拉力和位移。记录此时蒸馏水的温度。",
    )
    add_text(doc, "（2）打开加热器皿的盖子，注入适量洁净蒸馏水。水面不能太浅，以保证吊环下沿能够全部浸入。")
    add_text(
        doc,
        "（3）调节加热器皿下方的升降台，使器皿升到最高处。再调节压力传感器的高度或液面高度，让吊环下沿全部浸没在水中，然后将位移置零。",
    )
    add_text(
        doc,
        "（4）等实测温度与设定温度一致后，按“开始”。反向调节升降台，使液面缓慢下降。吊环和液面之间会形成一圈环形液膜，屏幕上显示出拉力随位移的变化。继续缓慢下降，直到液膜破裂，按“停止”。整个过程中吊环不能晃动，实验室也应保持安静，否则电压读数会波动。",
    )
    add_text(
        doc,
        "（5）点击曲线区域，切换到数据表格。在数据中找出液膜即将拉断前的电压极大值 U_{max}，以及液膜拉断后电压稳定下来的读数 U₂。",
    )
    add_text(doc, "（6）按以上步骤重复测量 6 次，将每次的 U_{max} 和 U₂ 记入表 2。若水被污染或使用时间较长，应更换蒸馏水后再测。")

    add_text(doc, "5. 测量不同温度下蒸馏水的表面张力系数", bold=True, before=6, after=2)
    add_text(
        doc,
        "用温控表依次把待测液体温度设定为 30 ℃、40 ℃、50 ℃ 和 60 ℃。每次都要等液体温度稳定，并且实测温度与设定温度一致以后，再按步骤 4 拉膜。每个温度记录一组 U_{max} 和 U₂，填入表 3。调节温度时不要触碰吊环。加热器皿温度较高，防止烫伤。",
    )

    add_text(doc, "6. 测量室温下肥皂水的表面张力系数", bold=True, before=6, after=2)
    add_text(
        doc,
        "倒出蒸馏水，清洗加热器皿和吊环并晾干，换入肥皂水，以免残留的水或前一种液体改变溶液浓度。在室温下按步骤 4 再次拉膜。报告表格要求测量 3 次，记录每次的 U_{max} 和 U₂。肥皂是表面活性物质，液膜较容易变形，下降液面时要比测蒸馏水更慢。",
    )

    add_text(doc, "7. 结束整理", bold=True, before=6, after=2)
    add_text(
        doc,
        "测量结束后倒掉液体，清洗吊环和器皿并晾干，关闭加热电源和仪器电源。测试架上其余部分多为金属部件，不要用其承重或玩耍，并注意用电安全。",
    )

    add_text(doc, "操作中还应注意以下几点。", before=6, after=2)
    notes = [
        "（1）定标加砝码必须使用镊子，轻拿轻放。",
        "（2）吊环表面的光洁程度和水平程度对液膜是否完整影响很大，不能划伤、挤压或使其变形。",
        "（3）蒸馏水要保持洁净，污染后应及时更换，否则表面张力系数会偏小。",
        "（4）拉膜时吊环不可晃动；环境嘈杂或台面振动都会使电压曲线抖动，增大读数误差。",
        "（5）液面下降要慢。下降过快时，液膜来不及达到 θ ≈ 0 的状态就会破裂，U_{max} 偏小。",
    ]
    for item in notes:
        add_text(doc, item, before=1, after=1)

    out = "/workspace/docs/液体表面张力系数的测定_实验报告_第一至四部分.docx"
    doc.save(out)
    print(out)


if __name__ == "__main__":
    main()
