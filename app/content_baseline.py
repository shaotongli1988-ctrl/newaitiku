from __future__ import annotations

from typing import Dict, List, Optional

POLICY_VERSION_CODE = "HB_ZSB_2026"
POLICY_VERSION_TITLE = "河北专升本题库内容体系基准文档（2026版）"

EXAM_CATEGORIES = [
    {"examCategoryCode": "ECONOMICS", "examCategoryName": "经济学类", "sortNo": 1},
    {"examCategoryCode": "MANAGEMENT", "examCategoryName": "管理学类", "sortNo": 2},
    {"examCategoryCode": "SCIENCE_ENGINEERING", "examCategoryName": "理工类", "sortNo": 3},
    {"examCategoryCode": "AGRICULTURE", "examCategoryName": "农学类", "sortNo": 4},
    {"examCategoryCode": "EDUCATION", "examCategoryName": "教育学类", "sortNo": 5},
    {"examCategoryCode": "LITERATURE", "examCategoryName": "文学类", "sortNo": 6},
    {"examCategoryCode": "LAW", "examCategoryName": "法学类", "sortNo": 7},
    {"examCategoryCode": "HISTORY", "examCategoryName": "历史学类", "sortNo": 8},
    {"examCategoryCode": "MEDICINE", "examCategoryName": "医学类", "sortNo": 9},
    {"examCategoryCode": "ART", "examCategoryName": "艺术类", "sortNo": 10},
]

PUBLIC_SUBJECTS = [
    {"subjectCode": "POLITICS", "subjectName": "政治", "subjectType": "PUBLIC", "score": 100},
    {"subjectCode": "ENGLISH", "subjectName": "英语", "subjectType": "PUBLIC", "score": 100},
]

SUBJECT_CODE_MAP = {
    "经济学基础": "ECONOMICS_FOUNDATION",
    "高等数学（一）": "ADVANCED_MATH_1",
    "高等数学（二）": "ADVANCED_MATH_2",
    "管理学原理": "MANAGEMENT_PRINCIPLES",
    "化工原理": "CHEMICAL_PRINCIPLES",
    "工程力学": "ENGINEERING_MECHANICS",
    "信息技术概论": "INFO_TECH_INTRO",
    "教育心理学": "EDUCATIONAL_PSYCHOLOGY",
    "动物生物化学": "ANIMAL_BIOCHEMISTRY",
    "植物学": "BOTANY",
    "园林花卉学": "LANDSCAPE_FLORICULTURE",
    "体育专业综合": "SPORTS_COMPREHENSIVE",
    "解剖生理学": "ANATOMY_PHYSIOLOGY",
    "文史基础": "ARTS_HISTORY_FOUNDATION",
    "外语专业综合": "FOREIGN_LANGUAGE_COMPREHENSIVE",
    "新媒体概论": "NEW_MEDIA_INTRO",
    "法理学": "JURISPRUDENCE",
    "中国近现代史纲要": "MODERN_CHINESE_HISTORY_OUTLINE",
    "生理学": "PHYSIOLOGY",
    "人体解剖学": "HUMAN_ANATOMY",
    "艺术概论": "ART_INTRODUCTION",
    "美术专业综合": "FINE_ARTS_COMPREHENSIVE",
    "书法专业综合": "CALLIGRAPHY_COMPREHENSIVE",
    "表演专业综合": "PERFORMANCE_COMPREHENSIVE",
    "舞蹈专业综合": "DANCE_COMPREHENSIVE",
    "声乐专业综合": "VOCAL_MUSIC_COMPREHENSIVE",
    "器乐专业综合": "INSTRUMENTAL_MUSIC_COMPREHENSIVE",
}

JOINT_EXAM_GROUPS = [
    {
        "jointExamGroupCode": "ECONOMICS_1",
        "jointExamGroupName": "经济学类",
        "examCategoryCode": "ECONOMICS",
        "majorListText": "经济学、金融学、金融工程、保险学、经济与金融、精算学、国际经济与贸易",
        "professionalSubjects": [
            {"subjectCode": "ECONOMICS_FOUNDATION", "subjectName": "经济学基础", "subjectType": "PROFESSIONAL_1", "score": 150},
            {"subjectCode": "ADVANCED_MATH_2", "subjectName": "高等数学（二）", "subjectType": "PROFESSIONAL_2", "score": 150},
        ],
    },
    {
        "jointExamGroupCode": "MANAGEMENT_1",
        "jointExamGroupName": "管理学 1",
        "examCategoryCode": "MANAGEMENT",
        "majorListText": "会计学、资产评估、大数据与会计、财务管理、审计学、工商管理、市场营销、国际商务、电子商务、电子商务及法律、跨境电子商务",
        "professionalSubjects": [
            {"subjectCode": "MANAGEMENT_PRINCIPLES", "subjectName": "管理学原理", "subjectType": "PROFESSIONAL_1", "score": 150},
            {"subjectCode": "ADVANCED_MATH_2", "subjectName": "高等数学（二）", "subjectType": "PROFESSIONAL_2", "score": 150},
        ],
    },
    {
        "jointExamGroupCode": "MANAGEMENT_2",
        "jointExamGroupName": "管理学 2",
        "examCategoryCode": "MANAGEMENT",
        "majorListText": "农林经济管理、工程管理、房地产开发与管理、工程造价、物流管理、供应链管理、健康服务与管理、旅游管理、酒店管理、旅游管理与服务教育、人力资源管理、土地资源管理、行政管理",
        "professionalSubjects": [
            {"subjectCode": "MANAGEMENT_PRINCIPLES", "subjectName": "管理学原理", "subjectType": "PROFESSIONAL_1", "score": 150},
            {"subjectCode": "ADVANCED_MATH_2", "subjectName": "高等数学（二）", "subjectType": "PROFESSIONAL_2", "score": 150},
        ],
    },
    {
        "jointExamGroupCode": "SCIENCE_ENGINEERING_1",
        "jointExamGroupName": "理工 1",
        "examCategoryCode": "SCIENCE_ENGINEERING",
        "majorListText": "化学工程与工艺、制药工程、轻化工程、环境工程、环境科学、环境生态工程、生物科学、生物技术、生态学、生物工程、石油工程技术、食品科学与工程、应用化学、生态环境工程技术",
        "professionalSubjects": [
            {"subjectCode": "CHEMICAL_PRINCIPLES", "subjectName": "化工原理", "subjectType": "PROFESSIONAL_1", "score": 150},
            {"subjectCode": "ADVANCED_MATH_1", "subjectName": "高等数学（一）", "subjectType": "PROFESSIONAL_2", "score": 150},
        ],
    },
    {
        "jointExamGroupCode": "SCIENCE_ENGINEERING_2",
        "jointExamGroupName": "理工 2",
        "examCategoryCode": "SCIENCE_ENGINEERING",
        "majorListText": "土木工程、道路桥梁与渡河工程、勘查技术与工程、采矿工程、交通工程、建筑学、智能建造工程、机械工程、机械设计制造及其自动化、机械电子工程、工业设计、车辆工程、汽车服务工程、新能源汽车工程、交通运输、机械设计制造及自动化、机械电子工程技术、汽车工程技术、新能源汽车工程技术、水利水电工程、农业水利工程、能源与动力工程、建筑环境与能源应用工程、材料成型及控制工程、金属材料工程、材料化学、服装设计与工程、服装工程技术、钢铁智能冶金技术",
        "professionalSubjects": [
            {"subjectCode": "ENGINEERING_MECHANICS", "subjectName": "工程力学", "subjectType": "PROFESSIONAL_1", "score": 150},
            {"subjectCode": "ADVANCED_MATH_1", "subjectName": "高等数学（一）", "subjectType": "PROFESSIONAL_2", "score": 150},
        ],
    },
    {
        "jointExamGroupCode": "SCIENCE_ENGINEERING_3",
        "jointExamGroupName": "理工 3",
        "examCategoryCode": "SCIENCE_ENGINEERING",
        "majorListText": "人工智能、计算机科学与技术、软件工程、网络工程、物联网工程、智能科学与技术、数据科学与大数据技术、虚拟现实技术、区块链工程、信息管理与信息系统、大数据管理与应用、网络工程技术",
        "professionalSubjects": [
            {"subjectCode": "INFO_TECH_INTRO", "subjectName": "信息技术概论", "subjectType": "PROFESSIONAL_1", "score": 150},
            {"subjectCode": "ADVANCED_MATH_1", "subjectName": "高等数学（一）", "subjectType": "PROFESSIONAL_2", "score": 150},
        ],
    },
    {
        "jointExamGroupCode": "SCIENCE_ENGINEERING_4",
        "jointExamGroupName": "理工 4",
        "examCategoryCode": "SCIENCE_ENGINEERING",
        "majorListText": "电气工程及其自动化、电子信息工程、通信工程、自动化、轨道交通信号与控制、建筑电气与智能化、电气工程及自动化、自动化技术与应用、人文地理与城乡规划",
        "professionalSubjects": [
            {"subjectCode": "INFO_TECH_INTRO", "subjectName": "信息技术概论", "subjectType": "PROFESSIONAL_1", "score": 150},
            {"subjectCode": "ADVANCED_MATH_1", "subjectName": "高等数学（一）", "subjectType": "PROFESSIONAL_2", "score": 150},
        ],
    },
    {
        "jointExamGroupCode": "SCIENCE_ENGINEERING_5",
        "jointExamGroupName": "理工 5",
        "examCategoryCode": "SCIENCE_ENGINEERING",
        "majorListText": "地理科学、数学与应用数学",
        "professionalSubjects": [
            {"subjectCode": "ADVANCED_MATH_1", "subjectName": "高等数学（一）", "subjectType": "PROFESSIONAL_1", "score": 150},
            {"subjectCode": "EDUCATIONAL_PSYCHOLOGY", "subjectName": "教育心理学", "subjectType": "PROFESSIONAL_2", "score": 150},
        ],
    },
    {
        "jointExamGroupCode": "AGRICULTURE_1",
        "jointExamGroupName": "农学 1",
        "examCategoryCode": "AGRICULTURE",
        "majorListText": "动物科学、动物医学",
        "professionalSubjects": [
            {"subjectCode": "ANIMAL_BIOCHEMISTRY", "subjectName": "动物生物化学", "subjectType": "PROFESSIONAL_1", "score": 150},
            {"subjectCode": "ADVANCED_MATH_2", "subjectName": "高等数学（二）", "subjectType": "PROFESSIONAL_2", "score": 150},
        ],
    },
    {
        "jointExamGroupCode": "AGRICULTURE_3",
        "jointExamGroupName": "农学 3",
        "examCategoryCode": "AGRICULTURE",
        "majorListText": "植物保护",
        "professionalSubjects": [
            {"subjectCode": "BOTANY", "subjectName": "植物学", "subjectType": "PROFESSIONAL_1", "score": 150},
            {"subjectCode": "ADVANCED_MATH_2", "subjectName": "高等数学（二）", "subjectType": "PROFESSIONAL_2", "score": 150},
        ],
    },
    {
        "jointExamGroupCode": "AGRICULTURE_4",
        "jointExamGroupName": "农学 4",
        "examCategoryCode": "AGRICULTURE",
        "majorListText": "风景园林、园林",
        "professionalSubjects": [
            {"subjectCode": "LANDSCAPE_FLORICULTURE", "subjectName": "园林花卉学", "subjectType": "PROFESSIONAL_1", "score": 150},
            {"subjectCode": "ADVANCED_MATH_2", "subjectName": "高等数学（二）", "subjectType": "PROFESSIONAL_2", "score": 150},
        ],
    },
    {
        "jointExamGroupCode": "EDUCATION_1",
        "jointExamGroupName": "教育学 1",
        "examCategoryCode": "EDUCATION",
        "majorListText": "体育教育",
        "professionalSubjects": [
            {"subjectCode": "EDUCATIONAL_PSYCHOLOGY", "subjectName": "教育心理学", "subjectType": "PROFESSIONAL_1", "score": 150},
            {"subjectCode": "SPORTS_COMPREHENSIVE", "subjectName": "体育专业综合", "subjectType": "PROFESSIONAL_2", "score": 150},
        ],
    },
    {
        "jointExamGroupCode": "EDUCATION_2",
        "jointExamGroupName": "教育学 2",
        "examCategoryCode": "EDUCATION",
        "majorListText": "社会体育指导与管理、休闲体育、冰雪运动、运动康复",
        "professionalSubjects": [
            {"subjectCode": "ANATOMY_PHYSIOLOGY", "subjectName": "解剖生理学", "subjectType": "PROFESSIONAL_1", "score": 150},
            {"subjectCode": "SPORTS_COMPREHENSIVE", "subjectName": "体育专业综合", "subjectType": "PROFESSIONAL_2", "score": 150},
        ],
    },
    {
        "jointExamGroupCode": "EDUCATION_3",
        "jointExamGroupName": "教育学 3",
        "examCategoryCode": "EDUCATION",
        "majorListText": "小学教育、学前教育、应用心理学",
        "professionalSubjects": [
            {"subjectCode": "EDUCATIONAL_PSYCHOLOGY", "subjectName": "教育心理学", "subjectType": "PROFESSIONAL_1", "score": 150},
            {"subjectCode": "ARTS_HISTORY_FOUNDATION", "subjectName": "文史基础", "subjectType": "PROFESSIONAL_2", "score": 150},
        ],
    },
    {
        "jointExamGroupCode": "LITERATURE_1",
        "jointExamGroupName": "文学 1",
        "examCategoryCode": "LITERATURE",
        "majorListText": "阿拉伯语",
        "professionalSubjects": [
            {"subjectCode": "FOREIGN_LANGUAGE_COMPREHENSIVE", "subjectName": "外语专业综合", "subjectType": "PROFESSIONAL_1", "score": 150},
            {"subjectCode": "ARTS_HISTORY_FOUNDATION", "subjectName": "文史基础", "subjectType": "PROFESSIONAL_2", "score": 150},
        ],
    },
    {
        "jointExamGroupCode": "LITERATURE_2",
        "jointExamGroupName": "文学 2",
        "examCategoryCode": "LITERATURE",
        "majorListText": "朝鲜语",
        "professionalSubjects": [
            {"subjectCode": "FOREIGN_LANGUAGE_COMPREHENSIVE", "subjectName": "外语专业综合", "subjectType": "PROFESSIONAL_1", "score": 150},
            {"subjectCode": "ARTS_HISTORY_FOUNDATION", "subjectName": "文史基础", "subjectType": "PROFESSIONAL_2", "score": 150},
        ],
    },
    {
        "jointExamGroupCode": "LITERATURE_3",
        "jointExamGroupName": "文学 3",
        "examCategoryCode": "LITERATURE",
        "majorListText": "德语",
        "professionalSubjects": [
            {"subjectCode": "FOREIGN_LANGUAGE_COMPREHENSIVE", "subjectName": "外语专业综合", "subjectType": "PROFESSIONAL_1", "score": 150},
            {"subjectCode": "ARTS_HISTORY_FOUNDATION", "subjectName": "文史基础", "subjectType": "PROFESSIONAL_2", "score": 150},
        ],
    },
    {
        "jointExamGroupCode": "LITERATURE_4",
        "jointExamGroupName": "文学 4",
        "examCategoryCode": "LITERATURE",
        "majorListText": "俄语",
        "professionalSubjects": [
            {"subjectCode": "FOREIGN_LANGUAGE_COMPREHENSIVE", "subjectName": "外语专业综合", "subjectType": "PROFESSIONAL_1", "score": 150},
            {"subjectCode": "ARTS_HISTORY_FOUNDATION", "subjectName": "文史基础", "subjectType": "PROFESSIONAL_2", "score": 150},
        ],
    },
    {
        "jointExamGroupCode": "LITERATURE_5",
        "jointExamGroupName": "文学 5",
        "examCategoryCode": "LITERATURE",
        "majorListText": "法语",
        "professionalSubjects": [
            {"subjectCode": "FOREIGN_LANGUAGE_COMPREHENSIVE", "subjectName": "外语专业综合", "subjectType": "PROFESSIONAL_1", "score": 150},
            {"subjectCode": "ARTS_HISTORY_FOUNDATION", "subjectName": "文史基础", "subjectType": "PROFESSIONAL_2", "score": 150},
        ],
    },
    {
        "jointExamGroupCode": "LITERATURE_6",
        "jointExamGroupName": "文学 6",
        "examCategoryCode": "LITERATURE",
        "majorListText": "英语、翻译、商务英语",
        "professionalSubjects": [
            {"subjectCode": "FOREIGN_LANGUAGE_COMPREHENSIVE", "subjectName": "外语专业综合", "subjectType": "PROFESSIONAL_1", "score": 150},
            {"subjectCode": "ARTS_HISTORY_FOUNDATION", "subjectName": "文史基础", "subjectType": "PROFESSIONAL_2", "score": 150},
        ],
    },
    {
        "jointExamGroupCode": "LITERATURE_7",
        "jointExamGroupName": "文学 7",
        "examCategoryCode": "LITERATURE",
        "majorListText": "葡萄牙语",
        "professionalSubjects": [
            {"subjectCode": "FOREIGN_LANGUAGE_COMPREHENSIVE", "subjectName": "外语专业综合", "subjectType": "PROFESSIONAL_1", "score": 150},
            {"subjectCode": "ARTS_HISTORY_FOUNDATION", "subjectName": "文史基础", "subjectType": "PROFESSIONAL_2", "score": 150},
        ],
    },
    {
        "jointExamGroupCode": "LITERATURE_8",
        "jointExamGroupName": "文学 8",
        "examCategoryCode": "LITERATURE",
        "majorListText": "日语",
        "professionalSubjects": [
            {"subjectCode": "FOREIGN_LANGUAGE_COMPREHENSIVE", "subjectName": "外语专业综合", "subjectType": "PROFESSIONAL_1", "score": 150},
            {"subjectCode": "ARTS_HISTORY_FOUNDATION", "subjectName": "文史基础", "subjectType": "PROFESSIONAL_2", "score": 150},
        ],
    },
    {
        "jointExamGroupCode": "LITERATURE_9",
        "jointExamGroupName": "文学 9",
        "examCategoryCode": "LITERATURE",
        "majorListText": "西班牙语",
        "professionalSubjects": [
            {"subjectCode": "FOREIGN_LANGUAGE_COMPREHENSIVE", "subjectName": "外语专业综合", "subjectType": "PROFESSIONAL_1", "score": 150},
            {"subjectCode": "ARTS_HISTORY_FOUNDATION", "subjectName": "文史基础", "subjectType": "PROFESSIONAL_2", "score": 150},
        ],
    },
    {
        "jointExamGroupCode": "LITERATURE_10",
        "jointExamGroupName": "文学 10",
        "examCategoryCode": "LITERATURE",
        "majorListText": "意大利语",
        "professionalSubjects": [
            {"subjectCode": "FOREIGN_LANGUAGE_COMPREHENSIVE", "subjectName": "外语专业综合", "subjectType": "PROFESSIONAL_1", "score": 150},
            {"subjectCode": "ARTS_HISTORY_FOUNDATION", "subjectName": "文史基础", "subjectType": "PROFESSIONAL_2", "score": 150},
        ],
    },
    {
        "jointExamGroupCode": "LITERATURE_11",
        "jointExamGroupName": "文学 11",
        "examCategoryCode": "LITERATURE",
        "majorListText": "新闻学、广播电视学、传播学、网络与新媒体、广告学、汉语言文学、秘书学、汉语国际教育",
        "professionalSubjects": [
            {"subjectCode": "NEW_MEDIA_INTRO", "subjectName": "新媒体概论", "subjectType": "PROFESSIONAL_1", "score": 150},
            {"subjectCode": "ARTS_HISTORY_FOUNDATION", "subjectName": "文史基础", "subjectType": "PROFESSIONAL_2", "score": 150},
        ],
    },
    {
        "jointExamGroupCode": "LAW_1",
        "jointExamGroupName": "法学 1",
        "examCategoryCode": "LAW",
        "majorListText": "法学、知识产权、国际经贸规则",
        "professionalSubjects": [
            {"subjectCode": "JURISPRUDENCE", "subjectName": "法理学", "subjectType": "PROFESSIONAL_1", "score": 150},
            {"subjectCode": "ARTS_HISTORY_FOUNDATION", "subjectName": "文史基础", "subjectType": "PROFESSIONAL_2", "score": 150},
        ],
    },
    {
        "jointExamGroupCode": "LAW_2",
        "jointExamGroupName": "法学 2",
        "examCategoryCode": "LAW",
        "majorListText": "思想政治教育",
        "professionalSubjects": [
            {"subjectCode": "JURISPRUDENCE", "subjectName": "法理学", "subjectType": "PROFESSIONAL_1", "score": 150},
            {"subjectCode": "ARTS_HISTORY_FOUNDATION", "subjectName": "文史基础", "subjectType": "PROFESSIONAL_2", "score": 150},
        ],
    },
    {
        "jointExamGroupCode": "HISTORY_1",
        "jointExamGroupName": "历史学类",
        "examCategoryCode": "HISTORY",
        "majorListText": "历史学、文物与博物馆学",
        "professionalSubjects": [
            {"subjectCode": "MODERN_CHINESE_HISTORY_OUTLINE", "subjectName": "中国近现代史纲要", "subjectType": "PROFESSIONAL_1", "score": 150},
            {"subjectCode": "ARTS_HISTORY_FOUNDATION", "subjectName": "文史基础", "subjectType": "PROFESSIONAL_2", "score": 150},
        ],
    },
    {
        "jointExamGroupCode": "MEDICINE_1",
        "jointExamGroupName": "医学 1",
        "examCategoryCode": "MEDICINE",
        "majorListText": "护理学、助产学",
        "professionalSubjects": [
            {"subjectCode": "PHYSIOLOGY", "subjectName": "生理学", "subjectType": "PROFESSIONAL_1", "score": 150},
            {"subjectCode": "HUMAN_ANATOMY", "subjectName": "人体解剖学", "subjectType": "PROFESSIONAL_2", "score": 150},
        ],
    },
    {
        "jointExamGroupCode": "MEDICINE_2",
        "jointExamGroupName": "医学 2",
        "examCategoryCode": "MEDICINE",
        "majorListText": "医学检验技术、医学影像技术、口腔医学技术",
        "professionalSubjects": [
            {"subjectCode": "PHYSIOLOGY", "subjectName": "生理学", "subjectType": "PROFESSIONAL_1", "score": 150},
            {"subjectCode": "HUMAN_ANATOMY", "subjectName": "人体解剖学", "subjectType": "PROFESSIONAL_2", "score": 150},
        ],
    },
    {
        "jointExamGroupCode": "MEDICINE_3",
        "jointExamGroupName": "医学 3",
        "examCategoryCode": "MEDICINE",
        "majorListText": "临床医学",
        "professionalSubjects": [
            {"subjectCode": "PHYSIOLOGY", "subjectName": "生理学", "subjectType": "PROFESSIONAL_1", "score": 150},
            {"subjectCode": "HUMAN_ANATOMY", "subjectName": "人体解剖学", "subjectType": "PROFESSIONAL_2", "score": 150},
        ],
    },
    {
        "jointExamGroupCode": "MEDICINE_4",
        "jointExamGroupName": "医学 4",
        "examCategoryCode": "MEDICINE",
        "majorListText": "中药学、药学",
        "professionalSubjects": [
            {"subjectCode": "PHYSIOLOGY", "subjectName": "生理学", "subjectType": "PROFESSIONAL_1", "score": 150},
            {"subjectCode": "HUMAN_ANATOMY", "subjectName": "人体解剖学", "subjectType": "PROFESSIONAL_2", "score": 150},
        ],
    },
    {
        "jointExamGroupCode": "MEDICINE_5",
        "jointExamGroupName": "医学 5",
        "examCategoryCode": "MEDICINE",
        "majorListText": "中医学、康复治疗学、针灸推拿学",
        "professionalSubjects": [
            {"subjectCode": "PHYSIOLOGY", "subjectName": "生理学", "subjectType": "PROFESSIONAL_1", "score": 150},
            {"subjectCode": "HUMAN_ANATOMY", "subjectName": "人体解剖学", "subjectType": "PROFESSIONAL_2", "score": 150},
        ],
    },
    {
        "jointExamGroupCode": "ART_1",
        "jointExamGroupName": "艺术 1",
        "examCategoryCode": "ART",
        "majorListText": "艺术教育（美术）、戏剧影视美术设计、美术学、绘画、产品设计、服装与服饰设计、数字媒体艺术、雕塑、动画、文物保护与修复、环境设计、公共艺术、艺术设计学、视觉传达设计、艺术与科技、影视摄影与制作、摄影",
        "professionalSubjects": [
            {"subjectCode": "FINE_ARTS_COMPREHENSIVE", "subjectName": "美术专业综合", "subjectType": "PROFESSIONAL_1", "score": 150},
            {"subjectCode": "ART_INTRODUCTION", "subjectName": "艺术概论", "subjectType": "PROFESSIONAL_2", "score": 150},
        ],
    },
    {
        "jointExamGroupCode": "ART_2",
        "jointExamGroupName": "艺术 2",
        "examCategoryCode": "ART",
        "majorListText": "书法学",
        "professionalSubjects": [
            {"subjectCode": "CALLIGRAPHY_COMPREHENSIVE", "subjectName": "书法专业综合", "subjectType": "PROFESSIONAL_1", "score": 150},
            {"subjectCode": "ART_INTRODUCTION", "subjectName": "艺术概论", "subjectType": "PROFESSIONAL_2", "score": 150},
        ],
    },
    {
        "jointExamGroupCode": "ART_3",
        "jointExamGroupName": "艺术 3",
        "examCategoryCode": "ART",
        "majorListText": "表演",
        "professionalSubjects": [
            {"subjectCode": "PERFORMANCE_COMPREHENSIVE", "subjectName": "表演专业综合", "subjectType": "PROFESSIONAL_1", "score": 150},
            {"subjectCode": "ART_INTRODUCTION", "subjectName": "艺术概论", "subjectType": "PROFESSIONAL_2", "score": 150},
        ],
    },
    {
        "jointExamGroupCode": "ART_4",
        "jointExamGroupName": "艺术 4",
        "examCategoryCode": "ART",
        "majorListText": "播音与主持艺术、广播电视编导",
        "professionalSubjects": [
            {"subjectCode": "NEW_MEDIA_INTRO", "subjectName": "新媒体概论", "subjectType": "PROFESSIONAL_1", "score": 150},
            {"subjectCode": "ART_INTRODUCTION", "subjectName": "艺术概论", "subjectType": "PROFESSIONAL_2", "score": 150},
        ],
    },
    {
        "jointExamGroupCode": "ART_5",
        "jointExamGroupName": "艺术 5",
        "examCategoryCode": "ART",
        "majorListText": "艺术教育（舞蹈）、舞蹈表演、舞蹈学、舞蹈编导",
        "professionalSubjects": [
            {"subjectCode": "DANCE_COMPREHENSIVE", "subjectName": "舞蹈专业综合", "subjectType": "PROFESSIONAL_1", "score": 150},
            {"subjectCode": "ART_INTRODUCTION", "subjectName": "艺术概论", "subjectType": "PROFESSIONAL_2", "score": 150},
        ],
    },
    {
        "jointExamGroupCode": "ART_6",
        "jointExamGroupName": "艺术 6",
        "examCategoryCode": "ART",
        "majorListText": "艺术教育（声乐）、音乐表演（声乐）、音乐学（声乐）",
        "professionalSubjects": [
            {"subjectCode": "VOCAL_MUSIC_COMPREHENSIVE", "subjectName": "声乐专业综合", "subjectType": "PROFESSIONAL_1", "score": 150},
            {"subjectCode": "ART_INTRODUCTION", "subjectName": "艺术概论", "subjectType": "PROFESSIONAL_2", "score": 150},
        ],
    },
    {
        "jointExamGroupCode": "ART_7",
        "jointExamGroupName": "艺术 7",
        "examCategoryCode": "ART",
        "majorListText": "音乐表演（器乐）、音乐学（器乐）",
        "professionalSubjects": [
            {"subjectCode": "INSTRUMENTAL_MUSIC_COMPREHENSIVE", "subjectName": "器乐专业综合", "subjectType": "PROFESSIONAL_1", "score": 150},
            {"subjectCode": "ART_INTRODUCTION", "subjectName": "艺术概论", "subjectType": "PROFESSIONAL_2", "score": 150},
        ],
    },
]

EXAM_CATEGORY_MAP: Dict[str, Dict[str, object]] = {
    str(item.get("examCategoryCode", "")).strip(): dict(item)
    for item in EXAM_CATEGORIES
    if isinstance(item, dict) and str(item.get("examCategoryCode", "")).strip()
}

JOINT_GROUP_MAP: Dict[str, Dict[str, object]] = {
    str(item.get("jointExamGroupCode", "")).strip(): dict(item)
    for item in JOINT_EXAM_GROUPS
    if isinstance(item, dict) and str(item.get("jointExamGroupCode", "")).strip()
}

SUBJECT_ID_OVERRIDES: Dict[str, str] = {
    "POLITICS": "subject-politics",
    "ENGLISH": "subject-english",
    "ADVANCED_MATH_1": "subject-advanced-math-1",
    "ADVANCED_MATH_2": "subject-advanced-math-2",
    "INFO_TECH_INTRO": "subject-computer",
}


def all_joint_exam_group_codes() -> List[str]:
    return [item["jointExamGroupCode"] for item in JOINT_EXAM_GROUPS]


def subject_id_from_subject_code(subject_code: str) -> str:
    normalized_subject_code = str(subject_code or "").strip().upper()
    if not normalized_subject_code:
        return ""
    override = SUBJECT_ID_OVERRIDES.get(normalized_subject_code)
    if override:
        return override
    component = normalized_subject_code.lower().replace("_", "-")
    return f"subject-{component}"


def subject_code_from_subject_id(subject_id: str) -> str:
    normalized_subject_id = str(subject_id or "").strip().lower()
    if not normalized_subject_id:
        return ""
    for subject_code, resolved_subject_id in (
        (str(item.get("subjectCode", "")).strip(), subject_id_from_subject_code(str(item.get("subjectCode", "")).strip()))
        for item in PUBLIC_SUBJECTS
        if isinstance(item, dict)
    ):
        if resolved_subject_id.lower() == normalized_subject_id:
            return subject_code
    for group in JOINT_EXAM_GROUPS:
        professional_subjects = group.get("professionalSubjects", [])
        if not isinstance(professional_subjects, list):
            continue
        for subject in professional_subjects:
            if not isinstance(subject, dict):
                continue
            subject_code = str(subject.get("subjectCode", "")).strip()
            if subject_id_from_subject_code(subject_code).lower() == normalized_subject_id:
                return subject_code
    if normalized_subject_id.startswith("subject-"):
        return normalized_subject_id.removeprefix("subject-").replace("-", "_").upper()
    return ""


def subject_applicable_group_codes(subject_code: str) -> List[str]:
    normalized_subject_code = str(subject_code or "").strip()
    if not normalized_subject_code:
        return []
    public_subject_codes = {
        str(item.get("subjectCode", "")).strip()
        for item in PUBLIC_SUBJECTS
        if isinstance(item, dict) and str(item.get("subjectCode", "")).strip()
    }
    if normalized_subject_code in public_subject_codes:
        return all_joint_exam_group_codes()
    matched_group_codes: List[str] = []
    for group in JOINT_EXAM_GROUPS:
        professional_subjects = group.get("professionalSubjects", [])
        if not isinstance(professional_subjects, list):
            continue
        for subject in professional_subjects:
            if not isinstance(subject, dict):
                continue
            if str(subject.get("subjectCode", "")).strip() == normalized_subject_code:
                group_code = str(group.get("jointExamGroupCode", "")).strip()
                if group_code:
                    matched_group_codes.append(group_code)
                break
    return sorted(set(matched_group_codes))


def level_code_from_level(level: int) -> str:
    normalized_level = max(1, int(level or 1))
    return f"L{normalized_level}"


def level_path_from_level(level: int) -> List[str]:
    normalized_level = max(1, int(level or 1))
    return [f"L{current_level}" for current_level in range(1, normalized_level + 1)]


def get_exam_category(exam_category_code: str) -> Optional[Dict[str, object]]:
    for item in EXAM_CATEGORIES:
        if item["examCategoryCode"] == exam_category_code:
            return item
    return None


def get_joint_exam_group(joint_exam_group_code: str) -> Optional[Dict[str, object]]:
    for item in JOINT_EXAM_GROUPS:
        if item["jointExamGroupCode"] == joint_exam_group_code:
            return item
    return None


def list_joint_exam_groups(exam_category_code: str = "") -> List[Dict[str, object]]:
    if not exam_category_code:
        return list(JOINT_EXAM_GROUPS)
    return [item for item in JOINT_EXAM_GROUPS if item["examCategoryCode"] == exam_category_code]


def build_content_baseline() -> Dict[str, object]:
    categories = []
    for category in EXAM_CATEGORIES:
        groups = []
        for group in list_joint_exam_groups(category["examCategoryCode"]):
            groups.append(
                {
                    **group,
                    "subjects": PUBLIC_SUBJECTS + group["professionalSubjects"],
                }
            )
        categories.append({**category, "jointExamGroups": groups})
    return {
        "policyVersionCode": POLICY_VERSION_CODE,
        "policyVersionTitle": POLICY_VERSION_TITLE,
        "publicSubjects": PUBLIC_SUBJECTS,
        "examCategories": categories,
    }
