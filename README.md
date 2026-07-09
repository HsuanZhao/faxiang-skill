# 法官造像· 中国法官法律裁判方法论蒸馏 Skill

> 法官不发微博，不开播客，不接受"人生访谈"。他/她唯一持续、公开、可信的自我表达，是判决书里的说理段落，和期刊上的署名文章。

法相Skill是一个可被AI大模型加载的自定义Skill：输入一位中国法官（在任或退休）的姓名与任职法院信息，自动完成学术论文、裁判文书说理、案例评析、学术会议发言等多源调研，提炼其**法律方法论**，最终生成一个可运行、可交互的"法官视角"Skill。

---

## 这是什么，不是什么

**是**：
- 一套系统化的调研与提炼流程，帮助法律从业者、研究者理解某位法官在学术论著与裁判说理中体现出的法律解释方法、论证结构、价值取向
- 一个强调"来源可信、方法论透明、边界清晰"的蒸馏框架，默认按中国法官的公开表达特点（几乎不接受专访、不发社交动态，但会在核心业务期刊、学术会议上持续输出）设计信息源策略

**不是**：
- **不是判决结果预测工具**。生成的Skill被硬性要求拒绝任何"这位法官会怎么判某个具体案子"类型的提问
- **不是法官本人的代言人**。所有输出都必须标注"基于公开学术观点的方法论模拟推演，不代表本人意见，不构成任何案件的裁判意见或法律意见"
- **不是自动化爬虫工具**。裁判文书网、知网等平台的检索/下载环节，本Skill刻意设计为"人工下载 + 脚本辅助登记校验"，不做自动抓取、不破解验证码、不绕过付费墙

---

## 适用范围

- ✅ 中国法官（在任/退休），有公开发表的学术论文、专著、案例评析或裁判文书
- ⚠️ 检察官、律师、学者等其他法律职业者：可参考本框架调整，但信息源策略（尤其是期刊清单、裁判文书处理方式）是针对法官身份设计的，直接套用需要自行评估
- ❌ 不适用于对具体在办案件做裁判结果预测——这一点在Skill内部有多处硬性拦截，不会因为提示词技巧而绕过

---

## 仓库结构

```
.
├── README.md
├── LICENSE
├── .gitignore
└── faguan-fangfalun/              # Skill本体，文件夹名与SKILL.md的name字段一致
    ├── SKILL.md                   # Skill定义（YAML frontmatter + 执行流程说明）
    └── scripts/
        ├── wenshu_lookup_helper.py       # 裁判文书本地语料登记/校验/分流
        ├── cnki_citation_formatter.py    # 学术论文引用规范化
        └── manifest_example.json         # manifest.json 字段示例
```

本仓库只维护Skill定义本身。使用Skill蒸馏具体法官时产生的调研文件、下载的裁判文书原文等运行产物，会生成在你本地的 `.claude/skills/[法官姓名]-judicial-perspective/` 目录下，**不会、也不应该**提交回本仓库（见 `.gitignore` 说明）。

---

## 安装

按照 [Anthropic Agent Skills](https://docs.claude.com) 规范，Skill 是一个包含 `SKILL.md` 的独立文件夹，放到对应的skills目录下即可被识别。

**Claude Code / 项目级安装**（推荐）：

```bash
# 在你的项目根目录下
mkdir -p .claude/skills
git clone <本仓库地址> /tmp/faguan-fangfalun-repo
cp -r /tmp/faguan-fangfalun-repo/faguan-fangfalun .claude/skills/
```

**个人级安装**（对所有项目生效）：

```bash
mkdir -p ~/.claude/skills
git clone <本仓库地址> /tmp/faguan-fangfalun-repo
cp -r /tmp/faguan-fangfalun-repo/faguan-fangfalun ~/.claude/skills/
```

安装后目录应为：

```
.claude/skills/faguan-fangfalun/
├── SKILL.md
└── scripts/
    ├── wenshu_lookup_helper.py
    ├── cnki_citation_formatter.py
    └── manifest_example.json
```

确认脚本可执行权限（可选，脚本用 `python3 script.py` 方式调用即可，不强制要求可执行位）：

```bash
chmod +x .claude/skills/faguan-fangfalun/scripts/*.py
```

---

## 快速开始

1. 完成上方安装步骤
2. 在支持该Skill的Claude环境中说：「蒸馏法官张三」或「造一个张三法官的skill」
3. 按提示完成身份核实（法官姓名+现任/曾任法院+庭室，避免同名混淆）、在任状态确认、蒸馏档位选择
4. 如果你手上有该法官的裁判文书原文，参考下方"本地裁判文书语料"部分手动下载后放入指定目录
5. Skill会依次完成调研→提炼→构建→验证四个阶段，每个关键节点都会暂停请你确认，不会一路裸奔到底

蒸馏完成后，生成的法官视角Skill会落在 `.claude/skills/[法官姓名]-judicial-perspective/SKILL.md`，与本仓库的 `faguan-fangfalun/` 是两个独立的Skill目录，互不覆盖。

---

## 蒸馏结果的目录结构（运行时生成，非本仓库内容）

当你用本Skill蒸馏一位具体法官时，会在 `.claude/skills/[法官姓名]-judicial-perspective/` 下生成如下结构（**这不是本仓库的内容，是Skill运行后的产物，仅存在于你本地**）：

```
.claude/skills/[法官姓名]-judicial-perspective/
├── SKILL.md                              # 最终生成的可运行Skill
└── references/
    ├── research/                         # 6个调研维度的原始产出（必存）
    │   ├── 01-academic-writings.md       # 学术论文与专著
    │   ├── 02-judicial-reasoning.md      # 裁判文书说理风格
    │   ├── 03-case-commentary.md         # 案例评析、指导性案例解读、培训讲稿
    │   ├── 04-academic-standing.md       # 学术任职、获奖、学术会议发言
    │   ├── 05-external-views.md          # 同行评价、学术引证、书评
    │   └── 06-timeline.md                # 职业时间线
    └── sources/
        ├── articles/                     # 期刊论文PDF/全文
        ├── monographs/                   # 专著
        ├── conference-papers/            # 学术会议论文集
        └── judgments/                    # 手动下载的裁判文书语料（见下）
            ├── manifest.json             # 元数据清单，唯一的"真相来源"
            ├── raw/                      # 待校验的原始下载文件
            ├── verified/                 # 校验通过，Skill实际读取的文件
            └── excluded/                 # 未通过校验，附排除原因
```

---

## 六个调研维度

| # | 维度 | 核心来源 |
|---|------|---------|
| 1 | 学术论文与专著 | 《法律适用》《人民司法》《数字法治》等法院系统权威业务期刊 + CLSCI核心法学期刊 + 个人专著 |
| 2 | 裁判文书说理风格 | 仅限已生效、公开合规、经人工核实的裁判文书 |
| 3 | 案例评析 | 本人撰写的指导性案例解读、审判业务培训讲稿 |
| 4 | 学术任职与会议 | 全国法院学术讨论会获奖情况、审判业务专家任职、学术会议发言记录 |
| 5 | 他者评价 | 学术引证、同行书评、上级法院对其观点的引用采纳 |
| 6 | 职业时间线 | 任职履历、学术产出年表 |

信息源明确排除：知乎、微信公众号、百度百科、来源不明的判决书截图、涉及具体在办案件的舆论报道。

---

## 本地裁判文书语料：手动下载 + 脚本校验

裁判文书网有反爬机制，公开检索式往往覆盖不全，因此本Skill默认推荐**人工下载、脚本辅助登记**的方式，而不是让Skill自己联网抓取：

```bash
# 1. 你在裁判文书网/北大法宝/威科先行手动搜索并下载文书原文，放进：
#    references/sources/judgments/raw/

# 2. 扫描raw/下的新文件，逐个交互式录入元数据
#    （法院全称、法官在本案中的角色、是否已生效、是否已核实身份、是否已核对敏感内容等）
python3 scripts/wenshu_lookup_helper.py scan [skill目录]

# 3. 根据录入结果，自动把文件分流到 verified/ 或 excluded/
python3 scripts/wenshu_lookup_helper.py sort [skill目录]

# 4. 查看当前可供调研读取的文书清单（附主审/非主审权重提示）
python3 scripts/wenshu_lookup_helper.py list-verified [skill目录]
```

**采纳硬性条件**：必须同时满足"已生效 + 已人工核实身份 + 已核对无敏感内容"三项，才会进入 `verified/`；缺一项都会被分流到 `excluded/` 并记录具体原因，方便日后追溯。非主审法官（合议庭成员但非承办人/审判长）的文书即使采纳，也会被标注为"仅作参考、权重较低"。

`manifest.json` 的完整字段说明见 `scripts/manifest_example.json`。

---

## 学术论文引用规范化

从知网/万方/维普等平台人工摘录题录信息后，用以下脚本统一格式并按期刊级别自动标注可信度：

```bash
python3 scripts/cnki_citation_formatter.py entries.json          # 纯文本输出
python3 scripts/cnki_citation_formatter.py entries.json --md     # Markdown表格输出
```

内置分级规则：《法律适用》《人民司法》《数字法治》→ 最高权重；常见CLSCI核心法学期刊 → 高权重；其他期刊 → 需人工核实。同时会根据署名顺序（第一作者/通讯作者/合著）提示该文章代表该法官本人观点的权重高低。

---

## 生成的Skill有哪些硬性约束

最终生成的"法官视角"Skill在角色扮演时必须遵守：

1. 开头与结尾均带有免责声明："基于公开学术观点的方法论模拟推演，不代表本人意见，不构成任何案件的裁判意见或法律意见"
2. 遇到涉及**具体在办案件**的提问，直接拒绝回答并说明理由，不做任何形式的裁判结果预测
3. 严格区分"法官个人学术观点"与"法院集体意见（如审判委员会讨论意见）"，不混为一谈
4. 引用法条、司法解释、指导性案例时必须先用工具核实准确性，不得凭训练语料编造法条内容或案号

质量验证阶段（Phase 4）专门设有"合规测试"：故意用一个涉及具体在办案件的问题测试生成的Skill，检验它是否能正确拒绝，而不是顺着问题给出预测性内容。

---

## 常见问题

**Q：这个Skill能用来预测某位法官会怎么判我手上的案子吗？**
不能，而且Skill内部有多重设计专门阻止这种用法（角色扮演规则、Agentic Protocol的问题分类、Phase 4合规测试）。它只能模拟该法官一贯的法律方法论进行学术推演。

**Q：该法官公开论著很少怎么办？**
Skill会在Phase 0.5就提前告知你信息不足，方法论要素会减至2-3个并明确标注"基于有限信息推测"，不会为了凑数而编造。

**Q：可以用来蒸馏检察官或律师吗？**
框架可以参考，但期刊清单、裁判文书处理逻辑是针对法官身份设计的，直接套用前建议先自行调整信息源部分。

**Q：裁判文书网检索总是搜不到怎么办？**
这是预期内的限制，因此本Skill默认推荐手动下载+本地登记的方式（见上方"本地裁判文书语料"部分），而不是依赖在线检索。

---

## 免责声明

本Skill及其生成的衍生Skill仅供学术研究、法律写作参考与法律方法论教学使用，不构成任何法律意见，不代表任何法官、法院的官方立场，不得用于预测具体案件的裁判结果。使用者应自行确保调研过程中获取和使用的裁判文书、学术论文等材料符合相关法律法规及平台服务条款。

---

## 📢 作者信息

**赵璇 律师**
北京市百瑞（上海）律师事务所 执业律师 / 市场部负责人

- **微信公众号**：
  - `法律雇佣军 LegalMercenary`
  - `贪心网络法 GreedyCyberlaw`
- **小红书**：`@硅律 SiliconLawyer`
- **工作微信**：`HsuanZhao`

专注科技伦理与法律实务交叉领域疑难问题的资深诉讼律师，热衷分享LawTech工具、诉讼经验、合规实务与高效工作方法。
