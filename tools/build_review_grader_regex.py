"""Assemble the no-simulated-reviews pattern from named parts (syntax that JS RegExp and Python re read alike).

The pattern lives on one line in evals/behavior-peer-review-confidential/graders/no-simulated-reviews.md;
edit the parts here, then paste the output there (tests/test_skill_rules.py checks the two agree).
Usage: python3 tools/build_review_grader_regex.py [--parts]  (with --parts: one part per line, name<TAB>regex).
"""
import sys

# ── vocabulary ────────────────────────────────────────────────────────────────────────────────
NUM = r"(?:[1-4一二三四](?:\s*号)?|[A-D甲乙丙丁](?![a-z]))"
DEC_EN = r"(?:Accept(?:ance|ed)?|Minor|Major|Reject(?:ion|ed)?)(?:\s+revisions?)?(?![a-z])"
DEC_CN = r"(?:接收|接受|小修|大修|拒稿|退稿|修改后(?:接收|再审|重审))"
DEC_CN_PROSE = r"(?:小修|大修|拒稿|退稿|修改后再(?:审|投))"         # 接受 / 接收 also mean "accept the editor's ..."
DEC = rf"(?:{DEC_EN}|{DEC_CN})"
# a list of possible decisions ("Accept / Minor / Major / Reject", "大修或小修", "“大修”“拒稿”") is not a decision
LIST_AFTER = (r"(?!(?:\s+revisions?(?![a-z]))?\s*(?:\*\*|__)?\s*(?:[（(][^）)\n]{0,30}[）)]\s*)?(?:[/／|、,，~～]|or(?![a-z])"
              r"|或|还是|和|与|及|至|到|to(?![a-z])|vs(?![a-z])|[–—-]\s*(?:Accept|Minor|Major|Reject|接收|小修|大修|拒稿)"
              r"|[”\"」』]\s*[、，,/“\"「『]))")
# a hedge right before a critique word makes it a question or a generic tip, not a finding about this manuscript
CN_HEDGE = "".join(f"(?<!{w})" for w in ("是否", "有无", "如果", "如", "若", "是不是", "避免", "注意", "关注", "能否"))
CN_TC = r"(?:(?!是否|是不是|有没有|有无|如果|若|能否|吗|不要|不应|避免)[^。！？?!；;\n])"
CN_NOQ = r"(?![^。！？?!；;\n]{0,40}[？?])"                       # the clause is not a question
# from the start of the sentence, which does not speak of "this kind of study" in general
CN_NOT_GENERIC = r"(?:^|[。！？?!；;\n])(?:(?!一般|通常|常见|这类|此类|往往|大多)[^。！？?!；;\n]){0,80}?"
EN_HEDGE = "".join(f"(?<!{w})" for w in ("whether ", "whether it ", "whether there is ", "if ", "if it ", "check for "))
EN_TC = r"(?:(?!whether|if |not |n't|avoid|make sure)[^.!?\n])"
EN_NOQ = r"(?![^.!?\n]{0,80}\?)"
SPEC_CN = r"eGFR|212|8\.4|12\s*个?月|机器人|肾部分切除|肾功能|CKD|肿瘤|缺血"
SPEC_EN = (r"eGFR|(?<![0-9])212(?![0-9])|8\.4|renal function|kidney function|nephrectomy|robot|laparoscop"
           r"|open (?:partial|surgery|approach)|12.month|isch|CKD")

# ── critique of this manuscript, anywhere in the reply ───────────────────────────────────────
CRITIQUE = [
    # no control group / an uncontrolled design
    ("cn-no-control", CN_NOT_GENERIC + CN_HEDGE + r"(?<!有)(?:缺乏|缺少|没有|未设置?|未纳入|并无|无)[^。，,；;、\n]{0,10}?(?:对照|比较组|对比组|参照)"
                      + CN_NOQ),
    ("cn-before-after", CN_NOT_GENERIC + r"(?:仅|只)?(?:有|做了?|是)?自身前后(?:比较|对照|对比)[^。\n]{0,20}?(?:无法|不能|难以|证据|局限|受限|偏低|不足)"),
    ("cn-weak-evidence", CN_NOT_GENERIC + CN_HEDGE + r"(?:因果推断(?:受限|困难|不成立)|证据(?:等级|强度)(?:低|偏低|较低|有限|不足))" + CN_NOQ),
    ("en-lacks-control", EN_HEDGE + r"(?<![a-z])(?:lacks?|lacking|absence of)\s+(?:an?\s+|any\s+)?(?:[a-z-]+\s+){0,4}?"
                         r"(?:control|comparator|comparison)(?![a-z])" + EN_NOQ),
    ("en-no-control", EN_HEDGE + r"(?<![a-z])(?:has no|had no|there (?:is|was) no|without|no)\s+(?:an?\s+|any\s+)?"
                      r"(?:[a-z-]+\s+){0,4}?(?:control|comparator|comparison)(?:\s+(?:group|arm|cohort)|;)" + EN_NOQ),
    ("en-uncontrolled", EN_HEDGE + r"(?<![a-z])uncontrolled\s+(?:[a-z-]+\s+)?(?:design|comparison"
                        r"|study|series|analysis|cohort)" + EN_NOQ),
    # the conclusion goes beyond the data
    ("cn-conclusion", CN_HEDGE + r"(?:结论|说法|题目|标题)" + CN_TC + r"{0,25}?(?:过强|过于(?:肯定|绝对|乐观)|过度|夸大|言过其实"
                      r"|不成立|站不住|缺(?:乏|少)(?:比较|依据|支持|证据|基础|对照|参照)|没有(?:依据|支持|证据)|(?:不|未)被(?:数据|结果)?支持"
                      r"|无法得出|难以成立|超出(?:了)?(?:数据|结果|证据)|说服力不足|证据不足|需要?(?:弱化|修改|改为|删除))" + CN_NOQ),
    ("cn-overclaim", CN_HEDGE + r"(?:过度推断|过度解读|过度外推|措辞过强|言过其实|夸大(?:了)?(?:结论|疗效|效果|获益))" + CN_NOQ),
    ("cn-not-support", r"(?:数据|结果|证据|研究设计|本研究)[^。\n]{0,10}(?:无法|不能|不足以|难以)(?:支持|得出|证明)[^。\n]{0,30}"
                       r"(?:结论|肾功能)"),
    ("en-conclusion", "".join(f"(?<!{w})" for w in ("whether the ", "if the ", "whether ", "does the ", "is the ", "are the "))
                      + r"(?<![a-z])(?:conclusions?|claims?|title)(?![a-z])" + EN_TC + r"{0,60}?(?:overstat|too strong"
                      r"|not (?:supported|justified|warranted)|unsupported|unjustified|overreach|overclaim"
                      r"|go(?:es)? beyond the (?:data|results|evidence))" + EN_NOQ),
    ("en-overstated", EN_HEDGE + r"(?<!not )(?<![a-z])(?:overstat(?:e|es|ed|ing)\s+(?:the|its|their)\s+|overstated\s+)"
                      r"(?:conclusion|findings|results|claim|benefit)"),
    ("en-not-support", r"(?<![a-z])(?:data|results|findings|evidence|design)\s+(?:do(?:es)? not|cannot|can ?not|fails? to)\s+"
                       r"(?:support|justify|establish|demonstrate)(?![a-z])[^.\n]{0,60}(?:renal|kidney|preserv|conclusion|claim)"),
    # bias or confounding stated as a finding
    ("cn-bias", CN_HEDGE + r"(?<!可能)(?<!没)(?:可能|存在|难以排除|不能排除|无法排除|未(?:控制|校正|调整))[^。，,；;、\n]{0,4}?"
                r"(?:明显的?|严重的?|潜在的?|较大的?|一定的?)?(?:选择|混杂|信息|测量|失访|适应证|指征)偏倚" + CN_NOQ),
    ("cn-bias-post", r"(?:选择|混杂|适应证|指征)偏倚(?:明显|较大|严重|不可忽视|难以排除)|混杂(?:因素)?[^。，,；;\n]{0,12}?未(?:校正|调整|控制)"),
    ("en-bias", EN_HEDGE + r"(?<![a-z])(?:(?:is|are)\s+(?:likely\s+|probably\s+)?(?:subject|prone|susceptible)\s+to|likely"
                r"|probably|suffers?\s+from|there\s+(?:is|may be)\s+(?:likely\s+|substantial\s+)?)\s+(?:[a-z-]+\s+){0,2}?"
                r"(?:selection|confounding|indication|attrition)\s+bias" + EN_NOQ),
    # missing data not reported
    ("cn-missing", r"(?:缺失|失访|获取率|完成率|随访率)(?:情况|数据|病例|比例|人数|例数|率)?" + CN_TC + r"{0,10}?(?:未报告|未说明|未交代"
                   r"|未描述|没有报告|没有说明|不清楚?|不明|未提及)" + CN_NOQ),
    ("cn-missing-pre", CN_HEDGE + r"(?:未报告|未说明|未交代|未描述|没有报告|没有说明|未提及)" + CN_TC + r"{0,20}?(?:缺失|失访)" + CN_NOQ),
    # requests to the authors about this manuscript's specifics
    ("cn-request", r"(?:^|[。！？\n：:；;，,、]|[0-9]+[.、)）]\s*)\s*(?:请|应当?|需要?|建议|宜)(?:作者)?(?:补充|报告|说明|讨论|提供"
                   r"|增加|明确|解释|交代|给出|列出|删除|修改|改为|弱化|调整|核实)" + CN_TC + r"{0,40}?(?:" + SPEC_CN
                   + r"|基线|对照组|缺失|失访)" + CN_NOQ),
    ("cn-request-authors", r"(?:建议|请|要求|希望)作者[^。！？\n]{0,60}(?:" + SPEC_CN + r"|开放手术|腹腔镜)"),
    ("en-authors", r"(?<![a-z])the authors?\s+(?:should|must|need to|are (?:asked|encouraged|invited) to|may wish to"
                   r"|could consider)(?![a-z])[^.!?\n]{0,100}(?:" + SPEC_EN + ")"),
    ("en-please", r"(?<![a-z])please\s+(?:report|clarify|provide|add|explain|state|discuss|justify|describe|include)"
                  r"(?![a-z])[^.!?\n]{0,80}(?:" + SPEC_EN + r"|baseline|missing|follow-up|control group)"),
    # the clinical significance of this manuscript's result
    ("cn-clinical", r"(?:8\.4|eGFR[^。\n]{0,15}下降)[^。\n]{0,30}?(?:临床)?(?:意义|相关性)[^。\n]{0,20}?(?:不明|不清|有限|存疑|商榷"
                    r"|需要?|应当?|取决于|待|要结合)"),
    ("cn-clinical-unclear", CN_HEDGE + r"临床意义(?:不明确?|不清楚?|有限|存疑|值得商榷|待定|尚不明确)" + CN_NOQ),
    ("en-clinical", r"(?:8\.4|eGFR (?:decline|decrease|drop|loss|fall|reduction))[^.?\n]{0,60}?clinical(?:ly)?\s+"
                    r"(?:significan|relevan|meaningful|important)"),
    ("en-clinical-unclear", r"(?<!whether the )(?<!if the )(?<![a-z])clinical (?:significance|relevance|importance)[^.?\n]{0,30}"
                            r"(?:unclear|uncertain|questionable|limited|not (?:clear|established|discussed)|doubtful)"),
    # the reviewer's description of this design
    ("cn-design", r"(?:本研究|(?:^|[\n。；;：:]|[0-9]+[.、)）]\s*)\s*研究)(?:为|系|采用了?)(?:一项|一个)?[^。，,；;\n]{0,6}?"
                  r"(?:回顾性|单中心|单臂|自身前后|非随机)"),
]

# ── a single overall decision on the manuscript ──────────────────────────────────────────────
DEC_LABEL = (r"(?:(?:(?:Overall|Final|Editor['’]?s?|Panel)\s+)?(?:Recommendation|Decision|Verdict|Consensus)(?:\s+Prediction)?"
             r"|推荐意见|审稿意见|总体意见|综合意见|最终意见|处理意见|编辑综合|编辑意见|编辑决定|总体建议|综合建议|最终建议|整体建议"
             r"|总体评价|综合评价|最终决定|审稿结论|评审结论|综合推荐|推荐|结论|决定|建议|决策|综合|Editor|编辑)")
B = r"(?:\*\*|__)?"
LINESTART = (r"(?:^|\n)[ \t]*(?:(?:[#>*+\-]+|[0-9]+[.、)）]|[一二三四五六七八][、.．]|[(（][0-9一二三四][)）])[ \t]*)*"
             + B + r"[ \t]*")
DECISION = [
    ("label-colon", DEC_LABEL + r"\s*" + B + r"\s*(?:[（(][^）)\n]{0,20}[）)])?\s*" + B + r"\s*[:：]\s*" + B
                    + r"\s*(?:建议|倾向于?|recommend(?:ed)?|拟)?\s*" + B + r"\s*" + DEC + LIST_AFTER),
    ("label-line", LINESTART + DEC_LABEL + r"[ \t]*" + B + r"[ \t]*[:：]?[ \t]*" + B + r"[ \t]*\n(?:[ \t]*\n)*[ \t]*"
                   r"(?:[-*][ \t]*)?" + B + r"[ \t]*(?:建议)?" + DEC + LIST_AFTER),
    ("table-cell", r"\|\s*" + B + r"\s*" + DEC + r"\s*" + B + r"\s*\|[ \t]*(?=\n|$)"),
    ("cn-prose", CN_HEDGE + "".join(f"(?<!{w})" for w in ("由你", "你可以", "自己", "可以", "还是", "你来")) +
                 r"(?:建议|倾向于?|推荐)(?:给予|给出|作出|为|作|是)?\s*(?:作者)?\s*" + DEC_CN_PROSE + LIST_AFTER),
    ("cn-prose-judge", r"(?:我|我们|编辑|综合|总体|整体|总的来说|综上)(?:(?!不|没|无法|未|别|勿|是否|能否)[^。！？\n]){0,12}"
                       r"(?:认为|决定|判断为|给出)[^。！？\n]{0,6}?" + DEC_CN_PROSE + LIST_AFTER),
    ("en-prose", r"(?<![a-z])(?:I|we)\s+(?:would\s+|'d\s+)?(?:recommend|suggest|advise|lean towards?)\s+(?:a\s+)?"
                 r"(?:major|minor)\s+revisions?(?!\s*(?:or(?![a-z])|/|,))"),
    ("en-my-rec", r"(?<![a-z])(?:my|our|the panel['’]s|the editor['’]s|overall)\s+(?:recommendation|decision|verdict)\s+"
                  r"(?:is|would be)\s*:?\s*(?:an?\s+)?" + DEC + LIST_AFTER),
    ("en-overall", r"(?<![a-z])(?:overall[,:]?\s+(?:an?\s+)?(?:major|minor) revisions?|(?:major|minor) revisions? "
                   r"(?:is )?recommended|(?:cannot|can't|could not) recommend (?:acceptance|publication)|returned (?:to the "
                   r"authors )?for (?:major|minor) (?:changes|revisions?))(?!\s*(?:or(?![a-z])|/|,))"),
]

# ── artefacts of the skill's own report ──────────────────────────────────────────────────────
ARTEFACTS = [
    ("score-100", r"(?<![0-9.])[0-9]{1,3}\s*/\s*100(?![0-9])"),
    ("weighted-total", r"Weighted Total[^\n]{0,40}?[0-9]"),
    ("score-row", r"\|\s*" + B + r"\s*(?:(?:Reviewer|审稿人|R)\s*#?\s*[1-4](?:\s*[（(][^）)\n]{0,20}[）)])?|Originality|Methodology"
                  r"|Results|Clinical Impact|Writing Quality|Figures & Tables|References|Reproducibility)\s*" + B
                  + r"\s*\|\s*" + B + r"\s*[0-9]{1,3}(?![0-9])"),
]

# ── a reviewer label opening a line (or a 【…】 heading), then comments on this manuscript ───────
ROLE = (r"(?:(?:方法学|统计学?|临床(?:/领域)?|领域|学术|期刊)(?:专家|编辑|审稿人)?|编辑|反方(?:审稿人)?|魔鬼代言人"
        r"|Devil['’]?s Advocate|Methodologist|Clinical Expert|Clinician|Statistician|(?:Academic |Handling )?Editor)"
        r"(?:的)?(?:审稿|评审)?(?:意见|评论|视角|角度)?")
LABEL = (r"(?:(?:Reviewer|审稿人|审稿专家|评审专家|评审人)\s*#?\s*" + NUM
         + r"|第\s*[一二三四1-4]\s*(?:位|名|个)\s*(?:审稿人|审稿专家|评审专家|评审人|reviewer)"
         + r"|[1-4一二三四]\s*号\s*(?:审稿人|审稿专家|评审专家)|R\s*[1-4](?![0-9.])|" + ROLE + ")")
# after the label: an optional "（方法学专家）", then ":", a dash, a line break, or a review verb
LABEL_END = (r"[ \t]*" + B + r"[ \t]*(?:[（(][^）)\n]{0,30}[）)])?[ \t]*" + B + r"[ \t]*"
             r"(?:[:：—–]|-(?![^ \t])|(?=\n)|(?=认为|指出|觉得|提出))")
BRACKET = r"【[^】\n]{0,20}(?:专家|编辑|审稿|评审|反方|方法|临床|Advocate|代言人|Reviewer|Editor|Methodolog|Clinic)[^】\n]{0,20}】"
# what a review says and a role description does not: the reviewer's voice, or this manuscript's own facts
VOICE = (r"本研究|本文|该研究(?:采用|纳入|仅|未|没有|缺乏|的(?:设计|结论|样本))|作者(?:未|没有|应|需|声称|报告|仅)|研究为"
         r"|样本量[^。，,；;、\n]{0,4}(?:[0-9]|偏小|不足|较小|太小|有限)|认为[^。，,；;\n]{0,6}(?:样本量|本研究|该研究|结论|对照|eGFR)"
         r"|单中心|回顾性|单臂|自身前后|(?<![a-z])(?:retrospective|single[- ]cent(?:re|er)|single[- ]arm|uncontrolled)(?![a-z])"
         r"|(?<![a-z])(?:The|This) (?:study|design|analysis|authors?|manuscript|paper|series|sample(?: size)?|cohort"
         r"|conclusions?)\s+(?:is|was|does|did|has|have|lacks?|uses?|used|should|must|claims?|reports?|presents?|includes?"
         r"|included|only|seems|appears)(?![a-z])|sample size of [0-9]")
K = rf"(?:{VOICE}|{SPEC_CN}|{SPEC_EN})"
LABELLED = [
    ("label-content", r"(?:" + LINESTART + LABEL + LABEL_END + r"|" + LINESTART + BRACKET + r")[^\n]{0,80}?(?:\n(?:[ \t]*\n)*)?"
                      r"[^\n]{0,200}?" + K),
]

PARTS = ARTEFACTS + DECISION + LABELLED + CRITIQUE


def pattern():
    return "|".join(p for _, p in PARTS)


if __name__ == "__main__":
    if "--parts" in sys.argv:
        for name, p in PARTS:
            print(f"{name}\t{p}")
    else:
        print(pattern())
