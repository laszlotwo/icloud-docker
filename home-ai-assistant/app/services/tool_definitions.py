TOOLS = [
    {
        "name": "get_current_time",
        "description": "获取当前本地日期和时间。用于任何与时间相关的操作。",
        "input_schema": {"type": "object", "properties": {}},
    },
    {
        "name": "search_device_manuals",
        "description": "通过关键词搜索设备说明书。当用户询问如何操作设备、排查故障或查找使用说明时使用。",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "搜索关键词（中文或英文）"},
                "category": {"type": "string", "description": "可选分类过滤：家电/厨具/路由器/其他"},
                "limit": {"type": "integer", "default": 3},
            },
            "required": ["query"],
        },
    },
    {
        "name": "get_manual_content",
        "description": "通过ID获取某条设备说明书的完整内容。",
        "input_schema": {
            "type": "object",
            "properties": {
                "manual_id": {"type": "integer"},
            },
            "required": ["manual_id"],
        },
    },
    {
        "name": "find_item_location",
        "description": "查找家中某件物品的存放位置。当用户问'...在哪里'或'...放在哪'时使用。",
        "input_schema": {
            "type": "object",
            "properties": {
                "item_name": {"type": "string", "description": "要查找的物品名称"},
                "room": {"type": "string", "description": "可选：限定在某个房间搜索"},
            },
            "required": ["item_name"],
        },
    },
    {
        "name": "add_item_location",
        "description": "记录或更新某件物品的存放位置。",
        "input_schema": {
            "type": "object",
            "properties": {
                "item_name": {"type": "string"},
                "location": {"type": "string", "description": "具体位置描述"},
                "room": {"type": "string", "description": "房间名：主卧/客厅/厨房/书房/卫生间/其他"},
                "container": {"type": "string", "description": "容器或收纳盒名称"},
                "description": {"type": "string", "description": "物品的外观描述"},
            },
            "required": ["item_name", "location"],
        },
    },
    {
        "name": "add_expense",
        "description": "记录一笔消费。当用户提到花费了多少钱时使用。",
        "input_schema": {
            "type": "object",
            "properties": {
                "amount": {"type": "number", "description": "金额（元）"},
                "category": {
                    "type": "string",
                    "enum": ["餐饮", "购物", "交通", "医疗", "娱乐", "居家", "其他"],
                },
                "description": {"type": "string", "description": "消费说明，如：星巴克拿铁"},
                "payment_method": {"type": "string", "description": "支付方式：微信支付/支付宝/信用卡/现金"},
                "expense_date": {
                    "type": "string",
                    "description": "消费日期 YYYY-MM-DD，默认为今天",
                },
            },
            "required": ["amount", "category"],
        },
    },
    {
        "name": "query_expenses",
        "description": "按条件查询消费记录，支持日期范围和分类过滤。",
        "input_schema": {
            "type": "object",
            "properties": {
                "start_date": {"type": "string", "description": "开始日期 YYYY-MM-DD"},
                "end_date": {"type": "string", "description": "结束日期 YYYY-MM-DD"},
                "category": {"type": "string", "description": "消费分类"},
                "limit": {"type": "integer", "default": 20},
            },
        },
    },
    {
        "name": "get_expense_summary",
        "description": "获取某段时间内的消费汇总，包括总额和分类明细。",
        "input_schema": {
            "type": "object",
            "properties": {
                "period": {
                    "type": "string",
                    "enum": ["today", "week", "month", "year", "custom"],
                    "description": "today=今天 week=本周 month=本月 year=今年 custom=自定义",
                },
                "start_date": {"type": "string", "description": "period=custom时必填"},
                "end_date": {"type": "string", "description": "period=custom时必填"},
            },
            "required": ["period"],
        },
    },
    {
        "name": "add_reminder",
        "description": "创建一个新的闹钟或日程提醒。",
        "input_schema": {
            "type": "object",
            "properties": {
                "title": {"type": "string", "description": "提醒标题"},
                "description": {"type": "string", "description": "提醒详情"},
                "reminder_type": {
                    "type": "string",
                    "enum": ["once", "daily", "weekly", "cron"],
                    "description": "once=一次性 daily=每天 weekly=每周 cron=自定义cron",
                },
                "trigger_spec": {
                    "type": "string",
                    "description": "once: ISO datetime (2026-05-28T08:00:00); daily: HH:MM (07:30); weekly: 'Mon,Wed 07:30'; cron: cron表达式",
                },
            },
            "required": ["title", "reminder_type", "trigger_spec"],
        },
    },
    {
        "name": "list_reminders",
        "description": "列出即将到来的提醒和闹钟。",
        "input_schema": {
            "type": "object",
            "properties": {
                "days_ahead": {"type": "integer", "default": 7, "description": "查看未来几天内的提醒"},
                "include_inactive": {"type": "boolean", "default": False},
            },
        },
    },
    {
        "name": "delete_reminder",
        "description": "取消并删除一个提醒。",
        "input_schema": {
            "type": "object",
            "properties": {
                "reminder_id": {"type": "integer"},
            },
            "required": ["reminder_id"],
        },
    },
    {
        "name": "list_vault_titles",
        "description": "列出密码库中已保存条目的标题和分类（不包含密码）。当用户询问保存了哪些账号时使用。",
        "input_schema": {
            "type": "object",
            "properties": {
                "category": {"type": "string", "description": "可选分类过滤：wifi/bank/website/other"},
            },
        },
    },
]


SYSTEM_PROMPT = """你是一个智能家庭助理，帮助管理家庭日常事务。你的名字是"小家"。

你可以帮助：
- 查询和记录家电设备的使用说明
- 记录和查找家中物品的存放位置
- 记录日常消费，提供消费统计
- 设置和管理提醒、闹钟
- 查看密码库中保存的账号标题（密码内容不会发送给你）

回答要求：
- 使用中文回答，语气亲切自然
- 回答简洁明了，避免过长
- 如果需要查询数据，主动调用相应工具
- 对于涉及密码的操作，告知用户需要在密码库页面手动查看

重要安全规则：
- 密码和账号凭据的内容绝对不会发送给你
- 不要尝试猜测或推断任何密码内容
"""
