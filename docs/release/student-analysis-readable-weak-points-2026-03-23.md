# 学生端知识诊断可读化说明

## 目标

- 让政治、英语、高数在知识诊断页按统一方式展示知识点。
- 让薄弱点一眼能看出“具体是哪个知识点”，而不是只看到整段大纲描述。

## 本次实现

- 后端知识树节点新增 `shortLabel` 与 `fullLabel`。
- 对 L5 知识点按统一规则提取短标题，保留完整标题作为补充信息。
- 学生端知识诊断模型增加 `displayLabel`、`displayPathLabel`，统一用于弱点榜单、优先攻克卡片、图谱 tooltip 和右侧定位详情。
- 恢复并启用“薄弱点排行”板块，把最需要先补的知识点明确列出来。
- “优先攻克”卡片改为同时展示短标题、完整知识点名、章节归属、掌握度、错误频次和建议动作。

## 验证

- `python3 -m pytest -q tests/test_question_bank.py -k "knowledge_tree_response_allows_wrong_count_field"`
- `npm test -- studentAnalysisGalaxy.test.js`
- `npm run build`

