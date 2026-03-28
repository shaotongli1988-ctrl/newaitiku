# 学生端 UI Token 收敛说明

## 交付总览

本次改造以 `web版UI设计` 目录中的参考图和 `azure_academix/DESIGN.md` 的 “Academic Sanctuary” 设计理念为基准，对学生端页面做了统一的视觉 token 收敛。

目标：

- 将学生端分散的颜色、渐变、圆角、阴影、胶囊标签、进度条等硬编码样式提取为全局 CSS 常量。
- 让首页、学情分析、任务页、自由练习、我的题库三子页和布局外壳在视觉层级上保持同一套语言。
- 保持项目现有业务逻辑不变，仅做样式与主题层的结构化收敛。

## 前端说明

本次新增和强化的样式基线主要落在以下文件：

- `frontend/src/assets/styles/variables.css`
  - 新增学生端语义 token，包括间距、圆角、表面层、边框、阴影、文本、图表色、主题渐变、学科色和交互态颜色。
- `frontend/src/style.css`
  - 将全局线条、高亮校验和进度条光效切到统一 token。
- 学生端页面与组件
  - `frontend/src/layouts/DefaultLayout.vue`
  - `frontend/src/views/Student/Home.vue`
  - `frontend/src/components/student/StudentHeroBanner.vue`
  - `frontend/src/components/student/StudentSubjectDrawer.vue`
  - `frontend/src/components/student/MasteryRadar.vue`
  - `frontend/src/views/Student/Analysis.vue`
  - `frontend/src/views/Student/Tasks.vue`
  - `frontend/src/views/Student/PersonalBank.vue`
  - `frontend/src/views/Student/Practice.vue`
  - `frontend/src/views/Student/WrongBook.vue`

视觉方向调整：

- 采用更轻的表面层级和更大的留白，减少“满屏硬边框”的感觉。
- 左侧导航、首页 Hero 和关键操作卡片统一为学院感蓝色体系。
- 常见胶囊标签、进度条、状态色和图表色改为语义变量，避免页面各自维护一套色板。
- 学科 accent 从脚本硬编码十六进制改为读取统一 token，便于后续继续扩展。

## 测试说明

本次改动未调整接口契约与业务计算逻辑，验证重点放在前端构建和样式落地可用性：

- 执行 `npm run build`
- 结果：通过
- 说明：Vite 生产构建成功，学生端相关页面样式文件均已完成编译产出

建议后续补充：

- 学生端关键页面的视觉回归或 E2E 冒烟，用于覆盖正常路径、异常路径和窄屏边界场景。
- 若后续继续调整学生端 UI，可将 token 使用规范补充进前端 README 或设计约定文档。
