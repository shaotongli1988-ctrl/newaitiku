# 学习方法模块标准卡片（V1 可录入）

## 使用说明

- 本文按固定字段输出：`methodCode`、`methodName`、`oneLineIntro`、`useWhen`、`steps`、`commonMistakes`、`questionBankActions`、`starterTask`、`difficultyLevel`、`estimatedMinutes`。
- 可直接用于管理端内容录入；如需结构化入库，可按同名字段转为 JSON。

---

## M01 费曼学习法

- `methodCode`: M01
- `methodName`: 费曼学习法
- `oneLineIntro`: 把知识讲给“新手”听，讲不清的地方就是你的薄弱点。
- `useWhen`:
  - 概念题总是似懂非懂。
  - 题会做但不会解释过程。
  - 复习时不知道自己哪里没懂。
- `steps`:
  - 选 1 个知识点，用 3 句话写出“我理解的版本”。
  - 假设对象是零基础同学，口述讲解 3 分钟。
  - 标出卡壳和表达模糊处，回教材补洞。
  - 再讲一遍并压缩成 5 句总结。
- `commonMistakes`:
  - 直接背定义，不做“自己的话重述”。
  - 讲解时跳步骤，忽略关键前提。
  - 不回查卡壳点，只做形式化复述。
- `questionBankActions`:
  - 进入同知识点 5 题小测，做完必须写“解题讲解”。
  - 错题页增加“请用自己的话解释错因”输入框。
- `starterTask`: 选今天最容易错的 1 个知识点，录一段 2 分钟语音讲解并完成 5 题验证。
- `difficultyLevel`: L1
- `estimatedMinutes`: 20

## M02 主动回忆

- `methodCode`: M02
- `methodName`: 主动回忆
- `oneLineIntro`: 先从脑中“取答案”，再看标准答案，记得更牢。
- `useWhen`:
  - 看笔记很熟，闭卷就想不起来。
  - 复习时间长但效果差。
  - 考场提取速度慢。
- `steps`:
  - 看题干后先遮住选项和答案。
  - 30-60 秒内写出你认为的答案与理由。
  - 对照标准答案，定位差异点。
  - 把差异点写成“下次提醒句”。
- `commonMistakes`:
  - 一上来就看答案。
  - 只看对错，不分析提取失败原因。
  - 回忆时间过长，影响节奏。
- `questionBankActions`:
  - 开启“先作答后看解析”模式。
  - 每题记录“首次回忆是否成功”。
- `starterTask`: 连做 10 题闭卷快答，每题先口述答案再提交。
- `difficultyLevel`: L1
- `estimatedMinutes`: 15

## M03 间隔重复

- `methodCode`: M03
- `methodName`: 间隔重复
- `oneLineIntro`: 在快要忘记前复习，花更少时间记更久。
- `useWhen`:
  - 记忆类知识反复遗忘。
  - 临考前发现旧知识断层。
  - 错题隔几天又错。
- `steps`:
  - 首次学习后当天做 1 次短测。
  - 按 D1、D3、D7、D14 节奏复习。
  - 每轮只复习“上轮错题 + 临界题”。
  - 连续两轮正确后降低频率。
- `commonMistakes`:
  - 集中突击，不做分散复习。
  - 每轮都从头复习，时间浪费。
  - 不记录复习轮次，节奏混乱。
- `questionBankActions`:
  - 系统自动生成 D1/D3/D7 复习包。
  - 按遗忘风险排序推题。
- `starterTask`: 建立 7 天复习队列，今天先完成 D1 包 15 题。
- `difficultyLevel`: L2
- `estimatedMinutes`: 25

## M04 莱特纳盒

- `methodCode`: M04
- `methodName`: 莱特纳盒
- `oneLineIntro`: 会的题少看，不会的题多看，把时间给薄弱点。
- `useWhen`:
  - 复习范围大，优先级不清。
  - 总在会的题上重复消耗时间。
  - 错题回炉没有层次。
- `steps`:
  - 建 3-5 个掌握层级盒（新题/待巩固/熟练）。
  - 做题后按表现升盒或降盒。
  - 每天优先练低盒题，高盒低频复查。
  - 每周一次全盒抽查校准。
- `commonMistakes`:
  - 只分对错，不分稳定性。
  - 只升不降，导致假掌握。
  - 不定期抽查，高盒长期失真。
- `questionBankActions`:
  - 题目自动标记盒层级。
  - 出题优先级按盒层级动态调整。
- `starterTask`: 从错题本挑 30 题建三盒，完成首轮分盒练习。
- `difficultyLevel`: L2
- `estimatedMinutes`: 30

## M05 检索练习

- `methodCode`: M05
- `methodName`: 检索练习
- `oneLineIntro`: 反复“想出来”比反复“看进去”更能提分。
- `useWhen`:
  - 同类题看解析后会，隔天又不会。
  - 记忆提取不稳定。
  - 模考时反应慢。
- `steps`:
  - 对同知识点做 3 轮短测（每轮 5 题）。
  - 轮间隔 10 分钟，不看答案重做。
  - 记录每轮首次提取成功率。
  - 低于 70% 的点加入次日复练。
- `commonMistakes`:
  - 每轮题目完全相同，形成机械记忆。
  - 轮间立即看答案，削弱检索强度。
  - 不统计成功率，只凭感觉。
- `questionBankActions`:
  - 自动生成“同点异题”三轮包。
  - 展示每轮提取成功率曲线。
- `starterTask`: 对一个薄弱知识点完成 3 轮检索快练并记录成功率。
- `difficultyLevel`: L2
- `estimatedMinutes`: 25

## M06 交错学习法

- `methodCode`: M06
- `methodName`: 交错学习法
- `oneLineIntro`: 把不同题型穿插练，提升识别题型和迁移能力。
- `useWhen`:
  - 单章节练得好，综合卷分数低。
  - 见到新题型不会选策略。
  - 题型切换时失误多。
- `steps`:
  - 选 3 类相关题型按 A-B-C 交替练。
  - 每做一题先说出“为什么用这个解法”。
  - 每轮结束复盘“误判题型”原因。
  - 下轮提高误判题型占比。
- `commonMistakes`:
  - 仍按单一题型连刷。
  - 只看对错，不看解法选择是否合理。
  - 交错难度过高导致放弃。
- `questionBankActions`:
  - 自动混编题包，强制题型切换。
  - 记录“解法选择是否匹配”。
- `starterTask`: 完成 18 题交错小卷（3 题型 * 6 题）并写 3 条误判总结。
- `difficultyLevel`: L2
- `estimatedMinutes`: 30

## M07 错题复盘法

- `methodCode`: M07
- `methodName`: 错题复盘法
- `oneLineIntro`: 错题价值不在“改对”，在“知道为什么又错”。
- `useWhen`:
  - 同类错误反复出现。
  - 错题本越积越多但提升慢。
  - 模考失分点集中。
- `steps`:
  - 每道错题先标错因（知识/审题/计算/粗心）。
  - 写“正确解法最短路径”。
  - 设置 24 小时后二刷提醒。
  - 三刷仍错则回到知识点重学。
- `commonMistakes`:
  - 只抄答案，不写错因。
  - 错因分类过粗，无法行动。
  - 不做延迟二刷。
- `questionBankActions`:
  - 错题必须标注错因标签后才能归档。
  - 自动生成“错因维度”复练包。
- `starterTask`: 复盘最近 10 道错题，完成错因分类并二刷。
- `difficultyLevel`: L1
- `estimatedMinutes`: 20

## M08 刻意练习

- `methodCode`: M08
- `methodName`: 刻意练习
- `oneLineIntro`: 聚焦最薄弱的一小块，短时间高质量重复突破。
- `useWhen`:
  - 冲刺期想快速抬分。
  - 某类题长期低正确率。
  - 大范围练习收益变小。
- `steps`:
  - 用数据选 1 个最低正确率点。
  - 设定可量化目标（如 40%->70%）。
  - 连续 3 轮高反馈训练（练习-反馈-修正）。
  - 达标后切换下一个薄弱点。
- `commonMistakes`:
  - 薄弱点选得太大，无法闭环。
  - 只刷题不看反馈。
  - 目标不量化，无法判断达成。
- `questionBankActions`:
  - 按薄弱标签自动拉题并限制范围。
  - 每轮结束给出改进建议与下一轮目标。
- `starterTask`: 选择正确率最低标签，完成 3 轮各 8 题训练。
- `difficultyLevel`: L3
- `estimatedMinutes`: 35

## M09 SQ3R 阅读法

- `methodCode`: M09
- `methodName`: SQ3R 阅读法
- `oneLineIntro`: 用“先提问后阅读”提升长文本理解和记忆。
- `useWhen`:
  - 理论类材料读完抓不住重点。
  - 阅读题正确率不稳定。
  - 长段文字容易走神。
- `steps`:
  - Survey：先扫结构和标题。
  - Question：把标题改成问题。
  - Read：带问题精读并标关键词。
  - Recite：合上材料口述答案。
  - Review：回顾并补全遗漏点。
- `commonMistakes`:
  - 省略提问步骤，直接读。
  - 只划线不复述。
  - 不做回顾，信息很快流失。
- `questionBankActions`:
  - 阅读题前先生成 3 个引导问题。
  - 提交后要求 60 秒复述核心结论。
- `starterTask`: 选 1 段理论材料，完成 SQ3R 全流程并做 6 题阅读题。
- `difficultyLevel`: L2
- `estimatedMinutes`: 30

## M10 康奈尔笔记法

- `methodCode`: M10
- `methodName`: 康奈尔笔记法
- `oneLineIntro`: 用“线索-笔记-总结”把零散知识变成可回忆结构。
- `useWhen`:
  - 听课记了很多但复习抓不到重点。
  - 笔记可读性差，回看成本高。
  - 缺乏复盘闭环。
- `steps`:
  - 右侧记录关键内容与例题。
  - 左侧写线索词与提问句。
  - 底部写 3-5 句总结。
  - 次日只看左侧线索进行回忆测试。
- `commonMistakes`:
  - 抄录过多细节，缺少提问线索。
  - 不写总结，知识未压缩。
  - 不做次日回忆检查。
- `questionBankActions`:
  - 题后自动生成“线索词模板”。
  - 支持按线索词反查关联题。
- `starterTask`: 用康奈尔模板整理今天一套题的核心知识并完成次日回忆。
- `difficultyLevel`: L1
- `estimatedMinutes`: 20

## M11 思维导图法

- `methodCode`: M11
- `methodName`: 思维导图法
- `oneLineIntro`: 把知识点做成网络结构，定位“断链”位置。
- `useWhen`:
  - 章节间联系不清。
  - 综合题不会拆解。
  - 复习时不知道先后顺序。
- `steps`:
  - 以章节主题做中心节点。
  - 拆出一级知识点与关键公式/概念。
  - 用箭头标注因果、包含、对比关系。
  - 对照错题标出高风险节点。
- `commonMistakes`:
  - 导图只列标题，没有关系线。
  - 节点过多过细，阅读负担大。
  - 不与错题数据联动更新。
- `questionBankActions`:
  - 章节练习后自动高亮错题密集节点。
  - 点击节点直接进入关联题练习。
- `starterTask`: 完成一个章节导图并把最近 15 道错题挂到对应节点。
- `difficultyLevel`: L2
- `estimatedMinutes`: 30

## M12 番茄学习法

- `methodCode`: M12
- `methodName`: 番茄学习法
- `oneLineIntro`: 把学习切成短冲刺，降低拖延并保持专注。
- `useWhen`:
  - 容易分心，学习时长难以保证。
  - 启动困难，拖延明显。
  - 长时学习后效率下降。
- `steps`:
  - 设定 25 分钟专注 + 5 分钟休息。
  - 每个番茄只做一个明确任务。
  - 4 个番茄后进行 15-20 分钟长休息。
  - 每日复盘番茄完成率与干扰来源。
- `commonMistakes`:
  - 一个番茄塞入多个任务。
  - 休息时继续刷题导致疲劳。
  - 不记录中断原因，无法改进。
- `questionBankActions`:
  - 题库训练可按番茄周期切片开始/结束。
  - 统计每个番茄的完成题量与正确率。
- `starterTask`: 今天完成 3 个番茄的题库训练，并记录每次中断原因。
- `difficultyLevel`: L1
- `estimatedMinutes`: 25

