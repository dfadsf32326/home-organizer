# 🏠 Home Organizer (越整理，越轻松)

这是一个基于“慢整理”理念打造的家庭物品与空间管理系统。采用 **Local-First (本地优先)** 的 JSON 数据结构，并与 **飞书多维表格 (Feishu Base)** 进行深度双向同步。

系统的核心目标不仅仅是“记录物品在哪”，而是通过数字化的手段建立并维护一套可持续的家庭收纳秩序。

---

## ✨ 核心特性 (Features)

- 🌳 **统一空间树模型 (Infinite Space Tree)**
  打破传统的“空间-容器”两级限制，采用单表自引用（Self-referencing）架构，实现从“房间 → 柜子 → 抽屉 → 收纳盒”的无限层级嵌套。
- 🔄 **高保真双向同步 (High-fidelity Sync)**
  通过深度内容指纹比对（Deep Compare），精确识别本地与云端的数据差异。在保证数据一致性的同时，严格保护飞书云端“最后更新时间”的真实性。
- 🗂️ **字段级配置解耦 (Decoupled Field Mapping)**
  飞书表的 ID 和字段映射集中管理于 `field_mapping.json`，即使飞书端发生表结构重建或字段重命名，Python 同步逻辑也无需修改任何代码。
- 📑 **智能分类映射 (Category Mapping)**
  维护严格的 MECE（相互独立，完全穷尽）分类标准，本地子分类自动关联飞书的大分类主键。

---

## 📂 项目结构 (Project Structure)

```text
home-organizer/
├── README.md                       # 简介与未来规划（本文件）
├── SKILL.md                        # 核心运行逻辑与系统架构（Agent 必读）
├── CLASSIFICATION_STANDARD.md      # 分类标准定义（MECE原则）
├── data/                           # 本地核心数据库 (Local-First)
│   ├── items.json                  # 物品清单（主数据）
│   ├── space_map.json              # 空间与容器嵌套树形数据
│   ├── category_mapping.json       # 分类名与飞书 record_id 映射
│   └── field_mapping.json          # 飞书字段 ID 配置表
└── scripts/                        # 同步引擎与脚本
    ├── sync_final.py               # 物品主数据同步
    ├── sync_category_mapping.py    # 分类表双向同步
    └── sync_space_map.py           # 空间结构双向同步
```

---

## 🚀 未来规划 (Roadmap)

为了保持当前系统架构的清晰性，当前版本聚焦于解决 **“空间与物品的拓扑归属关系”**（即收纳秩序）。后续计划以模块化扩展的方式引入以下新特性：

### 📅 1. 物品保质期管理 (Expiration Date Tracking) [Planned]

这是未来系统的重要升级方向。将管理维度从纯粹的“空间维”扩展到“时间维”。

**为什么暂不合并在当前版本做？**
当前的重心是建立稳固的物理收纳框架（空间树与分类标准）。保质期管理主要针对特定的**消耗品**（如食品、药品、护肤品），具有高频消耗、复购的动态特征。为了避免初期数据模型过于臃肿，这部分逻辑将被延后，待空间拓扑模型完全稳定后，再作为平行模块接入。

**未来功能构想：**
- **效期字段扩展**：新增 `production_date` (生产日期)、`expiration_date` (保质期至)、`shelf_life_days` (保质期天数) 等属性。
- **红绿灯状态机**：根据当前日期自动计算物品状态（安全 🟢 / 临期 🟡 / 过期 🔴）。
- **自动化预警推送**：结合 Hermes Agent 的 Cronjob 机制，每天早上自动巡检数据库，若发现即将过期的物品，主动推送到飞书/微信，提醒“优先消耗”。
- **飞书日历联动**：对于非常重要且有明确有效期的物品（如证件、重要药品），支持将到期日直接写入飞书日历日程中。

### 📸 2. 视觉辅助录入 (Vision-based Quick Entry) [Considering]
结合视觉大模型（Vision Model），未来可以通过直接拍摄抽屉或冰箱内部，由 AI 自动识别其中的物品、预估分类，并一键结构化写入 `items.json`，极大降低物品数字化的录入摩擦力。

### 📊 3. 囤货水位线管理 (Inventory Watermark) [Considering]
为高频消耗品（如纸巾、洗手液、咖啡豆）设置“最低库存警戒线”。当标记物品被消耗至低于警戒线时，自动加入“待采购清单”。