#!/usr/bin/env python3
"""
Claw Bot AI - 通知功能使用示例

这个文件展示了如何在您的项目中使用邮件、Telegram 和 WhatsApp 通知功能。
"""

import httpx
import asyncio
from datetime import datetime


# API 基础地址
API_BASE = "http://localhost:8000"


def send_telegram_alert(message: str, silent: bool = False) -> bool:
    """
    发送 Telegram 警报消息

    Args:
        message: 消息内容
        silent: 是否静默发送（不产生通知声音）

    Returns:
        是否发送成功
    """
    try:
        response = httpx.post(
            f"{API_BASE}/send-telegram",
            json={
                "text": message,
                "parse_mode": "Markdown",
                "disable_notification": silent
            },
            timeout=10.0
        )
        result = response.json()
        return result.get("success", False)
    except Exception as e:
        print(f"发送 Telegram 消息失败: {e}")
        return False


def send_email_report(to: str, subject: str, content: str, use_html: bool = False) -> bool:
    """
    发送邮件报告

    Args:
        to: 收件人邮箱
        subject: 邮件主题
        content: 邮件内容
        use_html: 是否使用 HTML 格式

    Returns:
        是否发送成功
    """
    try:
        response = httpx.post(
            f"{API_BASE}/send-email",
            json={
                "to": to,
                "subject": subject,
                "body": content,
                "html": use_html
            },
            timeout=10.0
        )
        result = response.json()
        return result.get("success", False)
    except Exception as e:
        print(f"发送邮件失败: {e}")
        return False


def send_whatsapp_message(phone: str, message: str) -> bool:
    """
    发送 WhatsApp 消息

    Args:
        phone: 手机号（格式: +1234567890）
        message: 消息内容

    Returns:
        是否发送成功
    """
    try:
        response = httpx.post(
            f"{API_BASE}/send-whatsapp",
            json={
                "to": phone,
                "message": message
            },
            timeout=10.0
        )
        result = response.json()
        return result.get("success", False)
    except Exception as e:
        print(f"发送 WhatsApp 消息失败: {e}")
        return False


def notify_all_channels(message: str):
    """
    向所有可用渠道发送通知

    Args:
        message: 消息内容
    """
    print(f"\n📢 向所有渠道发送通知: {message[:50]}...")

    # Telegram
    if send_telegram_alert(f"🔔 *通知*\n\n{message}"):
        print("  ✅ Telegram 发送成功")
    else:
        print("  ❌ Telegram 发送失败")

    # Email (需要配置)
    # if send_email_report("admin@example.com", "系统通知", message):
    #     print("  ✅ 邮件发送成功")

    # WhatsApp (需要配置)
    # if send_whatsapp_message("+1234567890", message):
    #     print("  ✅ WhatsApp 发送成功")


# ============= 实用场景示例 =============

def example_trading_alert():
    """场景 1: 交易提醒"""
    symbol = "BTC/USDT"
    price = 42150.50
    profit = 150.25

    message = f"""
🎯 *交易完成*

币种: `{symbol}`
价格: ${price:,.2f}
利润: ${profit:,.2f}
时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

✅ 交易已成功执行！
"""

    send_telegram_alert(message)


def example_error_alert():
    """场景 2: 错误警报"""
    error_msg = "数据库连接失败"

    message = f"""
🚨 *系统错误警报*

错误: {error_msg}
时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
服务器: Production Server

⚠️ 请立即检查！
"""

    # 紧急消息不静默
    send_telegram_alert(message, silent=False)


def example_daily_report():
    """场景 3: 每日报告"""
    total_trades = 15
    profit = 325.50
    success_rate = 80

    message = f"""
📊 *每日交易报告*

日期: {datetime.now().strftime('%Y-%m-%d')}

总交易次数: {total_trades}
总利润: ${profit:,.2f}
成功率: {success_rate}%

{'🎉 表现优秀！' if success_rate >= 80 else '💪 继续努力！'}
"""

    # 每日报告可以静默发送
    send_telegram_alert(message, silent=True)


def example_system_status():
    """场景 4: 系统状态更新"""
    message = f"""
💻 *系统状态*

🟢 AI 服务: 正常
🟢 数据库: 正常
🟢 API: 正常
🟢 通知系统: 正常

最后检查: {datetime.now().strftime('%H:%M:%S')}
"""

    send_telegram_alert(message, silent=True)


def example_with_ai_chat():
    """场景 5: 结合 AI 生成消息内容"""
    # 先让 AI 生成消息
    response = httpx.post(
        f"{API_BASE}/chat",
        json={"message": "用一句话激励我今天的交易"},
        timeout=30.0
    )

    if response.status_code == 200:
        ai_message = response.json()["message"]

        message = f"""
🤖 *AI 每日激励*

{ai_message}

祝您今天交易顺利！ 💪
"""

        send_telegram_alert(message)


async def example_batch_notifications():
    """场景 6: 批量异步发送通知"""
    users = [
        {"phone": "+1234567890", "name": "用户A"},
        {"phone": "+0987654321", "name": "用户B"},
        {"phone": "+1111111111", "name": "用户C"},
    ]

    message = "🎉 系统维护已完成，所有服务已恢复正常！"

    async with httpx.AsyncClient() as client:
        tasks = []
        for user in users:
            task = client.post(
                f"{API_BASE}/send-whatsapp",
                json={"to": user["phone"], "message": message},
                timeout=10.0
            )
            tasks.append(task)

        results = await asyncio.gather(*tasks, return_exceptions=True)

        success_count = sum(1 for r in results if not isinstance(r, Exception) and r.json().get("success"))
        print(f"批量发送完成: {success_count}/{len(users)} 成功")


# ============= 主函数 =============

def main():
    """运行示例"""
    print("🚀 Claw Bot AI - 通知功能示例\n")
    print("=" * 50)

    # 示例 1: 交易提醒
    print("\n📌 示例 1: 交易提醒")
    example_trading_alert()

    # 示例 2: 错误警报
    print("\n📌 示例 2: 错误警报")
    example_error_alert()

    # 示例 3: 每日报告
    print("\n📌 示例 3: 每日报告")
    example_daily_report()

    # 示例 4: 系统状态
    print("\n📌 示例 4: 系统状态")
    example_system_status()

    # 示例 5: AI 生成内容
    print("\n📌 示例 5: 结合 AI 生成消息")
    example_with_ai_chat()

    # 示例 6: 批量发送（需要配置 WhatsApp）
    # print("\n📌 示例 6: 批量异步发送")
    # asyncio.run(example_batch_notifications())

    print("\n" + "=" * 50)
    print("✅ 所有示例执行完毕！")
    print("\n💡 提示: 查看您的 Telegram 接收通知")


if __name__ == "__main__":
    main()
